#!/usr/bin/env python3
"""Executa e registra um trial cronometrado (S01-05).

Roda a suíte de aceitação de uma kata em segundo plano até todos os testes
passarem ou até o limite de 35 minutos (2.100 segundos), o que ocorrer
primeiro, e grava o resultado em `data/raw/trials/<trial_id>/`.

Uso padrão — cronometra `katas/<KATA>/src/` contra `katas/<KATA>/tests/`:

    python scripts/run_trial.py P01 K01 ai

`treatment` deve ser `ai` ou `manual`, conforme o protocolo. O `trial_id` é
composto automaticamente como `<participante>-<kata>-<tratamento>`.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.collection import TIME_LIMIT_SECONDS, TrialCollectionError, collect_trial
from src.collection.trial_collector import DEFAULT_POLL_INTERVAL_SECONDS


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("participant", help="Identificador anonimizado, ex.: P01")
    parser.add_argument("kata", help="Identificador da kata, ex.: K01")
    parser.add_argument("treatment", choices=sorted(("ai", "manual")), help="Tratamento do trial")
    parser.add_argument(
        "--src",
        type=Path,
        default=None,
        help="Diretório com a implementação a cronometrar (default: katas/<KATA>/src)",
    )
    parser.add_argument(
        "--tests",
        type=Path,
        default=None,
        help="Diretório com a suíte de aceitação (default: katas/<KATA>/tests)",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "data" / "raw" / "trials",
        help="Raiz das saídas brutas do trial",
    )
    parser.add_argument(
        "--time-limit-seconds",
        type=int,
        default=TIME_LIMIT_SECONDS,
        help="Limite de encerramento do cronômetro (default: 2100s / 35 min)",
    )
    parser.add_argument(
        "--poll-interval-seconds",
        type=float,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help="Intervalo entre checagens da suíte enquanto o trial está em andamento",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    kata_dir = ROOT / "katas" / args.kata
    tests_dir = args.tests or kata_dir / "tests"
    src_dir = args.src or kata_dir / "src"

    print(f"Trial: {args.participant} / {args.kata} / {args.treatment}")
    print(
        f"Cronômetro iniciado. Limite: {args.time_limit_seconds}s "
        f"(~{args.time_limit_seconds / 60:.0f} min). Checando a cada {args.poll_interval_seconds}s."
    )

    try:
        trial_path = collect_trial(
            args.participant,
            args.kata,
            args.treatment,
            tests_dir,
            src_dir,
            output_root=args.output_root,
            time_limit_seconds=args.time_limit_seconds,
            poll_interval_seconds=args.poll_interval_seconds,
        )
    except TrialCollectionError as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 2

    print(f"Trial registrado em: {trial_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
