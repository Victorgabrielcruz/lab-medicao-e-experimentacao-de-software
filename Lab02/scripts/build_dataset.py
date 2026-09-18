#!/usr/bin/env python3
"""Consolida os registros brutos dos trials no dataset processado do Lab02."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.processing.dataset_builder import build_dataset, write_build_result


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allocation", type=Path, default=ROOT / "data/metadata/allocation.csv")
    parser.add_argument("--raw-trials", type=Path, default=ROOT / "data/raw/trials")
    parser.add_argument("--raw-metrics", type=Path, default=ROOT / "data/raw/metrics")
    parser.add_argument("--trials", type=Path, default=ROOT / "trials")
    parser.add_argument("--output", type=Path, default=ROOT / "data/processed/trials.csv")
    parser.add_argument(
        "--errors-output",
        type=Path,
        default=ROOT / "data/processed/consolidation-errors.csv",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        result = build_dataset(
            allocation_path=args.allocation,
            raw_trials_root=args.raw_trials,
            raw_metrics_root=args.raw_metrics,
            trials_root=args.trials,
            project_root=ROOT,
        )
        write_build_result(result, args.output, args.errors_output)
    except (OSError, ValueError) as error:
        print(f"Erro ao consolidar o dataset: {error}", file=sys.stderr)
        return 2

    error_count = sum(item.severity == "error" for item in result.errors)
    warning_count = sum(item.severity == "warning" for item in result.errors)
    print(
        f"Dataset consolidado: {len(result.rows)} linhas em {args.output} "
        f"({error_count} erros, {warning_count} avisos em {args.errors_output})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
