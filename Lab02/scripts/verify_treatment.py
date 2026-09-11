#!/usr/bin/env python3
"""Verifica o controle de IA e grava evidência antes de um trial."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.environment import (
    EnvironmentValidationError,
    EXPECTED_VERSIONS,
    extract_version,
    parse_extensions,
    run_command,
    running_process_names,
    validate_treatment,
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("treatment", choices=("ai", "manual"))
    parser.add_argument("--trial-dir", type=Path, required=True)
    parser.add_argument("--confirm-manual-no-ai", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    trial_dir = args.trial_dir.resolve()
    config_path = trial_dir / "trial-config.json"
    if not config_path.is_file():
        print(f"Erro: configuração do trial ausente: {config_path}", file=sys.stderr)
        return 2
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("treatment") != args.treatment:
        print("Erro: tratamento informado diverge de trial-config.json", file=sys.stderr)
        return 2
    evidence_path = trial_dir / "treatment-verification.json"
    if evidence_path.exists():
        print(f"Erro: evidência existente não será sobrescrita: {evidence_path}", file=sys.stderr)
        return 2
    try:
        extension_records = parse_extensions(
            run_command(["code", "--list-extensions", "--show-versions"])
        )
        extensions = [item["id"] for item in extension_records]
        processes = sorted(running_process_names())
        try:
            codex_output = run_command(["codex", "--version"])
            codex_version = extract_version(codex_output)
        except EnvironmentValidationError:
            codex_version = None
    except EnvironmentValidationError as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 2

    errors = validate_treatment(
        args.treatment,
        extensions=extensions,
        processes=processes,
        codex_version=codex_version,
        manual_confirmation=args.confirm_manual_no_ai,
    )
    evidence = {
        "schema_version": 1,
        "trial_id": config["trial_id"],
        "treatment": args.treatment,
        "verified_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "vscode_extensions": extension_records,
        "codex_expected_version": EXPECTED_VERSIONS["codex"],
        "codex_detected_version": codex_version,
        "codex_process_running": any(name.startswith("codex") for name in processes),
        "manual_confirmation": args.confirm_manual_no_ai,
        "errors": errors,
        "status": "passed" if not errors else "failed",
    }
    if errors:
        print("Tratamento incompatível:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2
    evidence_path.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Tratamento verificado: {evidence_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
