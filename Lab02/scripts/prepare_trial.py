#!/usr/bin/env python3
"""Cria ou restaura um diretório limpo conforme a alocação congelada."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.collection.allocation import AllocationError
from src.collection.trial_preparation import TrialPreparationError, prepare_trial


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("participant", choices=("P01", "P02", "P03"))
    parser.add_argument("kata", choices=tuple(f"K{i:02d}" for i in range(1, 7)))
    parser.add_argument("treatment", choices=("ai", "manual"))
    parser.add_argument(
        "--restore",
        action="store_true",
        help="Descarta alterações locais e restaura o esqueleto; proibido após a coleta",
    )
    parser.add_argument("--trials-root", type=Path, default=ROOT / "trials")
    parser.add_argument("--raw-root", type=Path, default=ROOT / "data/raw/trials")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        path = prepare_trial(
            args.participant,
            args.kata,
            args.treatment,
            trials_root=args.trials_root,
            raw_root=args.raw_root,
            restore=args.restore,
        )
    except (TrialPreparationError, AllocationError, OSError, ValueError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 2
    print(f"Trial preparado: {path}")
    print(f"Próximo passo: verificar o tratamento {args.treatment!r} antes de iniciar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
