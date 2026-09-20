"""RQ2 — defeitos e taxa de sucesso: IA aumenta a taxa de sucesso dos testes?

Compara `success_rate` (`passed_tests / total_tests × 100`) entre tratamentos.
`failed_tests` é reportado como métrica complementar, nunca substituindo a
taxa de sucesso como medida primária (Seção 14 / critérios de S03-03).
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

SUCCESS_METRIC = "success_rate"
FAILED_METRIC = "failed_tests"
ALTERNATIVE = "greater"  # H1: success_rate(ai) > success_rate(manual)


@dataclass(frozen=True)
class GreenSummary:
    treatment: str
    n: int
    fully_green: int
    fully_green_pct: float | None


@dataclass(frozen=True)
class RQ2Result:
    success_descriptive: dict[str, DescriptiveStats]
    failed_descriptive: dict[str, DescriptiveStats]
    green: dict[str, GreenSummary]
    success_pairs: list[Pair]
    wilcoxon: WilcoxonResult


def _green_summary(rows: list[dict[str, Any]], treatment: str) -> GreenSummary:
    treatment_rows = [row for row in rows if row["treatment"] == treatment]
    fully_green = sum(1 for row in treatment_rows if row.get("success_rate") == 100)
    pct = round(fully_green / len(treatment_rows) * 100, 2) if treatment_rows else None
    return GreenSummary(treatment=treatment, n=len(treatment_rows), fully_green=fully_green, fully_green_pct=pct)


def analyze(rows: list[dict[str, Any]]) -> RQ2Result:
    # Direção invertida: success_rate(manual) - success_rate(ai) é o que build_pairs
    # calcula por padrão (manual - ai); testamos alternative="less" para capturar
    # "ai aumenta" como a mesma direção usada em wilcoxon_signed_rank(manual - ai).
    success_pairs = build_pairs(rows, SUCCESS_METRIC)
    wilcoxon = wilcoxon_signed_rank(success_pairs, alternative="less")

    return RQ2Result(
        success_descriptive={t: describe_treatment(rows, SUCCESS_METRIC, t) for t in ("ai", "manual")},
        failed_descriptive={t: describe_treatment(rows, FAILED_METRIC, t) for t in ("ai", "manual")},
        green={t: _green_summary(rows, t) for t in ("ai", "manual")},
        success_pairs=success_pairs,
        wilcoxon=wilcoxon,
    )


def _format(value: float | None, digits: int = 2) -> str:
    return "—" if value is None else f"{value:.{digits}f}"


def _descriptive_table(descriptive: dict[str, DescriptiveStats], *, unit: str) -> str:
    lines = [
        f"| Tratamento | n | Mediana ({unit}) | Q1 | Q3 | IQR | Mínimo | Máximo | Ausentes |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for treatment in ("ai", "manual"):
        stats = descriptive[treatment]
        lines.append(
            f"| {treatment} | {stats.n} | {_format(stats.median)} | {_format(stats.q1)} | {_format(stats.q3)} | "
            f"{_format(stats.iqr)} | {_format(stats.minimum)} | {_format(stats.maximum)} | {stats.missing} |"
        )
    return "\n".join(lines) + "\n"


def _green_table(green: dict[str, GreenSummary]) -> str:
    lines = ["| Tratamento | Trials | 100% verdes | % |", "|---|---|---|---|"]
    for treatment in ("ai", "manual"):
        summary = green[treatment]
        lines.append(f"| {treatment} | {summary.n} | {summary.fully_green} | {_format(summary.fully_green_pct)}% |")
    return "\n".join(lines) + "\n"


def _pairs_table(pairs: list[Pair]) -> str:
    lines = [
        "| Participante | Bloco | Trial IA | success_rate (ai) | Trial Manual | success_rate (manual) | Diferença |",
        "|---|---|---|---|---|---|---|",
    ]
    for pair in pairs:
        diff = "—" if pair.difference is None else f"{pair.difference:+.2f}"
        lines.append(
            f"| {pair.participant_id} | {pair.difficulty_block} | {pair.ai_trial_id or '—'} | "
            f"{_format(pair.ai_value)} | {pair.manual_trial_id or '—'} | {_format(pair.manual_value)} | {diff} |"
        )
    return "\n".join(lines) + "\n"


def render_report_markdown(result: RQ2Result) -> str:
    p_value = result.wilcoxon.p_value
    verdict = (
        "há evidência exploratória de taxa de sucesso maior com IA (p < 0,05)"
        if p_value is not None and p_value < 0.05
        else "não há evidência estatística suficiente de diferença na direção esperada"
    )
    sections = [
        "# RQ2 — Defeitos e taxa de sucesso",
        "",
        "**Pergunta:** o tratamento com IA aumenta a taxa de sucesso dos testes de aceitação em relação ao manual?",
        "",
        f"**Resumo:** {verdict}. Katas diferentes têm quantidades de teste distintas, então a taxa "
        "de sucesso (não a contagem bruta de testes) é a métrica primária.",
        "",
        "## 1. Taxa de sucesso por tratamento (%)",
        "",
        _descriptive_table(result.success_descriptive, unit="%"),
        "## 2. Testes falhando (métrica complementar, nunca substitui a taxa de sucesso)",
        "",
        _descriptive_table(result.failed_descriptive, unit="testes"),
        "## 3. Trials completamente verdes (success_rate = 100%)",
        "",
        _green_table(result.green),
        "## 4. Comparação inferencial",
        "",
        "### Wilcoxon unilateral (ai > manual)",
        "",
        f"- Pares válidos: {result.wilcoxon.n_pairs} (ausentes: {result.wilcoxon.n_missing_pairs}, "
        f"empates/diferença zero: {result.wilcoxon.n_zero_diffs})",
        f"- Mediana das diferenças (manual - ai): {_format(result.wilcoxon.median_diff)} p.p.",
        f"- Estatística W: {_format(result.wilcoxon.statistic, 3)}",
        f"- p-valor (unilateral, ai > manual): {_format(result.wilcoxon.p_value, 4)}",
        f"- Tamanho de efeito (correlação bisserial de postos): {_format(result.wilcoxon.effect_size_r, 3)}",
        f"- IC 95% (bootstrap, exploratório): [{_format(result.wilcoxon.ci_low)}, {_format(result.wilcoxon.ci_high)}] p.p.",
        "",
        "## 5. Pares participante × bloco",
        "",
        _pairs_table(result.success_pairs),
        "## 6. Limitações",
        "",
        "- Testes de aceitação são um proxy de qualidade funcional, não uma contagem completa de defeitos.",
        "- Muitos trials atingem 100% de sucesso (efeito-teto): com pouca variação, o teste de postos "
        "perde poder para distinguir tratamentos.",
        "- Nove pares de três participantes não são plenamente independentes; resultado exploratório "
        "(Seção 14.3).",
    ]
    return "\n".join(sections).rstrip() + "\n"


def render_figures(result: RQ2Result, output_dir: Path) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    fig, ax = plt.subplots(figsize=(5, 4))
    positions = {"ai": 0, "manual": 1}
    for treatment, position in positions.items():
        values = [
            pair.ai_value if treatment == "ai" else pair.manual_value
            for pair in result.success_pairs
            if (pair.ai_value if treatment == "ai" else pair.manual_value) is not None
        ]
        ax.scatter([position] * len(values), values, alpha=0.7, label=treatment)
        stats = result.success_descriptive[treatment]
        if stats.median is not None:
            ax.hlines(stats.median, position - 0.15, position + 0.15, color="black")
    ax.set_xticks(list(positions.values()))
    ax.set_xticklabels(list(positions.keys()))
    ax.set_ylabel("success_rate (%)")
    ax.set_ylim(-5, 105)
    ax.set_title("RQ2 — taxa de sucesso por tratamento (barra = mediana)")
    fig.tight_layout()
    success_path = output_dir / "success_rate_by_treatment.png"
    fig.savefig(success_path, dpi=150)
    plt.close(fig)
    paths.append(success_path)

    fig, ax = plt.subplots(figsize=(5, 4))
    for pair in result.success_pairs:
        if not pair.valid:
            continue
        ax.plot([0, 1], [pair.ai_value, pair.manual_value], marker="o", alpha=0.7, color="tab:gray")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["ai", "manual"])
    ax.set_ylabel("success_rate (%)")
    ax.set_ylim(-5, 105)
    ax.set_title("RQ2 — pares participante × bloco")
    fig.tight_layout()
    paired_path = output_dir / "paired_success_rate.png"
    fig.savefig(paired_path, dpi=150)
    plt.close(fig)
    paths.append(paired_path)

    return paths
