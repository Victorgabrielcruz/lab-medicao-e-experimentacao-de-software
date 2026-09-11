#!/usr/bin/env python3
"""Coleta as métricas estáticas do código de produção de um trial."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.metrics.static_metrics import MetricsCollectionError, collect_static_metrics


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trial_id", help="Identificador único do trial")
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Diretório de produção (padrão: trials/<trial_id>/src)",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "data" / "raw" / "metrics",
        help="Raiz das saídas brutas",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    source = args.source or ROOT / "trials" / args.trial_id / "src"
    try:
        result = collect_static_metrics(args.trial_id, source, args.output_root)
    except MetricsCollectionError as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 2
    print(f"Métricas consolidadas: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
