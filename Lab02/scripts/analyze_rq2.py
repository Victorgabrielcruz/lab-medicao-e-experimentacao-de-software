#!/usr/bin/env python3
"""Executa a análise de RQ2 (defeitos e taxa de sucesso) sobre o dataset validado."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.analysis import DatasetNotAuthorizedError, load_validated_dataset
from src.analysis.rq2_defects import analyze, render_figures, render_report_markdown


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/processed/trials.csv")
    parser.add_argument("--report", type=Path, default=ROOT / "reports/drafts/rq2-analysis.md")
    parser.add_argument("--figures", type=Path, default=ROOT / "reports/figures/rq2")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        rows = load_validated_dataset(args.dataset)
    except DatasetNotAuthorizedError as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 2

    result = analyze(rows)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report_markdown(result), encoding="utf-8")
    figures = render_figures(result, args.figures)

    print(f"RQ2: relatório em {args.report}, {len(figures)} figura(s) em {args.figures}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
