#!/usr/bin/env python3
"""Verifica e opcionalmente registra o ambiente congelado da S01-08."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.environment import (
    EnvironmentValidationError,
    collect_environment,
    record_environment,
    validate_environment,
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("participant", choices=("P01", "P02", "P03"))
    parser.add_argument("--record", action="store_true", help="Grava o inventário validado")
    parser.add_argument("--replace", action="store_true", help="Substitui o registro do participante")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/metadata/environment.json",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    record = collect_environment(args.participant)
    errors = validate_environment(record)
    print(json.dumps(record, ensure_ascii=False, indent=2))
    if errors:
        print("\nAmbiente incompatível:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2
    if args.record:
        try:
            registry = record_environment(args.output, record, replace=args.replace)
        except EnvironmentValidationError as error:
            print(f"Erro: {error}", file=sys.stderr)
            return 2
        print(f"Inventário registrado em {args.output}; estado: {registry['status']}")
    else:
        print("Ambiente compatível. Use --record para preservar a evidência.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
