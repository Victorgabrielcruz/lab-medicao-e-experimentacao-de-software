"""Analisa a RQ07 a partir do dataset consolidado das RQ01--RQ06.

RQ07: sistemas escritos em linguagens mais populares recebem mais contribuição
externa, lançam mais releases e são atualizados com mais frequência?

Uso:
    python src/analysis/rq07_analysis.py data/processed/repos_rq07_consolidated_<coleta>.csv

Sem argumento, usa o dataset consolidado mais recente. A análise não altera a
base de entrada; ela produz tabelas, evidências de outliers, relatório e SVGs.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from html import escape
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "reports" / "drafts"
FIGURES_DIR = ROOT / "reports" / "figures"

RQ07_METRICS = {
    "accepted_pull_requests": "Pull requests aceitas",
    "releases_count": "Releases",
    "days_since_push": "Dias desde o último push",
}
CORRELATION_METRICS = {
    "age_years": "Idade (anos)",
    "accepted_pull_requests": "Pull requests aceitas",
    "releases_count": "Releases",
    "days_since_push": "Dias desde o último push",
    "total_issues": "Issues totais",
    "closed_issues_percentage": "% de issues fechadas",
}
REQUIRED_COLUMNS = [
    "id", "name_with_owner", "stargazer_count", "language_group",
    "is_popular_language", *RQ07_METRICS, *CORRELATION_METRICS,
]
UNIDENTIFIED_LANGUAGE = "Sem linguagem identificada"


@dataclass
class AnalysisResult:
    group_statistics: pd.DataFrame
    correlations: pd.DataFrame
    outliers: pd.DataFrame
    repositories: int
    excluded_without_language: int


def latest_consolidated_csv() -> Path:
    """Retorna o consolidado mais recente, sem confundir saídas da análise."""
    files = sorted(PROCESSED_DIR.glob("repos_rq07_consolidated_*.csv"))
    if not files:
        raise FileNotFoundError(f"Nenhum dataset consolidado encontrado em {PROCESSED_DIR}.")
    return files[-1]


def load(path: Path) -> pd.DataFrame:
    """Carrega e confere as colunas necessárias para a RQ07."""
    df = pd.read_csv(path, dtype={"id": "string"})
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(missing)}")
    return df


def prepare(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Normaliza tipos e separa linguagem popular, não popular e ausente."""
    prepared = df.copy()
    numeric_columns = set(RQ07_METRICS) | set(CORRELATION_METRICS) | {"stargazer_count"}
    for column in numeric_columns:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")

    popular = prepared["is_popular_language"]
    if popular.dtype != bool:
        popular = popular.astype(str).str.strip().str.lower().map({"true": True, "false": False})
    prepared["is_popular_language"] = popular

    without_language = prepared["language_group"].isna() | prepared["language_group"].eq(UNIDENTIFIED_LANGUAGE)
    prepared["language_category"] = pd.NA
    prepared.loc[~without_language & prepared["is_popular_language"].eq(True), "language_category"] = "Popular"
    prepared.loc[~without_language & prepared["is_popular_language"].eq(False), "language_category"] = "Não popular"

    return prepared, int(without_language.sum())


def group_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula estatísticas exploratórias das métricas RQ02--RQ04 por grupo."""
    rows: list[dict] = []
    valid = df.dropna(subset=["language_category"])
    for category in ["Popular", "Não popular"]:
        group = valid.loc[valid["language_category"] == category]
        for metric, label in RQ07_METRICS.items():
            values = group[metric].dropna()
            rows.append({
                "grupo": category,
                "metrica": metric,
                "descricao": label,
                "n": int(values.size),
                "media": float(values.mean()) if not values.empty else float("nan"),
                "mediana": float(values.median()) if not values.empty else float("nan"),
                "q1": float(values.quantile(0.25)) if not values.empty else float("nan"),
                "q3": float(values.quantile(0.75)) if not values.empty else float("nan"),
            })
    return pd.DataFrame(rows)


def correlations(df: pd.DataFrame) -> pd.DataFrame:
    """Relaciona popularidade por estrelas com métricas das RQ01--RQ06."""
    rows: list[dict] = []
    for metric, label in CORRELATION_METRICS.items():
        paired = df[["stargazer_count", metric]].dropna()
        rows.append({
            "metrica": metric,
            "descricao": label,
            "n": int(len(paired)),
            "pearson": float(paired["stargazer_count"].corr(paired[metric], method="pearson")),
            # Spearman é a correlação de Pearson aplicada aos postos. Assim a
            # análise não depende de scipy, que não faz parte do ambiente.
            "spearman": float(paired["stargazer_count"].rank().corr(paired[metric].rank())),
        })
    return pd.DataFrame(rows)


def identify_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Sinaliza valores IQR das métricas diretamente relacionadas à RQ07."""
    rows: list[dict] = []
    for metric, label in RQ07_METRICS.items():
        values = df[metric].dropna()
        q1, q3 = values.quantile([0.25, 0.75])
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        mask = (df[metric] < lower) | (df[metric] > upper)
        for _, row in df.loc[mask].iterrows():
            rows.append({
                "id": row["id"],
                "name_with_owner": row["name_with_owner"],
                "language_category": row["language_category"],
                "metrica": metric,
                "descricao": label,
                "valor": row[metric],
                "limite_inferior": lower,
                "limite_superior": upper,
            })
    return pd.DataFrame(rows, columns=[
        "id", "name_with_owner", "language_category", "metrica", "descricao",
        "valor", "limite_inferior", "limite_superior",
    ])


def analyze(df: pd.DataFrame) -> AnalysisResult:
    """Executa todas as análises quantitativas da RQ07."""
    prepared, excluded = prepare(df)
    return AnalysisResult(
        group_statistics=group_statistics(prepared),
        correlations=correlations(prepared),
        outliers=identify_outliers(prepared),
        repositories=len(prepared),
        excluded_without_language=excluded,
    )


def stamp_for(source: Path) -> str:
    return source.stem.removeprefix("repos_rq07_consolidated_")


def svg_bar_chart(path: Path, title: str, labels: list[str], values: list[float], color: str, centered: bool = False) -> Path:
    """Gera um gráfico SVG simples sem depender de bibliotecas externas."""
    path.parent.mkdir(parents=True, exist_ok=True)
    width, height, left, bottom = 900, 480, 100, 90
    chart_height, chart_width = height - bottom - 70, width - left - 40
    maximum = max([abs(value) for value in values] or [1]) or 1
    baseline = 70 + chart_height / 2 if centered else 70 + chart_height
    scale = (chart_height / 2 if centered else chart_height) / maximum
    bar_width = chart_width / max(len(values) * 1.7, 1)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width / 2}" y="35" text-anchor="middle" font-family="Arial" font-size="20" font-weight="bold">{escape(title)}</text>',
        f'<line x1="{left}" y1="{baseline:.1f}" x2="{width - 40}" y2="{baseline:.1f}" stroke="#555"/>',
    ]
    for index, (label, value) in enumerate(zip(labels, values)):
        x = left + (index + 0.5) * chart_width / max(len(values), 1) - bar_width / 2
        bar_height = abs(value) * scale
        y = baseline - bar_height if value >= 0 else baseline
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" fill="{color}"/>')
        parts.append(f'<text x="{x + bar_width / 2:.1f}" y="{y - 7 if value >= 0 else y + bar_height + 18:.1f}" text-anchor="middle" font-family="Arial" font-size="13">{value:.2f}</text>')
        parts.append(f'<text x="{x + bar_width / 2:.1f}" y="{height - 45}" text-anchor="middle" font-family="Arial" font-size="12">{escape(label)}</text>')
    parts.append('</svg>')
    path.write_text("\n".join(parts), encoding="utf-8")
    return path


def save_figures(result: AnalysisResult, stamp: str) -> tuple[Path, Path]:
    medians = result.group_statistics.pivot(index="metrica", columns="grupo", values="mediana")
    # Diferença de medianas torna as três escalas comparáveis no mesmo gráfico.
    difference = [float(medians.loc[metric, "Popular"] - medians.loc[metric, "Não popular"]) for metric in RQ07_METRICS]
    group_figure = svg_bar_chart(
        FIGURES_DIR / f"rq07_median_differences_{stamp}.svg",
        "RQ07 — mediana: popular menos não popular",
        list(RQ07_METRICS.values()),
        difference,
        "#1f77b4",
        centered=True,
    )
    correlation_figure = svg_bar_chart(
        FIGURES_DIR / f"rq07_star_correlations_{stamp}.svg",
        "Correlação de Spearman com estrelas",
        result.correlations["descricao"].tolist(),
        result.correlations["spearman"].tolist(),
        "#ff7f0e",
        centered=True,
    )
    return group_figure, correlation_figure


def report_text(result: AnalysisResult, source: Path, statistics_path: Path, outliers_path: Path, figures: tuple[Path, Path]) -> str:
    lines = [
        "# Análise quantitativa da RQ07",
        "",
        f"Base analisada: `{source.name}`.",
        f"Repositórios: **{result.repositories}**. Sem linguagem identificada e excluídos da comparação entre linguagens: **{result.excluded_without_language}**.",
        "",
        "## Variáveis e método",
        "",
        "A comparação principal separa linguagens classificadas como populares pela fonte adotada pelo projeto das não populares. "
        "A RQ02 é representada por `accepted_pull_requests`, a RQ03 por `releases_count` e a RQ04 por `days_since_push`. "
        "Para RQ04, valor menor significa atualização mais frequente.",
        "",
        "As relações entre estrelas e métricas são apresentadas por correlações de Pearson e Spearman. Correlação descreve associação, não causalidade.",
        "",
        "## Comparação por popularidade da linguagem",
        "",
        "| grupo | métrica | n | média | mediana | Q1 | Q3 |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for _, row in result.group_statistics.iterrows():
        lines.append(f"| {row.grupo} | {row.descricao} | {row.n:.0f} | {row.media:.2f} | {row.mediana:.2f} | {row.q1:.2f} | {row.q3:.2f} |")

    lines += [
        "",
        "## Correlação com popularidade por estrelas",
        "",
        "| métrica | n | Pearson | Spearman |",
        "|---|---:|---:|---:|",
    ]
    for _, row in result.correlations.iterrows():
        lines.append(f"| {row.descricao} | {row.n:.0f} | {row.pearson:.3f} | {row.spearman:.3f} |")

    outlier_counts = result.outliers.groupby("descricao").size() if not result.outliers.empty else pd.Series(dtype=int)
    lines += ["", "## Outliers relevantes", "", "Método: cercas de Tukey (IQR, 1,5 × IQR). Os casos são evidência para interpretação; não foram removidos.", ""]
    for label in RQ07_METRICS.values():
        lines.append(f"- {label}: **{int(outlier_counts.get(label, 0))}** ocorrência(s) sinalizada(s).")

    lines += [
        "",
        "## Artefatos gerados",
        "",
        f"- Estatísticas: `{relative_path(statistics_path)}`",
        f"- Outliers: `{relative_path(outliers_path)}`",
        f"- Visualização de diferenças de mediana: `{relative_path(figures[0])}`",
        f"- Visualização de correlações: `{relative_path(figures[1])}`",
        "",
        "A interpretação substantiva dos resultados e a resposta final da RQ07 pertencem à S03-03.",
    ]
    return "\n".join(lines) + "\n"


def relative_path(path: Path) -> str:
    """Exibe caminho do projeto ou somente nome para caminhos externos de teste."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return path.name


def run(source: Path) -> tuple[AnalysisResult, dict[str, Path]]:
    """Executa a análise e grava todos os artefatos de evidência."""
    result = analyze(load(source))
    stamp = stamp_for(source)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    statistics_path = PROCESSED_DIR / f"rq07_statistics_{stamp}.csv"
    outliers_path = PROCESSED_DIR / f"rq07_analysis_outliers_{stamp}.csv"
    report_path = REPORTS_DIR / f"rq07_analysis_{stamp}.md"

    statistics = pd.concat([
        result.group_statistics.assign(tipo="grupo"),
        result.correlations.assign(tipo="correlacao"),
    ], ignore_index=True, sort=False)
    statistics.to_csv(statistics_path, index=False)
    result.outliers.to_csv(outliers_path, index=False)
    figures = save_figures(result, stamp)
    report_path.write_text(report_text(result, source, statistics_path, outliers_path, figures), encoding="utf-8")
    return result, {
        "statistics": statistics_path,
        "outliers": outliers_path,
        "report": report_path,
        "median_figure": figures[0],
        "correlation_figure": figures[1],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Executa a análise integrada da RQ07.")
    parser.add_argument("source", nargs="?", type=Path, help="Dataset consolidado da RQ07")
    args = parser.parse_args()
    source = args.source or latest_consolidated_csv()
    result, outputs = run(source)
    print(f"Repositórios analisados: {result.repositories}")
    print(f"Sem linguagem (excluídos da comparação): {result.excluded_without_language}")
    print(f"Outliers RQ07: {len(result.outliers)}")
    for label, path in outputs.items():
        print(f"{label}: {path}")


if __name__ == "__main__":
    main()
