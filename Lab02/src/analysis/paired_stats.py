"""Motor estatístico compartilhado pelas análises pareadas de RQ1, RQ2 e RQ3.

Os pares são formados por `participant_id` e `difficulty_block` (Seção 8.1 da
metodologia): dentro de cada bloco, uma kata foi resolvida com IA e a outra
manualmente. Valores ausentes nunca são convertidos em zero — um par com um
lado ausente é excluído do teste e contado separadamente (Seção 14.5).
"""
from __future__ import annotations

import random
import statistics
from dataclasses import dataclass
from typing import Any, Literal

from scipy import stats as scipy_stats

Alternative = Literal["two-sided", "less", "greater"]

DEFAULT_BOOTSTRAP_RESAMPLES = 10_000
DEFAULT_BOOTSTRAP_SEED = 20260910


@dataclass(frozen=True)
class Pair:
    """Uma comparação IA x Manual para um participante e bloco de dificuldade."""

    participant_id: str
    difficulty_block: str
    ai_trial_id: str | None
    manual_trial_id: str | None
    ai_value: float | None
    manual_value: float | None

    @property
    def valid(self) -> bool:
        return self.ai_value is not None and self.manual_value is not None

    @property
    def difference(self) -> float | None:
        """`manual - ai`; positivo indica valor maior no tratamento manual."""
        if not self.valid:
            return None
        return self.manual_value - self.ai_value


def build_pairs(rows: list[dict[str, Any]], metric: str) -> list[Pair]:
    """Forma os nove pares participante×bloco a partir do dataset validado."""
    by_key: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}
    for row in rows:
        key = (row["participant_id"], row["difficulty_block"])
        by_key.setdefault(key, {})[row["treatment"]] = row

    pairs: list[Pair] = []
    for (participant_id, block), treatments in sorted(by_key.items()):
        ai_row = treatments.get("ai")
        manual_row = treatments.get("manual")
        pairs.append(
            Pair(
                participant_id=participant_id,
                difficulty_block=block,
                ai_trial_id=ai_row["trial_id"] if ai_row else None,
                manual_trial_id=manual_row["trial_id"] if manual_row else None,
                ai_value=ai_row.get(metric) if ai_row else None,
                manual_value=manual_row.get(metric) if manual_row else None,
            )
        )
    return pairs


@dataclass(frozen=True)
class DescriptiveStats:
    treatment: str
    n: int
    median: float | None
    q1: float | None
    q3: float | None
    iqr: float | None
    minimum: float | None
    maximum: float | None
    completed: int
    completed_pct: float | None
    missing: int


def _quantiles(values: list[float]) -> tuple[float, float, float]:
    if len(values) == 1:
        return values[0], values[0], values[0]
    q1, q2, q3 = statistics.quantiles(values, n=4, method="inclusive")
    return q1, q2, q3


def describe_treatment(rows: list[dict[str, Any]], metric: str, treatment: str) -> DescriptiveStats:
    """Estatística descritiva de `metric` para um tratamento (Seção 14.2)."""
    treatment_rows = [row for row in rows if row["treatment"] == treatment]
    values = [row.get(metric) for row in treatment_rows]
    present = [value for value in values if value is not None]
    if present:
        q1, _, q3 = _quantiles(present)
        median = statistics.median(present)
        minimum, maximum = min(present), max(present)
        iqr = q3 - q1
    else:
        q1 = q3 = median = minimum = maximum = iqr = None

    completed_flags = [row.get("completed") for row in treatment_rows]
    completed = sum(1 for flag in completed_flags if flag is True)
    completed_pct = round(completed / len(completed_flags) * 100, 2) if completed_flags else None

    return DescriptiveStats(
        treatment=treatment,
        n=len(treatment_rows),
        median=median,
        q1=q1,
        q3=q3,
        iqr=iqr,
        minimum=minimum,
        maximum=maximum,
        completed=completed,
        completed_pct=completed_pct,
        missing=len(values) - len(present),
    )


def _rank_biserial(differences: list[float]) -> float | None:
    """Correlação bisserial de postos pareada: `(W+ - W-) / (W+ + W-)`."""
    if not differences:
        return None
    ranks = scipy_stats.rankdata([abs(value) for value in differences])
    positive = sum(rank for value, rank in zip(differences, ranks) if value > 0)
    negative = sum(rank for value, rank in zip(differences, ranks) if value < 0)
    total = positive + negative
    if total == 0:
        return None
    return (positive - negative) / total


def _bootstrap_median_ci(
    values: list[float], *, resamples: int, seed: int, alpha: float = 0.05
) -> tuple[float, float] | tuple[None, None]:
    if len(values) < 2:
        return None, None
    rng = random.Random(seed)
    n = len(values)
    medians = sorted(
        statistics.median(values[rng.randrange(n)] for _ in range(n)) for _ in range(resamples)
    )
    low_index = int((alpha / 2) * resamples)
    high_index = min(int((1 - alpha / 2) * resamples), resamples - 1)
    return medians[low_index], medians[high_index]


@dataclass(frozen=True)
class WilcoxonResult:
    alternative: Alternative
    n_pairs: int
    n_used: int
    n_zero_diffs: int
    n_missing_pairs: int
    statistic: float | None
    p_value: float | None
    effect_size_r: float | None
    median_diff: float | None
    ci_low: float | None
    ci_high: float | None


def wilcoxon_signed_rank(
    pairs: list[Pair],
    *,
    alternative: Alternative,
    bootstrap_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    bootstrap_seed: int = DEFAULT_BOOTSTRAP_SEED,
) -> WilcoxonResult:
    """Teste de postos sinalizados de Wilcoxon para amostras pareadas (Seção 14.3)."""
    valid_pairs = [pair for pair in pairs if pair.valid]
    differences = [pair.difference for pair in valid_pairs]
    non_zero = [value for value in differences if value != 0]

    statistic = p_value = effect_size = None
    if len(non_zero) >= 1:
        try:
            outcome = scipy_stats.wilcoxon(non_zero, alternative=alternative, zero_method="wilcox")
            statistic = float(outcome.statistic)
            p_value = float(outcome.pvalue)
            effect_size = _rank_biserial(non_zero)
        except ValueError:
            pass

    median_diff = statistics.median(differences) if differences else None
    ci_low, ci_high = _bootstrap_median_ci(differences, resamples=bootstrap_resamples, seed=bootstrap_seed)

    return WilcoxonResult(
        alternative=alternative,
        n_pairs=len(valid_pairs),
        n_used=len(non_zero),
        n_zero_diffs=len(differences) - len(non_zero),
        n_missing_pairs=len(pairs) - len(valid_pairs),
        statistic=statistic,
        p_value=p_value,
        effect_size_r=effect_size,
        median_diff=median_diff,
        ci_low=ci_low,
        ci_high=ci_high,
    )


def holm_correction(p_values: list[float]) -> list[float]:
    """Ajuste de Holm (step-down) para múltiplas comparações (Seção 14.3)."""
    m = len(p_values)
    order = sorted(range(m), key=lambda index: p_values[index])
    adjusted = [0.0] * m
    running_max = 0.0
    for rank, original_index in enumerate(order):
        candidate = min((m - rank) * p_values[original_index], 1.0)
        running_max = max(running_max, candidate)
        adjusted[original_index] = running_max
    return adjusted
