"""Gera o dashboard e exporta figuras/dados a partir do dataset oficial validado."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.dashboard.figures import generate  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/processed/trials.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "reports/figures/dashboard")
    args = parser.parse_args(argv)
    figures = generate(args.dataset, args.output)
    print(f"Dashboard gerado em {args.output}: {len(figures)} figuras, index.html e dois CSVs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
