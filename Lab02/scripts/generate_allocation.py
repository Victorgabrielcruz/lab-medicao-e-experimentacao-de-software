#!/usr/bin/env python3
"""Gera, congela ou valida a alocação contrabalanceada do experimento."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.collection.allocation import (
    DEFAULT_SEED,
    AllocationError,
    freeze_allocation,
    generate_allocation,
    read_allocation,
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "data/metadata/allocation.csv"
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=ROOT / "data/metadata/allocation-metadata.json",
    )
    parser.add_argument(
        "--check", action="store_true", help="Apenas valida a alocação congelada"
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        if args.check:
            rows = read_allocation(args.output)
            expected = generate_allocation(args.seed)
            if rows != expected:
                raise AllocationError("O CSV não corresponde à semente informada")
            print(f"Alocação válida: {len(rows)} trials, semente {args.seed}")
            return 0
        created = freeze_allocation(
            generate_allocation(args.seed), args.output, args.metadata, args.seed
        )
    except (AllocationError, OSError, ValueError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 2
    action = "congelada" if created else "já estava congelada e foi confirmada"
    print(f"Alocação {action}: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
