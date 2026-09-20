"""RQ1 — tempo de resolução: IA reduz o tempo em relação ao manual?

Compara `duration_seconds` entre tratamentos, mantendo os trials censurados
com 2.100 segundos (Seção 14.4). Além da análise principal, executa uma
análise de sensibilidade apenas com trials concluídos, explicitamente
identificada como condicionada ao sucesso e sujeita a viés de seleção.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .paired_stats import (
    DescriptiveStats,
    Pair,
    WilcoxonResult,
    build_pairs,
    describe_treatment,
    wilcoxon_signed_rank,
)

METRIC = "duration_seconds"
ALTERNATIVE = "greater"  # H1: duration(manual) > duration(ai) -> IA mais rápida


@dataclass(frozen=True)
class CensoringSummary:
    treatment: str
    n: int
    censored: int
    censored_pct: float | None


@dataclass(frozen=True)
class RQ1Result:
    descriptive: dict[str, DescriptiveStats]
    censoring: dict[str, CensoringSummary]
    pairs: list[Pair]
    wilcoxon: WilcoxonResult
    completed_only_pairs: list[Pair]
    wilcoxon_completed_only: WilcoxonResult


def _censoring_summary(rows: list[dict[str, Any]], treatment: str) -> CensoringSummary:
    treatment_rows = [row for row in rows if row["treatment"] == treatment]
    censored = sum(1 for row in treatment_rows if row.get("censored") is True)
    pct = round(censored / len(treatment_rows) * 100, 2) if treatment_rows else None
    return CensoringSummary(treatment=treatment, n=len(treatment_rows), censored=censored, censored_pct=pct)


def analyze(rows: list[dict[str, Any]]) -> RQ1Result:
    descriptive = {
        treatment: describe_treatment(rows, METRIC, treatment) for treatment in ("ai", "manual")
    }
    censoring = {treatment: _censoring_summary(rows, treatment) for treatment in ("ai", "manual")}

    pairs = build_pairs(rows, METRIC)
    wilcoxon = wilcoxon_signed_rank(pairs, alternative=ALTERNATIVE)

    completed_rows = [row for row in rows if row.get("completed") is True]
    completed_only_pairs = build_pairs(completed_rows, METRIC)
    wilcoxon_completed_only = wilcoxon_signed_rank(completed_only_pairs, alternative=ALTERNATIVE)

    return RQ1Result(
        descriptive=descriptive,
        censoring=censoring,
        pairs=pairs,
        wilcoxon=wilcoxon,
        completed_only_pairs=completed_only_pairs,
        wilcoxon_completed_only=wilcoxon_completed_only,
    )


def _format(value: float | None, digits: int = 2) -> str:
    return "—" if value is None else f"{value:.{digits}f}"


def _descriptive_table(descriptive: dict[str, DescriptiveStats]) -> str:
    lines = [
        "| Tratamento | n | Mediana | Q1 | Q3 | IQR | Mínimo | Máximo | Concluídos | Ausentes |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for treatment in ("ai", "manual"):
        stats = descriptive[treatment]
        lines.append(
            f"| {treatment} | {stats.n} | {_format(stats.median, 0)} | {_format(stats.q1, 0)} | "
            f"{_format(stats.q3, 0)} | {_format(stats.iqr, 0)} | {_format(stats.minimum, 0)} | "
            f"{_format(stats.maximum, 0)} | {stats.completed} ({_format(stats.completed_pct)}%) | {stats.missing} |"
        )
    return "\n".join(lines) + "\n"


def _censoring_table(censoring: dict[str, CensoringSummary]) -> str:
    lines = ["| Tratamento | Trials | Censurados | % censurados |", "|---|---|---|---|"]
    for treatment in ("ai", "manual"):
        summary = censoring[treatment]
        lines.append(f"| {treatment} | {summary.n} | {summary.censored} | {_format(summary.censored_pct)}% |")
    return "\n".join(lines) + "\n"


def _wilcoxon_block(result: WilcoxonResult, *, title: str) -> str:
    return "\n".join(
        [
            f"### {title}",
            "",
            f"- Pares válidos: {result.n_pairs} (ausentes: {result.n_missing_pairs}, empates/diferença zero: {result.n_zero_diffs})",
            f"- Mediana das diferenças (manual - ai): {_format(result.median_diff, 1)} s",
            f"- Estatística W: {_format(result.statistic, 3)}",
            f"- p-valor (unilateral, manual > ai): {_format(result.p_value, 4)}",
            f"- Tamanho de efeito (correlação bisserial de postos): {_format(result.effect_size_r, 3)}",
            f"- IC 95% (bootstrap, exploratório) da mediana das diferenças: [{_format(result.ci_low, 1)}, {_format(result.ci_high, 1)}] s",
            "",
        ]
    )


def _pairs_table(pairs: list[Pair]) -> str:
    lines = [
        "| Participante | Bloco | Trial IA | duration (ai) | Trial Manual | duration (manual) | Diferença |",
        "|---|---|---|---|---|---|---|",
    ]
    for pair in pairs:
        diff = "—" if pair.difference is None else f"{pair.difference:+.0f}"
        lines.append(
            f"| {pair.participant_id} | {pair.difficulty_block} | {pair.ai_trial_id or '—'} | "
            f"{_format(pair.ai_value, 0)} | {pair.manual_trial_id or '—'} | {_format(pair.manual_value, 0)} | {diff} |"
        )
    return "\n".join(lines) + "\n"


def render_report_markdown(result: RQ1Result) -> str:
    verdict_p = result.wilcoxon.p_value
    verdict = (
        "há evidência exploratória de tempo menor com IA (p < 0,05)"
        if verdict_p is not None and verdict_p < 0.05
        else "não há evidência estatística suficiente de diferença na direção esperada"
    )
    sections = [
        "# RQ1 — Tempo de resolução e conclusão",
        "",
        "**Pergunta:** o tratamento com IA reduz o tempo de resolução em relação ao manual?",
        "",
        f"**Resumo:** {verdict}. Com apenas 3 participantes e 9 pares, o resultado é "
        "tratado como evidência exploratória, não conclusiva (Seção 14.3).",
        "",
        "## 1. Estatística descritiva (duration_seconds, em segundos)",
        "",
        _descriptive_table(result.descriptive),
        "## 2. Censura",
        "",
        "Trials sem sucesso dentro do limite permanecem com 2.100 segundos e `censored=true`; "
        "esse valor é usado no teste de postos, mas não representa o tempo real necessário (Seção 14.4).",
        "",
        _censoring_table(result.censoring),
        "## 3. Comparação inferencial — todos os pares (censurados incluídos)",
        "",
        _wilcoxon_block(result.wilcoxon, title="Wilcoxon unilateral (manual > ai)"),
        "## 4. Análise de sensibilidade — apenas trials concluídos",
        "",
        "Exclui qualquer par em que ao menos um lado não tenha concluído dentro do limite. "
        "Amostra menor e **condicionada ao sucesso**: sujeita a viés de seleção, não deve ser lida "
        "isoladamente (Seção 14.4).",
        "",
        _wilcoxon_block(result.wilcoxon_completed_only, title="Wilcoxon unilateral, apenas concluídos"),
        "## 5. Pares participante × bloco (análise principal)",
        "",
        _pairs_table(result.pairs),
        "## 6. Limitações",
        "",
        "- Três participantes geram nove pares não plenamente independentes (pseudorreplicação); "
        "o teste é evidência exploratória, não prova estatística formal.",
        "- A análise de sensibilidade tem amostra menor e viés de seleção por depender da conclusão.",
        "- O valor de `p` não é interpretado isoladamente (Seção 14.6): direção, magnitude, IQR e "
        "tamanho de efeito compõem a resposta.",
    ]
    return "\n".join(sections).rstrip() + "\n"


def render_figures(result: RQ1Result, output_dir: Path) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    # Distribuição por tratamento, com pontos individuais (18 trials são poucos
    # para esconder atrás de uma barra de média).
    fig, ax = plt.subplots(figsize=(5, 4))
    positions = {"ai": 0, "manual": 1}
    for treatment, position in positions.items():
        stats = result.descriptive[treatment]
        rows_values = [pair.ai_value if treatment == "ai" else pair.manual_value for pair in result.pairs]
        rows_values = [value for value in rows_values if value is not None]
        ax.scatter([position] * len(rows_values), rows_values, alpha=0.7, label=treatment)
        if stats.median is not None:
            ax.hlines(stats.median, position - 0.15, position + 0.15, color="black")
    ax.set_xticks(list(positions.values()))
    ax.set_xticklabels(list(positions.keys()))
    ax.set_ylabel("duration_seconds")
    ax.set_title("RQ1 — duração por tratamento (barra = mediana)")
    fig.tight_layout()
    duration_path = output_dir / "duration_by_treatment.png"
    fig.savefig(duration_path, dpi=150)
    plt.close(fig)
    paths.append(duration_path)

    # Gráfico pareado: liga ai -> manual por participante/bloco.
    fig, ax = plt.subplots(figsize=(5, 4))
    for pair in result.pairs:
        if not pair.valid:
            continue
        ax.plot([0, 1], [pair.ai_value, pair.manual_value], marker="o", alpha=0.7, color="tab:gray")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["ai", "manual"])
    ax.set_ylabel("duration_seconds")
    ax.set_title("RQ1 — pares participante × bloco")
    fig.tight_layout()
    paired_path = output_dir / "paired_duration.png"
    fig.savefig(paired_path, dpi=150)
    plt.close(fig)
    paths.append(paired_path)

    return paths
