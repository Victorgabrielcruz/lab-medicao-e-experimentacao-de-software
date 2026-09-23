"""RQ3 — qualidade estrutural: IA produz código menos complexo/duplicado?

Complexidade ciclomática média e duplicação são comparadas com testes de
Wilcoxon bilaterais; os dois valores de `p` são ajustados pelo método de
Holm (Seção 14.3). LOC acompanha toda comparação estrutural como covariável
de tamanho, sem entrar no teste. O Índice de Manutenibilidade é apenas
exploratório. Métricas estruturais ausentes (Seção 12) nunca viram zero: o
par correspondente fica fora do teste e é listado separadamente.
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
    holm_correction,
    wilcoxon_signed_rank,
)

COMPLEXITY_METRIC = "mean_cyclomatic_complexity"
DUPLICATION_METRIC = "duplication_percentage"
LOC_METRIC = "loc"
MAINTAINABILITY_METRIC = "maintainability_index"
ALTERNATIVE = "two-sided"


@dataclass(frozen=True)
class RQ3Result:
    complexity_descriptive: dict[str, DescriptiveStats]
    duplication_descriptive: dict[str, DescriptiveStats]
    loc_descriptive: dict[str, DescriptiveStats]
    maintainability_descriptive: dict[str, DescriptiveStats]
    complexity_pairs: list[Pair]
    duplication_pairs: list[Pair]
    loc_pairs: list[Pair]
    complexity_wilcoxon: WilcoxonResult
    duplication_wilcoxon: WilcoxonResult
    complexity_p_holm: float | None
    duplication_p_holm: float | None


def analyze(rows: list[dict[str, Any]]) -> RQ3Result:
    complexity_pairs = build_pairs(rows, COMPLEXITY_METRIC)
    duplication_pairs = build_pairs(rows, DUPLICATION_METRIC)
    loc_pairs = build_pairs(rows, LOC_METRIC)

    complexity_wilcoxon = wilcoxon_signed_rank(
        complexity_pairs, alternative=ALTERNATIVE, difference_direction="ai-manual"
    )
    duplication_wilcoxon = wilcoxon_signed_rank(
        duplication_pairs, alternative=ALTERNATIVE, difference_direction="ai-manual"
    )

    raw_p_values = [complexity_wilcoxon.p_value, duplication_wilcoxon.p_value]
    # A família foi pré-registrada com dois testes. Um desfecho todo empatado
    # não fornece p calculável; p=1 apenas no ajuste mantém a família de dois.
    holm_adjusted = holm_correction([value if value is not None else 1.0
                                     for value in raw_p_values])

    return RQ3Result(
        complexity_descriptive={t: describe_treatment(rows, COMPLEXITY_METRIC, t) for t in ("ai", "manual")},
        duplication_descriptive={t: describe_treatment(rows, DUPLICATION_METRIC, t) for t in ("ai", "manual")},
        loc_descriptive={t: describe_treatment(rows, LOC_METRIC, t) for t in ("ai", "manual")},
        maintainability_descriptive={t: describe_treatment(rows, MAINTAINABILITY_METRIC, t) for t in ("ai", "manual")},
        complexity_pairs=complexity_pairs,
        duplication_pairs=duplication_pairs,
        loc_pairs=loc_pairs,
        complexity_wilcoxon=complexity_wilcoxon,
        duplication_wilcoxon=duplication_wilcoxon,
        complexity_p_holm=holm_adjusted[0] if raw_p_values[0] is not None else None,
        duplication_p_holm=holm_adjusted[1] if raw_p_values[1] is not None else None,
    )


def _format(value: float | None, digits: int = 2) -> str:
    return "—" if value is None else f"{0.0 if value == 0 else value:.{digits}f}"


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


def _wilcoxon_block(result: WilcoxonResult, adjusted_p: float | None, *, title: str, unit: str) -> str:
    return "\n".join(
        [
            f"### {title}",
            "",
            f"- Pares válidos: {result.n_pairs} (ausentes: {result.n_missing_pairs}, "
            f"empates/diferença zero: {result.n_zero_diffs})",
            f"- Mediana das diferenças (ai - manual): {_format(result.median_diff)} {unit}",
            f"- Estatística W: {_format(result.statistic, 3)}",
            f"- p-valor (bilateral, bruto): {_format(result.p_value, 4)}",
            f"- p-valor ajustado (Holm, 2 comparações): {_format(adjusted_p, 4)}",
            f"- Tamanho de efeito (correlação bisserial de postos): {_format(result.effect_size_r, 3)}",
            f"- IC 95% (bootstrap, exploratório): [{_format(result.ci_low)}, {_format(result.ci_high)}] {unit}",
            "",
        ]
    )


def _combined_pairs_table(result: RQ3Result) -> str:
    lines = [
        "| Participante | Bloco | Trial IA | LOC (ai) | Complexidade (ai) | Duplicação % (ai) | "
        "Trial Manual | LOC (manual) | Complexidade (manual) | Duplicação % (manual) |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for complexity_pair, duplication_pair, loc_pair in zip(
        result.complexity_pairs, result.duplication_pairs, result.loc_pairs
    ):
        lines.append(
            f"| {complexity_pair.participant_id} | {complexity_pair.difficulty_block} | "
            f"{complexity_pair.ai_trial_id or '—'} | {_format(loc_pair.ai_value, 0)} | "
            f"{_format(complexity_pair.ai_value)} | {_format(duplication_pair.ai_value)} | "
            f"{complexity_pair.manual_trial_id or '—'} | {_format(loc_pair.manual_value, 0)} | "
            f"{_format(complexity_pair.manual_value)} | {_format(duplication_pair.manual_value)} |"
        )
    return "\n".join(lines) + "\n"


def render_report_markdown(result: RQ3Result) -> str:
    valid_complexity = result.complexity_wilcoxon.n_pairs
    total_pairs = valid_complexity + result.complexity_wilcoxon.n_missing_pairs
    sections = [
        "# RQ3 — Qualidade estrutural (complexidade e duplicação)",
        "",
        "**Pergunta:** o tratamento com IA altera a complexidade e a duplicação do código, "
        "controlando o tamanho (LOC)?",
        "",
        f"**Resumo:** apenas {valid_complexity} de {total_pairs} pares têm métricas estruturais nos "
        "dois lados (Seção 12: valores ausentes nunca viram zero); a amostra efetiva para RQ3 é "
        "pequena e os resultados abaixo são fortemente exploratórios.",
        "",
        "## 1. LOC por tratamento (covariável de tamanho)",
        "",
        _descriptive_table(result.loc_descriptive, unit="linhas"),
        "## 2. Complexidade ciclomática média por tratamento",
        "",
        _descriptive_table(result.complexity_descriptive, unit="complexidade"),
        "## 3. Duplicação por tratamento (%)",
        "",
        _descriptive_table(result.duplication_descriptive, unit="%"),
        "## 4. Índice de Manutenibilidade (exploratório, não é métrica principal)",
        "",
        _descriptive_table(result.maintainability_descriptive, unit="MI"),
        "## 5. Comparação inferencial (bilateral, ajustada por Holm)",
        "",
        "A família pré-registrada contém dois testes. Quando todos os pares de um "
        "desfecho empatam, seu p bruto permanece indefinido; apenas para o ajuste "
        "de Holm ele é tratado como 1, preservando a família de dois testes.",
        "",
        _wilcoxon_block(
            result.complexity_wilcoxon, result.complexity_p_holm, title="Complexidade ciclomática média", unit="pts"
        ),
        _wilcoxon_block(
            result.duplication_wilcoxon, result.duplication_p_holm, title="Duplicação", unit="p.p."
        ),
        "## 6. Pares participante × bloco (LOC, complexidade e duplicação lado a lado)",
        "",
        _combined_pairs_table(result),
        "## 7. Limitações",
        "",
        "- Métricas estruturais estão ausentes para vários trials manuais antigos "
        "(coleta retroativa incompleta); esses pares ficam fora dos testes de RQ3, "
        "reduzindo bastante a amostra efetiva.",
        "- Código de teste, dependências e arquivos gerados não entram nas métricas "
        "(configuração de coleta em `radon.cfg`/`.jscpd.json`).",
        "- LOC é reportado ao lado de toda comparação estrutural porque complexidade e "
        "duplicação absolutas tendem a crescer com o tamanho do código.",
        "- O Índice de Manutenibilidade é exploratório: combina LOC, complexidade e comentários "
        "em uma única escala e não substitui as métricas primárias.",
        "- Nove pares de três participantes não são plenamente independentes; resultado "
        "exploratório (Seção 14.3).",
    ]
    return "\n".join(sections).rstrip() + "\n"


def render_figures(result: RQ3Result, output_dir: Path) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    def _scatter_by_treatment(pairs: list[Pair], descriptive: dict[str, DescriptiveStats], ylabel: str, filename: str, title: str) -> Path:
        fig, ax = plt.subplots(figsize=(5, 4))
        positions = {"ai": 0, "manual": 1}
        for treatment, position in positions.items():
            values = [
                pair.ai_value if treatment == "ai" else pair.manual_value
                for pair in pairs
                if (pair.ai_value if treatment == "ai" else pair.manual_value) is not None
            ]
            ax.scatter([position] * len(values), values, alpha=0.7, label=treatment)
            stats = descriptive[treatment]
            if stats.median is not None:
                ax.hlines(stats.median, position - 0.15, position + 0.15, color="black")
        ax.set_xticks(list(positions.values()))
        ax.set_xticklabels(list(positions.keys()))
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        fig.tight_layout()
        path = output_dir / filename
        fig.savefig(path, dpi=150)
        plt.close(fig)
        return path

    paths.append(
        _scatter_by_treatment(
            result.complexity_pairs,
            result.complexity_descriptive,
            "mean_cyclomatic_complexity",
            "complexity_by_treatment.png",
            "RQ3 — complexidade por tratamento (barra = mediana)",
        )
    )
    paths.append(
        _scatter_by_treatment(
            result.duplication_pairs,
            result.duplication_descriptive,
            "duplication_percentage",
            "duplication_by_treatment.png",
            "RQ3 — duplicação por tratamento (barra = mediana)",
        )
    )

    fig, ax = plt.subplots(figsize=(5, 4))
    for loc_pair, complexity_pair in zip(result.loc_pairs, result.complexity_pairs):
        for loc_value, complexity_value, treatment in (
            (loc_pair.ai_value, complexity_pair.ai_value, "ai"),
            (loc_pair.manual_value, complexity_pair.manual_value, "manual"),
        ):
            if loc_value is not None and complexity_value is not None:
                color = "tab:blue" if treatment == "ai" else "tab:orange"
                ax.scatter(loc_value, complexity_value, color=color, alpha=0.7, label=treatment)
    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    ax.legend(unique.values(), unique.keys())
    ax.set_xlabel("loc")
    ax.set_ylabel("mean_cyclomatic_complexity")
    ax.set_title("RQ3 — LOC x complexidade")
    fig.tight_layout()
    scatter_path = output_dir / "loc_vs_complexity.png"
    fig.savefig(scatter_path, dpi=150)
    plt.close(fig)
    paths.append(scatter_path)

    return paths
