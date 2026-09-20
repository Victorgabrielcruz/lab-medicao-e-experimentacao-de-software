#!/usr/bin/env python3
"""Valida o dataset oficial do Lab02 e gera o relatório da Seção 13."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.validation import load_dataset_csv, render_report_markdown, validate_dataset


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/processed/trials.csv")
    parser.add_argument("--allocation", type=Path, default=ROOT / "data/metadata/allocation.csv")
    parser.add_argument("--raw-trials", type=Path, default=ROOT / "data/raw/trials")
    parser.add_argument("--raw-metrics", type=Path, default=ROOT / "data/raw/metrics")
    parser.add_argument("--trials", type=Path, default=ROOT / "trials")
    parser.add_argument("--katas", type=Path, default=ROOT / "katas")
    parser.add_argument("--report", type=Path, default=ROOT / "reports/drafts/data-validation.md")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        rows = load_dataset_csv(args.dataset)
    except (OSError, csv.Error) as error:
        print(f"Erro ao ler o dataset: {error}", file=sys.stderr)
        return 2

    result = validate_dataset(
        rows,
        allocation_path=args.allocation,
        raw_trials_root=args.raw_trials,
        raw_metrics_root=args.raw_metrics,
        trials_root=args.trials,
        katas_root=args.katas,
        project_root=ROOT,
    )

    report = render_report_markdown(result, dataset_path=args.dataset.relative_to(ROOT))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report, encoding="utf-8")

    print(
        f"Validação concluída: {result.row_count} linhas, "
        f"{len(result.critical)} erro(s) crítico(s), {len(result.warnings)} aviso(s), "
        f"{len(result.infos)} observação(ões). Relatório em {args.report}."
    )
    if not result.authorized:
        print("Dataset NÃO autorizado para as análises de RQ1-RQ3.", file=sys.stderr)
        return 2
    print("Dataset autorizado para as análises de RQ1-RQ3.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
