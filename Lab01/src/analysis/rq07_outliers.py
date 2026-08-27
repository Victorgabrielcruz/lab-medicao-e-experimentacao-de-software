"""Identifica outliers nas métricas do Lab01 (atividade extra da Sprint 3).

Uso:
    python src/analysis/rq07_outliers.py data/processed/repos_rq07_consolidated_<coleta>.csv

Sem argumento, usa o consolidado mais recente em data/processed/.

O script não altera a base original. Ele grava um CSV com os repositórios
sinalizados e um relatório em markdown com o método e os limites usados.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "reports" / "drafts"

# Multiplicadores das cercas de Tukey. 1.5 é a convenção para outlier
# moderado e 3.0 para extremo.
MODERATE = 1.5
EXTREME = 3.0

# Desvios padrão para o método alternativo, usado só como comparação.
ZSCORE_THRESHOLD = 3.0

# Métricas quantitativas pedidas na task, na ordem em que entram no relatório.
METRICS = {
    "age_years": "idade em anos",
    "accepted_pull_requests": "pull requests aceitas",
    "releases_count": "releases",
    "days_since_push": "dias desde o último push",
    "closed_issues_percentage": "percentual de issues fechadas",
    "stargazer_count": "estrelas",
}

IDENTITY_COLUMNS = ["name_with_owner", "url", "primary_language"]


@dataclass
class MetricFences:
    """Limites de uma métrica, calculados pelo IQR."""

    column: str
    label: str
    count: int
    missing: int
    q1: float
    median: float
    q3: float
    iqr: float
    lower: float
    upper: float
    lower_extreme: float
    upper_extreme: float
    below: int
    above: int
    zscore_flagged: int
    skew: float


@dataclass
class MetricProfile:
    """Como o grupo sinalizado se compara ao resto da amostra."""

    column: str
    label: str
    flagged: int
    median_flagged: float
    median_rest: float
    without_language: float
    without_language_sample: float
    archived: int
    zero_releases: float
    zero_releases_sample: float


@dataclass
class OutlierResult:
    fences: list[MetricFences]
    outliers: pd.DataFrame
    total_rows: int
    profiles: list[MetricProfile]
    overlap: pd.Series
    multi_metric: pd.DataFrame


def latest_consolidated_csv() -> Path:
    """Consolidado da RQ07 mais recente; se não houver, o processado."""
    for pattern in ("repos_rq07_consolidated_*.csv", "repos_processed_*.csv"):
        files = sorted(PROCESSED_DIR.glob(pattern))

        if files:
            return files[-1]

    raise SystemExit(
        f"nenhum repos_rq07_consolidated_*.csv ou repos_processed_*.csv em {PROCESSED_DIR}"
    )


def load(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"arquivo nao encontrado: {path}")

    df = pd.read_csv(path)

    faltando = [c for c in list(METRICS) + IDENTITY_COLUMNS if c not in df.columns]

    if faltando:
        raise SystemExit(f"colunas ausentes na base: {faltando}")

    return df


def fences_for(df: pd.DataFrame, column: str, label: str) -> MetricFences:
    valores = pd.to_numeric(df[column], errors="coerce")
    validos = valores.dropna()

    q1 = float(validos.quantile(0.25))
    q3 = float(validos.quantile(0.75))
    iqr = q3 - q1

    media = float(validos.mean())
    desvio = float(validos.std())

    # Desvio zero acontece quando a métrica é constante: nesse caso nenhum
    # ponto se afasta e o z-score não sinaliza nada.
    if desvio > 0:
        zscore_flagged = int((((validos - media) / desvio).abs() > ZSCORE_THRESHOLD).sum())
    else:
        zscore_flagged = 0

    lower = q1 - MODERATE * iqr
    upper = q3 + MODERATE * iqr

    return MetricFences(
        column=column,
        label=label,
        count=int(validos.size),
        missing=int(valores.isna().sum()),
        q1=q1,
        median=float(validos.median()),
        q3=q3,
        iqr=iqr,
        lower=lower,
        upper=upper,
        lower_extreme=q1 - EXTREME * iqr,
        upper_extreme=q3 + EXTREME * iqr,
        below=int((validos < lower).sum()),
        above=int((validos > upper).sum()),
        zscore_flagged=zscore_flagged,
        skew=float(validos.skew()),
    )


def outliers_for(df: pd.DataFrame, fences: MetricFences) -> pd.DataFrame:
    """Uma linha por repositório sinalizado na métrica."""
    valores = pd.to_numeric(df[fences.column], errors="coerce")

    abaixo = valores < fences.lower
    acima = valores > fences.upper
    marcados = df.loc[abaixo | acima, IDENTITY_COLUMNS].copy()

    if marcados.empty:
        return pd.DataFrame(columns=IDENTITY_COLUMNS + [
            "metrica", "descricao", "valor", "lado", "severidade",
            "limite_inferior", "limite_superior", "mediana", "observacao",
        ])

    selecionados = valores.loc[marcados.index]

    marcados["metrica"] = fences.column
    marcados["descricao"] = fences.label
    marcados["valor"] = selecionados
    marcados["lado"] = ["abaixo" if v < fences.lower else "acima" for v in selecionados]
    marcados["severidade"] = [
        "extremo"
        if v < fences.lower_extreme or v > fences.upper_extreme
        else "moderado"
        for v in selecionados
    ]
    marcados["limite_inferior"] = fences.lower
    marcados["limite_superior"] = fences.upper
    marcados["mediana"] = fences.median
    marcados["observacao"] = observacao_for(df, fences, marcados.index)

    return marcados.sort_values("valor", ascending=False)


def observacao_for(df: pd.DataFrame, fences: MetricFences, index) -> list[str]:
    """Ressalvas de medição que afetam a leitura do valor extremo."""
    if fences.column != "releases_count" or "releases_no_teto" not in df.columns:
        return [""] * len(index)

    no_teto = df.loc[index, "releases_no_teto"]

    return ["valor truncado pela API" if bool(v) else "" for v in no_teto]


def profile_for(df: pd.DataFrame, fences: MetricFences, nomes: set[str]) -> MetricProfile:
    """Compara o grupo sinalizado com o restante da amostra."""
    dentro = df[df["name_with_owner"].isin(nomes)]
    fora = df[~df["name_with_owner"].isin(nomes)]

    sem_linguagem = float(dentro["primary_language"].isna().mean()) if len(dentro) else 0.0
    arquivados = int(dentro["is_archived"].sum()) if "is_archived" in dentro else 0

    def zero_releases(frame: pd.DataFrame) -> float:
        if "releases_count" not in frame or frame.empty:
            return 0.0

        return float((frame["releases_count"] == 0).mean())

    return MetricProfile(
        column=fences.column,
        label=fences.label,
        flagged=len(dentro),
        median_flagged=float(dentro[fences.column].median()) if len(dentro) else float("nan"),
        median_rest=float(fora[fences.column].median()) if len(fora) else float("nan"),
        without_language=sem_linguagem,
        without_language_sample=float(df["primary_language"].isna().mean()),
        archived=arquivados,
        zero_releases=zero_releases(dentro),
        zero_releases_sample=zero_releases(df),
    )


def overlap_for(outliers: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    """Quantas metricas sinalizam cada repositorio, e quem repete mais."""
    if outliers.empty:
        return pd.Series(dtype=int), pd.DataFrame(columns=["name_with_owner", "metricas", "quais"])

    por_repo = outliers.groupby("name_with_owner")["metrica"]

    contagem = por_repo.size()
    resumo = contagem.value_counts().sort_index()

    multi = pd.DataFrame(
        {
            "name_with_owner": contagem.index,
            "metricas": contagem.values,
            "quais": por_repo.apply(lambda s: ", ".join(sorted(s))).values,
        }
    )
    multi = multi[multi["metricas"] >= 2].sort_values("metricas", ascending=False)

    return resumo, multi.reset_index(drop=True)


def analyze(df: pd.DataFrame) -> OutlierResult:
    fences = [fences_for(df, coluna, rotulo) for coluna, rotulo in METRICS.items()]
    partes = [outliers_for(df, f) for f in fences]
    preenchidas = [parte for parte in partes if not parte.empty]

    outliers = (
        pd.concat(preenchidas, ignore_index=True)
        if preenchidas
        else partes[0] if partes else pd.DataFrame()
    )

    nomes_por_metrica = {
        f.column: set(outliers.loc[outliers["metrica"] == f.column, "name_with_owner"])
        if not outliers.empty
        else set()
        for f in fences
    }

    profiles = [profile_for(df, f, nomes_por_metrica[f.column]) for f in fences]
    resumo, multi = overlap_for(outliers)

    return OutlierResult(
        fences=fences,
        outliers=outliers,
        total_rows=len(df),
        profiles=profiles,
        overlap=resumo,
        multi_metric=multi,
    )


def output_for(source: Path, prefixo: str, extensao: str) -> Path:
    marca = source.stem.split("_")[-1]
    pasta = PROCESSED_DIR if extensao == "csv" else REPORTS_DIR

    return pasta / f"{prefixo}_{marca}.{extensao}"


def save_outliers(result: OutlierResult, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    result.outliers.to_csv(output, index=False)

    return output


def caminho_relativo(path: Path) -> str:
    """Caminho a partir da raiz do projeto, ou o nome se estiver fora dela."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return path.name


def build_report(result: OutlierResult, source: Path, csv_output: Path) -> str:
    linhas = [
        "# Outliers das métricas do Lab01",
        "",
        f"Base analisada: `{source.name}`, com {result.total_rows} repositórios.",
        f"Saída detalhada: `{caminho_relativo(csv_output)}`.",
        "",
        "Atividade extra da Sprint 3. Não altera a base original e nenhum",
        "repositório é removido do dataset principal.",
        "",
        "## Método",
        "",
        "Regra do intervalo interquartil (cercas de Tukey). Um repositório é",
        "sinalizado quando o valor da métrica fica fora de:",
        "",
        "```",
        "[ Q1 - 1.5 x IQR ,  Q3 + 1.5 x IQR ]      moderado",
        "[ Q1 - 3.0 x IQR ,  Q3 + 3.0 x IQR ]      extremo",
        "```",
        "",
        "O IQR foi escolhido no lugar do z-score porque quase todas as métricas",
        "são fortemente assimétricas. Média e desvio padrão são puxados pelos",
        "próprios valores extremos, o que faz o z-score sinalizar menos casos",
        "justamente onde a cauda é mais longa. A coluna de comparação abaixo",
        "mostra essa diferença.",
        "",
        "Valores ausentes são ignorados no cálculo dos quartis, não contam como",
        "outlier e aparecem na coluna de vazios.",
        "",
        "## Limites por métrica",
        "",
        "| métrica | Q1 | mediana | Q3 | IQR | limite inferior | limite superior | vazios |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for f in result.fences:
        linhas.append(
            f"| {f.label} | {f.q1:.1f} | {f.median:.1f} | {f.q3:.1f} | {f.iqr:.1f} "
            f"| {f.lower:.1f} | {f.upper:.1f} | {f.missing} |"
        )

    linhas += [
        "",
        "## Quantidade sinalizada e comparação entre métodos",
        "",
        "| métrica | assimetria | abaixo | acima | total IQR | z-score |",
        "|---|---|---|---|---|---|",
    ]

    for f in result.fences:
        linhas.append(
            f"| {f.label} | {f.skew:.2f} | {f.below} | {f.above} "
            f"| {f.below + f.above} | {f.zscore_flagged} |"
        )

    linhas += [
        "",
        "## Comparação com o comportamento geral da amostra",
        "",
        "| métrica | sinalizados | mediana do grupo | mediana do resto | sem linguagem | arquivados |",
        "|---|---|---|---|---|---|",
    ]

    for p in result.profiles:
        if p.flagged == 0:
            linhas.append(f"| {p.label} | 0 | | | | |")
            continue

        linhas.append(
            f"| {p.label} | {p.flagged} | {p.median_flagged:.1f} | {p.median_rest:.1f} "
            f"| {p.without_language:.0%} (amostra {p.without_language_sample:.0%}) | {p.archived} |"
        )

    linhas += [
        "",
        "## Repositórios sinalizados em mais de uma métrica",
        "",
    ]

    if result.overlap.empty:
        linhas += ["Nenhum.", ""]
    else:
        linhas += ["| métricas simultâneas | repositórios |", "|---|---|"]

        for quantidade, repos in result.overlap.items():
            linhas.append(f"| {quantidade} | {repos} |")

        if not result.multi_metric.empty:
            linhas += [
                "",
                "| repositório | métricas | quais |",
                "|---|---|---|",
            ]

            for _, linha in result.multi_metric.head(15).iterrows():
                linhas.append(
                    f"| {linha['name_with_owner']} | {linha['metricas']} | {linha['quais']} |"
                )

        linhas.append("")

    linhas += ["## Repositórios sinalizados por métrica", ""]

    for f in result.fences:
        marcados = result.outliers[result.outliers["metrica"] == f.column]

        linhas += [f"### {f.label}", ""]

        if marcados.empty:
            linhas += ["Nenhum repositório fora das cercas.", ""]
            continue

        extremos = int((marcados["severidade"] == "extremo").sum())

        linhas += [
            f"{len(marcados)} repositórios sinalizados, {extremos} deles extremos.",
            "",
            "| repositório | valor | lado | severidade | linguagem | observação |",
            "|---|---|---|---|---|---|",
        ]

        for _, linha in marcados.head(10).iterrows():
            linguagem = linha["primary_language"]
            linguagem = "" if pd.isna(linguagem) else linguagem

            linhas.append(
                f"| {linha['name_with_owner']} | {linha['valor']:.1f} | {linha['lado']} "
                f"| {linha['severidade']} | {linguagem} | {linha['observacao']} |"
            )

        if len(marcados) > 10:
            linhas.append(f"| ... | | | | | mais {len(marcados) - 10} repositórios no CSV |")

        linhas.append("")

    linhas += [
        "## Ressalvas de leitura",
        "",
        "`releases_count` é truncado em 1000 pela API. Repositórios no teto",
        "aparecem marcados na coluna de observação e o valor real deles é",
        "desconhecido, então a posição na cauda é um piso.",
        "",
        "`closed_issues_percentage` é limitado a 100 por construção, então só",
        "existe outlier na ponta de baixo. Repositórios sem issues ficam vazios",
        "e não entram na conta.",
        "",
        "`days_since_push` tem mediana de 1 dia, então a cauda são justamente os",
        "projetos parados. Nessa métrica o outlier é o repositório abandonado, e",
        "não o mais ativo.",
        "",
    ]

    return "\n".join(linhas)


def save_report(conteudo: str, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(conteudo, encoding="utf-8")

    return output


def run(source: Path) -> tuple[OutlierResult, Path, Path]:
    df = load(source)
    result = analyze(df)

    csv_output = save_outliers(result, output_for(source, "outliers", "csv"))
    md_output = save_report(
        build_report(result, source, csv_output),
        output_for(source, "outliers", "md"),
    )

    return result, csv_output, md_output


def main() -> None:
    parser = argparse.ArgumentParser(description="Identifica outliers nas métricas do Lab01.")
    parser.add_argument("source", nargs="?", type=Path, help="CSV consolidado da RQ07")
    args = parser.parse_args()

    source = args.source or latest_consolidated_csv()
    print(f"Entrada: {source}\n")

    result, csv_output, md_output = run(source)

    print(f"{'metrica':<32}{'abaixo':>8}{'acima':>8}{'z-score':>10}")
    print("-" * 58)

    for f in result.fences:
        print(f"{f.label:<32}{f.below:>8}{f.above:>8}{f.zscore_flagged:>10}")

    print(f"\n{len(result.outliers)} sinalizacoes em {result.total_rows} repositorios")
    print(f"csv: {csv_output}")
    print(f"relatorio: {md_output}")


if __name__ == "__main__":
    main()
