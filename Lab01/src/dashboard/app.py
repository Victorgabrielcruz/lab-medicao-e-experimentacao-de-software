
from __future__ import annotations

import io
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# Tema escuro tanto na interface (`.streamlit/config.toml`) quanto nos
# gráficos Matplotlib, para não haver retângulos brancos destoando do fundo.
plt.style.use("dark_background")
DASHBOARD_BACKGROUND = "#0e1117"

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"

UNIDENTIFIED_LANGUAGE = "Sem linguagem identificada"

# RQ01-06: coluna derivada, título, descrição da métrica (coerente com
# docs/methodology.md) e tipo de gráfico mais adequado.
RQ_DEFINITIONS = [
    {
        "rq": "RQ01",
        "titulo": "Idade do repositório",
        "coluna": "age_years",
        "descricao": "Quantos anos o repositório tem, da data de criação até a data da coleta.",
        "tipo": "histograma",
    },
    {
        "rq": "RQ02",
        "titulo": "Pull requests aceitas",
        "coluna": "accepted_pull_requests",
        "descricao": "Quantidade de contribuições de outras pessoas (Pull Requests) que foram aceitas no repositório.",
        "tipo": "histograma",
    },
    {
        "rq": "RQ03",
        "titulo": "Releases",
        "coluna": "releases_count",
        "descricao": "Quantidade total de versões (releases) publicadas pelo repositório.",
        "tipo": "histograma",
    },
    {
        "rq": "RQ04",
        "titulo": "Atividade e frequência de atualização",
        "coluna": "days_since_push",
        "descricao": "Quantos dias se passaram desde a última atualização de código. Quanto menor, mais recente a atividade.",
        "tipo": "histograma",
    },
    {
        "rq": "RQ05",
        "titulo": "Linguagem de programação",
        "coluna": "language_group",
        "descricao": "Linguagem de programação principal de cada repositório.",
        "tipo": "barras_categoria",
    },
    {
        "rq": "RQ06",
        "titulo": "Percentual de issues fechadas",
        "coluna": "closed_issues_percentage",
        "descricao": "Percentual de issues (problemas relatados) que já foram fechadas. Repositórios sem nenhuma issue não entram nesta conta.",
        "tipo": "histograma",
    },
]

# RQ07: métricas comparadas entre linguagem popular e não popular
# (docs/methodology.md, seção RQ07), reaproveitando as mesmas colunas de
# RQ02/RQ03/RQ04 já presentes no dataset consolidado.
RQ07_METRICS = {
    "accepted_pull_requests": "Pull requests aceitas (RQ02)",
    "releases_count": "Releases (RQ03)",
    "days_since_push": "Dias desde o último push (RQ04)",
}

# RQ07: rótulos amigáveis para as correlações entre estrelas (popularidade)
# e as métricas de RQ01-RQ06, geradas por `rq07_analysis.py` (tipo == "correlacao"
# em rq07_statistics_<coleta>.csv).
RQ07_CORRELATION_LABELS = {
    "age_years": "Idade (anos) — RQ01",
    "accepted_pull_requests": "Pull requests aceitas — RQ02",
    "releases_count": "Releases — RQ03",
    "days_since_push": "Dias desde o último push — RQ04",
    "total_issues": "Issues totais — RQ06",
    "closed_issues_percentage": "% de issues fechadas — RQ06",
}

# RQ04: métricas complementares de atividade (metodologia, seção 9), exibidas
# como estatísticas resumidas ao lado do histograma principal de
# `days_since_push`, sem gráfico adicional.
RQ04_EXTRA_METRICS = {
    "development_period_days": "Período de desenvolvimento (dias)",
    "total_commits": "Quantidade de commits",
}


def list_processed_datasets() -> list[Path]:
    """Lista os CSVs processados disponíveis, do mais recente para o mais antigo."""
    return sorted(PROCESSED_DIR.glob("repos_processed_*.csv"), reverse=True)


def stamp_for(path: Path) -> str:
    return path.stem.removeprefix("repos_processed_")


@st.cache_data(show_spinner=False)
def load_processed(path: str) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"id": "string"})


@st.cache_data(show_spinner=False)
def load_csv_if_exists(path: str) -> pd.DataFrame | None:
    file = Path(path)
    if not file.exists():
        return None
    return pd.read_csv(file, dtype={"id": "string"})


def rq07_artifacts_for(stamp: str) -> tuple[Path, Path]:
    """Caminhos dos artefatos da RQ07 para a mesma coleta do processado escolhido."""
    consolidated = PROCESSED_DIR / f"repos_rq07_consolidated_{stamp}.csv"
    statistics = PROCESSED_DIR / f"rq07_statistics_{stamp}.csv"
    return consolidated, statistics


def outliers_path_for(stamp: str) -> Path:
    """Caminho do CSV de outliers (S03-04/S03-05) para a mesma coleta."""
    return PROCESSED_DIR / f"outliers_{stamp}.csv"


def fig_download_buttons(fig: plt.Figure, key: str) -> None:
    """Botões de download do gráfico em PNG e SVG, sem alterar a figura exibida."""
    png_buffer = io.BytesIO()
    fig.savefig(png_buffer, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    svg_buffer = io.BytesIO()
    fig.savefig(svg_buffer, format="svg", bbox_inches="tight", facecolor=fig.get_facecolor())

    col_png, col_svg = st.columns(2)
    with col_png:
        st.download_button(
            "Baixar gráfico (PNG)",
            data=png_buffer.getvalue(),
            file_name=f"{key}.png",
            mime="image/png",
            key=f"png_{key}",
        )
    with col_svg:
        st.download_button(
            "Baixar gráfico (SVG)",
            data=svg_buffer.getvalue(),
            file_name=f"{key}.svg",
            mime="image/svg+xml",
            key=f"svg_{key}",
        )


def data_download_button(data: pd.DataFrame, key: str, label: str = "Baixar dados do gráfico (CSV)") -> None:
    st.download_button(
        label,
        data=data.to_csv(index=False).encode("utf-8"),
        file_name=f"{key}.csv",
        mime="text/csv",
        key=f"csv_{key}",
    )


def render_overview(df: pd.DataFrame, stamp: str) -> None:
    st.subheader("Visão geral da coleta")
    collected_at = df["collected_at"].iloc[0] if "collected_at" in df.columns and not df.empty else "N/D"
    archived = int(df["is_archived"].sum()) if "is_archived" in df.columns else 0
    without_language = int((df["language_group"] == UNIDENTIFIED_LANGUAGE).sum()) if "language_group" in df.columns else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Repositórios (filtro atual)", len(df))
    col2.metric("Data de referência", str(collected_at)[:19].replace("T", " "))
    col3.metric("Repositórios arquivados", archived)
    col4.metric("Sem linguagem identificada", without_language)
    st.caption(f"Coleta: `{stamp}` · base: `data/processed/repos_processed_{stamp}.csv`")


def render_numeric_rq(df: pd.DataFrame, definition: dict) -> None:
    column = definition["coluna"]
    values = pd.to_numeric(df[column], errors="coerce").dropna()

    st.markdown(f"**Métrica:** {definition['descricao']}")
    if values.empty:
        st.info("Nenhum valor disponível para esta métrica com o filtro atual.")
        return

    stats = {
        "n": int(values.size),
        "mediana": float(values.median()),
        "média": float(values.mean()),
        "mínimo": float(values.min()),
        "máximo": float(values.max()),
    }
    st.dataframe(pd.DataFrame([stats]), hide_index=True, width="stretch")

    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.hist(values, bins=min(30, max(5, values.nunique())), color="#4c72b0", edgecolor="white")
    ax.set_title(f"{definition['rq']} — {definition['titulo']}")
    ax.set_xlabel(definition["titulo"])
    ax.set_ylabel("Repositórios")
    fig.tight_layout()
    st.pyplot(fig)

    key = f"{definition['rq'].lower()}_{column}"
    fig_download_buttons(fig, key)
    data_download_button(values.to_frame(name=column), key)
    plt.close(fig)


def render_categorical_rq(df: pd.DataFrame, definition: dict) -> None:
    column = definition["coluna"]
    st.markdown(f"**Métrica:** {definition['descricao']}")

    counts = df[column].value_counts()
    if counts.empty:
        st.info("Nenhum valor disponível para esta métrica com o filtro atual.")
        return

    top = counts.head(10)
    stats = pd.DataFrame({
        "linguagem": top.index,
        "repositórios": top.values,
        "percentual": (top.values / len(df) * 100).round(1),
    })
    st.dataframe(stats, hide_index=True, width="stretch")

    fig, ax = plt.subplots(figsize=(7, 3.8))
    ax.bar(top.index.astype(str), top.values, color="#55a868")
    ax.set_title(f"{definition['rq']} — {definition['titulo']} (top 10)")
    ax.set_ylabel("Repositórios")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    st.pyplot(fig)

    key = f"{definition['rq'].lower()}_{column}"
    fig_download_buttons(fig, key)
    counts_df = counts.rename("repositorios").reset_index()
    counts_df.columns = [column, "repositorios"]
    data_download_button(counts_df, key)
    plt.close(fig)


def render_rq07(consolidated_path: Path, statistics_path: Path) -> None:
    st.caption(
        "Comparação entre repositórios em linguagens populares e os demais. "
        "Esses números já vêm prontos de uma análise anterior; os filtros da "
        "barra lateral não mudam o que aparece aqui."
    )

    if not consolidated_path.exists() or not statistics_path.exists():
        st.warning(
            "Ainda não existe essa análise para a coleta selecionada. Rode o "
            "pipeline (`scripts/run_pipeline.py`) para gerá-la."
        )
        return

    statistics = pd.read_csv(statistics_path)
    group_stats = statistics[statistics["tipo"] == "grupo"]
    if group_stats.empty:
        st.info("Nenhuma estatística de grupo encontrada para esta coleta.")
        return

    for metric, label in RQ07_METRICS.items():
        metric_rows = group_stats[group_stats["metrica"] == metric]
        if metric_rows.empty:
            continue
        st.markdown(f"**{label}**")
        display = metric_rows[["grupo", "n", "media", "mediana", "q1", "q3"]].reset_index(drop=True)
        st.dataframe(display, hide_index=True, width="stretch")

        fig, ax = plt.subplots(figsize=(5, 3))
        ax.bar(display["grupo"], display["mediana"], color=["#4c72b0", "#dd8452"])
        ax.set_title(f"Mediana de {label} por grupo")
        ax.set_ylabel(label)
        fig.tight_layout()
        st.pyplot(fig)

        key = f"rq07_{metric}"
        fig_download_buttons(fig, key)
        data_download_button(display, key)
        plt.close(fig)

    correlation_stats = statistics[statistics["tipo"] == "correlacao"]
    if not correlation_stats.empty:
        st.markdown("**Repositórios mais populares têm mais dessas características?**")
        st.caption(
            "Quanto mais perto de 1 ou -1, mais forte a relação. Perto de 0 "
            "significa que não há relação. Isso mostra associação, não prova "
            "que uma coisa causa a outra."
        )
        display = correlation_stats[["metrica", "n", "pearson", "spearman"]].copy()
        display["metrica"] = display["metrica"].map(RQ07_CORRELATION_LABELS).fillna(display["metrica"])
        display = display.rename(columns={"metrica": "métrica"}).reset_index(drop=True)
        st.dataframe(display, hide_index=True, width="stretch")
        data_download_button(display, "rq07_correlacoes")


def render_outliers(outliers_path: Path) -> None:
    st.caption(
        "Repositórios com valores bem fora do padrão da amostra — muito "
        "acima ou muito abaixo da maioria."
    )

    if not outliers_path.exists():
        st.warning(
            "Ainda não existe essa análise para a coleta selecionada. Rode o "
            "pipeline (`scripts/run_pipeline.py`) para gerá-la."
        )
        return

    outliers = pd.read_csv(outliers_path)
    if outliers.empty:
        st.info("Nenhum repositório foi sinalizado como outlier nesta coleta.")
        return

    counts = outliers["descricao"].value_counts()
    st.markdown("**Sinalizações por métrica**")
    fig, ax = plt.subplots(figsize=(7, 3.8))
    ax.bar(counts.index.astype(str), counts.values, color="#c44e52")
    ax.set_ylabel("Repositórios sinalizados")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    st.pyplot(fig)
    fig_download_buttons(fig, "outliers_por_metrica")
    counts_df = counts.rename("repositorios").reset_index()
    counts_df.columns = ["descricao", "repositorios"]
    data_download_button(counts_df, "outliers_por_metrica")
    plt.close(fig)

    st.markdown("**Repositórios sinalizados**")
    metric_labels = ["Todas"] + sorted(outliers["descricao"].unique().tolist())
    metric_choice = st.selectbox("Filtrar por métrica", metric_labels, key="outlier_metric_filter")
    table = outliers if metric_choice == "Todas" else outliers[outliers["descricao"] == metric_choice]
    display = table[[
        "name_with_owner", "descricao", "valor", "lado", "severidade",
        "mediana", "primary_language", "observacao",
    ]].sort_values("valor", ascending=False)
    st.dataframe(display, hide_index=True, width="stretch")
    data_download_button(display, "outliers_detalhado", "Baixar repositórios sinalizados (CSV)")


def render_rq04_extra(df: pd.DataFrame) -> None:
    """Estatísticas complementares de RQ04 (metodologia, seção 9): período de
    desenvolvimento e quantidade de commits, ao lado do histograma principal
    de `days_since_push`. Sem gráfico adicional, para manter a aba enxuta."""
    available = {col: label for col, label in RQ04_EXTRA_METRICS.items() if col in df.columns}
    if not available:
        return

    rows = []
    for column, label in available.items():
        values = pd.to_numeric(df[column], errors="coerce").dropna()
        missing = int(df[column].isna().sum())
        if values.empty:
            continue
        rows.append({
            "métrica": label,
            "n": int(values.size),
            "mediana": float(values.median()),
            "média": round(float(values.mean()), 1),
            "mínimo": float(values.min()),
            "máximo": float(values.max()),
            "sem valor": missing,
        })

    if not rows:
        return

    st.markdown("**Métricas complementares de atividade**")
    st.caption(
        "O período de desenvolvimento é contado a partir da data de criação "
        "do repositório (a API não informa a data do primeiro commit). "
        "Repositórios sem nenhum commit ficam de fora, sem virar zero."
    )
    stats_df = pd.DataFrame(rows)
    st.dataframe(stats_df, hide_index=True, width="stretch")
    data_download_button(stats_df, "rq04_metricas_complementares")


def main() -> None:
    st.set_page_config(page_title="Lab01 — Dashboard das RQs", layout="wide")
    st.title("Dashboard das Questões de Pesquisa (RQ01–RQ07)")

    datasets = list_processed_datasets()
    if not datasets:
        st.error(
            "Nenhum CSV processado encontrado em `data/processed/`. Rode a coleta "
            "(`dotnet run --project src/collector`) e depois o pipeline "
            "(`python scripts/run_pipeline.py data/raw/repos_raw_<coleta>.csv`) "
            "antes de abrir este dashboard."
        )
        return

    labels = [stamp_for(path) for path in datasets]
    choice = st.sidebar.selectbox("Coleta (execução do pipeline)", labels, index=0)
    selected_path = datasets[labels.index(choice)]

    try:
        df = load_processed(str(selected_path))
    except Exception as exc:  # noqa: BLE001 - qualquer falha de leitura vira mensagem clara
        st.error(f"Não foi possível ler `{selected_path}`: {exc}")
        return

    st.sidebar.subheader("Filtros")
    languages = ["Todas"] + sorted(df["language_group"].dropna().unique().tolist())
    language_choice = st.sidebar.selectbox("Linguagem primária", languages)
    archived_choice = st.sidebar.selectbox(
        "Status de arquivamento", ["Todos", "Somente ativos", "Somente arquivados"]
    )

    filtered = df.copy()
    if language_choice != "Todas":
        filtered = filtered[filtered["language_group"] == language_choice]
    if archived_choice == "Somente ativos":
        filtered = filtered[~filtered["is_archived"]]
    elif archived_choice == "Somente arquivados":
        filtered = filtered[filtered["is_archived"]]

    if filtered.empty:
        st.warning("Nenhum repositório corresponde ao filtro selecionado.")
        return

    render_overview(filtered, choice)

    st.divider()
    st.header("Métricas e resultados das RQs")
    tab_labels = [definition["rq"] for definition in RQ_DEFINITIONS] + ["RQ07", "Outliers"]
    tabs = st.tabs(tab_labels)
    for tab, definition in zip(tabs, RQ_DEFINITIONS):
        with tab:
            st.subheader(f"{definition['rq']} — {definition['titulo']}")
            if definition["tipo"] == "histograma":
                render_numeric_rq(filtered, definition)
            else:
                render_categorical_rq(filtered, definition)
            if definition["rq"] == "RQ04":
                render_rq04_extra(filtered)

    with tabs[-2]:
        st.subheader("RQ07 — Linguagens populares × demais características")
        consolidated_path, statistics_path = rq07_artifacts_for(stamp_for(selected_path))
        render_rq07(consolidated_path, statistics_path)

    with tabs[-1]:
        st.subheader("Outliers (S03-04/S03-05 — atividade extra)")
        render_outliers(outliers_path_for(stamp_for(selected_path)))


if __name__ == "__main__":
    main()
