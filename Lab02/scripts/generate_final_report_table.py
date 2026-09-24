"""Gera a tabela de síntese do relatório final a partir da análise consolidada.

A tabela não recalcula estatísticas: ela apenas seleciona os valores já
produzidos por ``scripts/run_analysis.py``. Assim, o relatório, o dashboard e
o CSV estatístico usam a mesma fonte de verdade. Os valores ausentes continuam
explícitos e nunca são transformados em zero.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data/processed/statistical-results.csv"
DEFAULT_OUTPUT = ROOT / "reports/final/figures"
FIELDS = ("RQ", "Métrica", "Manual", "IA", "Comparação pareada / ressalva")


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _find(rows: list[dict[str, str]], **filters: str) -> dict[str, str]:
    matches = [row for row in rows if all(row.get(key, "") == value for key, value in filters.items())]
    if len(matches) != 1:
        description = ", ".join(f"{key}={value}" for key, value in filters.items())
        raise ValueError(f"Esperada exatamente uma linha para {description}; encontradas {len(matches)}.")
    return matches[0]


def _number(row: dict[str, str], field: str) -> float | None:
    value = row.get(field, "").strip()
    return float(value) if value else None


def _count(row: dict[str, str], field: str) -> int:
    value = _number(row, field)
    if value is None:
        raise ValueError(f"Campo obrigatório ausente: {field}.")
    return int(value)


def _format(value: float | None, digits: int = 2, *, signed: bool = False) -> str:
    if value is None:
        return "—"
    text = f"{value:.{digits}f}".replace(".", ",")
    return f"+{text}" if signed and value > 0 else text


def _summary(row: dict[str, str], *, unit: str, digits: int) -> str:
    return (
        f"{_format(_number(row, 'median'), digits)} "
        f"[{_format(_number(row, 'q1'), digits)}; {_format(_number(row, 'q3'), digits)}] "
        f"(n={_count(row, 'n_valid')}) {unit}"
    )


def _pair_counts(row: dict[str, str]) -> tuple[int, int, int]:
    return _count(row, "n_pairs"), _count(row, "n_ties"), _count(row, "n_missing")


def build_summary(input_path: Path = DEFAULT_INPUT) -> list[dict[str, str]]:
    """Retorna as linhas da tabela final, sempre em uma ordem estável."""
    rows = _read_rows(Path(input_path))

    def treatment(rq: str, metric: str, name: str) -> dict[str, str]:
        return _find(rows, rq=rq, metric=metric, row_type="treatment", treatment=name)

    def comparison(rq: str, metric: str) -> dict[str, str]:
        return _find(rows, rq=rq, metric=metric, row_type="comparison")

    rq1_manual = treatment("RQ1", "duration_seconds", "manual")
    rq1_ai = treatment("RQ1", "duration_seconds", "ai")
    rq1 = comparison("RQ1", "duration_seconds")
    rq1_pairs, _, rq1_missing = _pair_counts(rq1)

    rq2_manual = treatment("RQ2", "success_rate", "manual")
    rq2_ai = treatment("RQ2", "success_rate", "ai")
    rq2 = comparison("RQ2", "success_rate")
    rq2_pairs, rq2_ties, rq2_missing = _pair_counts(rq2)

    cc_manual = treatment("RQ3", "mean_cyclomatic_complexity", "manual")
    cc_ai = treatment("RQ3", "mean_cyclomatic_complexity", "ai")
    cc = comparison("RQ3", "mean_cyclomatic_complexity")
    cc_pairs, _, cc_missing = _pair_counts(cc)

    dup_manual = treatment("RQ3", "duplication_percentage", "manual")
    dup_ai = treatment("RQ3", "duplication_percentage", "ai")
    dup = comparison("RQ3", "duplication_percentage")
    dup_pairs, dup_ties, dup_missing = _pair_counts(dup)

    loc_manual = treatment("RQ3", "loc", "manual")
    loc_ai = treatment("RQ3", "loc", "ai")
    mi_manual = treatment("RQ3", "maintainability_index", "manual")
    mi_ai = treatment("RQ3", "maintainability_index", "ai")

    return [
        {
            "RQ": "RQ1",
            "Métrica": "Tempo até todos os testes verdes",
            "Manual": _summary(rq1_manual, unit="s", digits=0),
            "IA": _summary(rq1_ai, unit="s", digits=0),
            "Comparação pareada / ressalva": (
                f"Δ Manual−IA={_format(_number(rq1, 'difference'), 0, signed=True)} s; "
                f"p={_format(_number(rq1, 'p_value'), 4)}; "
                f"r={_format(_number(rq1, 'rank_biserial'), 2)}; "
                f"IC expl. [{_format(_number(rq1, 'ci_low'), 0)}; "
                f"{_format(_number(rq1, 'ci_high'), 0)}] s; "
                f"{rq1_pairs}/9 pares, {rq1_missing} ausente(s)."
            ),
        },
        {
            "RQ": "RQ2",
            "Métrica": "Taxa de sucesso dos testes",
            "Manual": _summary(rq2_manual, unit="%", digits=0),
            "IA": _summary(rq2_ai, unit="%", digits=0),
            "Comparação pareada / ressalva": (
                f"Δ IA−Manual={_format(_number(rq2, 'difference'), 0, signed=True)} p.p.; "
                f"{rq2_ties}/{rq2_pairs} empates; p e r indefinidos por empates totais; "
                f"IC expl. [{_format(_number(rq2, 'ci_low'), 0)}; "
                f"{_format(_number(rq2, 'ci_high'), 0)}] p.p.; "
                f"{rq2_missing} ausente(s)."
            ),
        },
        {
            "RQ": "RQ3",
            "Métrica": "Complexidade ciclomática média",
            "Manual": _summary(cc_manual, unit="pontos", digits=2),
            "IA": _summary(cc_ai, unit="pontos", digits=2),
            "Comparação pareada / ressalva": (
                f"Δ IA−Manual={_format(_number(cc, 'difference'), 2, signed=True)} pontos; "
                f"{cc_pairs}/9 pares; {cc_missing} ausente(s); "
                f"p={_format(_number(cc, 'p_value'), 4)}; "
                f"Holm={_format(_number(cc, 'p_holm'), 4)}; "
                f"r={_format(_number(cc, 'rank_biserial'), 2)}; "
                f"IC expl. [{_format(_number(cc, 'ci_low'), 0)}; "
                f"{_format(_number(cc, 'ci_high'), 0)}]."
            ),
        },
        {
            "RQ": "RQ3",
            "Métrica": "Duplicação",
            "Manual": _summary(dup_manual, unit="%", digits=2),
            "IA": _summary(dup_ai, unit="%", digits=2),
            "Comparação pareada / ressalva": (
                f"Δ IA−Manual={_format(_number(dup, 'difference'), 2, signed=True)} p.p.; "
                f"{dup_ties}/{dup_pairs} empates; {dup_missing} ausente(s); "
                "p e r indefinidos por empates totais."
            ),
        },
        {
            "RQ": "RQ3",
            "Métrica": "LOC / manutenibilidade (exploratórias)",
            "Manual": (
                f"LOC {_format(_number(loc_manual, 'median'), 2)}; "
                f"MI {_format(_number(mi_manual, 'median'), 2)} (n={_count(loc_manual, 'n_valid')})"
            ),
            "IA": (
                f"LOC {_format(_number(loc_ai, 'median'), 2)}; "
                f"MI {_format(_number(mi_ai, 'median'), 2)} (n={_count(loc_ai, 'n_valid')})"
            ),
            "Comparação pareada / ressalva": (
                "Métricas de controle/exploratórias; 4/9 pares estruturais completos; "
                "sem teste confirmatório pré-registrado."
            ),
        },
    ]


def _markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Tabela 1 — Síntese quantitativa das RQs",
        "",
        "Gerada por `scripts/generate_final_report_table.py` a partir de "
        "`data/processed/statistical-results.csv`.",
        "",
        "| " + " | ".join(FIELDS) + " |",
        "| " + " | ".join("---" for _ in FIELDS) + " |",
    ]
    lines.extend("| " + " | ".join(row[field] for field in FIELDS) + " |" for row in rows)
    lines.extend((
        "",
        "> Δ em RQ1 = Manual − IA; Δ em RQ2/RQ3 = IA − Manual. "
        "IC = intervalo de confiança bootstrap exploratório de 95%. "
        "Valores ausentes permanecem ausentes; não houve imputação.",
        "",
    ))
    return "\n".join(lines)


def write_artifacts(rows: list[dict[str, str]], output_dir: Path) -> tuple[Path, Path]:
    """Escreve versões CSV e Markdown da tabela para uso no relatório."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "tabela-resumo-rqs.csv"
    markdown_path = output_dir / "tabela-resumo-rqs.md"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    markdown_path.write_text(_markdown(rows), encoding="utf-8")
    return csv_path, markdown_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT,
                        help="CSV estatístico produzido por run_analysis.py.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT,
                        help="Diretório dos artefatos finais da tabela.")
    args = parser.parse_args(argv)
    rows = build_summary(args.input)
    csv_path, markdown_path = write_artifacts(rows, args.output_dir)
    print(f"Tabela final gerada: {csv_path} e {markdown_path}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
