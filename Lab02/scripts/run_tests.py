#!/usr/bin/env python3
"""Executa a suíte de aceitação de uma kata contra uma implementação.

Uso padrão — testa o código em `katas/<KATA>/src/`:

    python scripts/run_tests.py K01

Para validar a própria suíte contra a solução de referência (uso interno da
equipe, nunca durante um trial):

    python scripts/run_tests.py K01 --src reference-solutions/K01

Cada chamada roda pytest em um processo separado, isolado por kata, para que
o módulo "solution" de uma kata nunca seja confundido com o de outra. Por
isso os testes de várias katas não devem ser coletados juntos num único
comando `pytest`.

O relatório é gerado em JUnit XML (formato padrão do pytest, sem plugin
extra) e usado aqui só para extrair o total de testes, quantos passaram e
quantos falharam. O coletor de trials (S01-05) pode ler o mesmo arquivo.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPORT_DIR = ROOT / ".reports"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("kata", help="Identificador da kata, ex.: K01")
    parser.add_argument(
        "--src",
        default=None,
        help="Diretório com a implementação a testar (default: katas/<KATA>/src)",
    )
    parser.add_argument(
        "--junit-xml",
        default=None,
        help="Caminho do relatório JUnit XML (default: .reports/<KATA>_junit.xml)",
    )
    return parser.parse_args(argv)


def resumo_do_junit(caminho: Path) -> tuple[int, int, int] | None:
    """Lê total, testes passando e testes falhando do relatório JUnit XML."""
    if not caminho.exists():
        return None
    root = ET.parse(caminho).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    if suite is None:
        return None
    total = int(suite.get("tests", 0))
    falhas = int(suite.get("failures", 0)) + int(suite.get("errors", 0))
    ignorados = int(suite.get("skipped", 0))
    passando = total - falhas - ignorados
    return total, passando, falhas


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    kata_dir = ROOT / "katas" / args.kata
    tests_dir = kata_dir / "tests"
    src_dir = (Path(args.src) if args.src else kata_dir / "src").resolve()
    junit_path = (
        Path(args.junit_xml)
        if args.junit_xml
        else DEFAULT_REPORT_DIR / f"{args.kata}_junit.xml"
    )

    if not tests_dir.exists():
        print(f"Suíte de testes não encontrada: {tests_dir}", file=sys.stderr)
        return 2
    if not src_dir.exists():
        print(f"Implementação não encontrada: {src_dir}", file=sys.stderr)
        return 2

    junit_path.parent.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["KATA_SRC_DIR"] = str(src_dir)

    resultado = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(tests_dir),
            f"--junit-xml={junit_path}",
        ],
        cwd=ROOT,
        env=env,
    )

    resumo = resumo_do_junit(junit_path)
    print()
    print(f"Kata: {args.kata}")
    print(f"Implementação testada: {src_dir}")
    if resumo is not None:
        total, passando, falhando = resumo
        print(f"Total: {total} | Passando: {passando} | Falhando: {falhando}")
    else:
        print("Não foi possível ler o resumo do relatório JUnit.")
    print(f"Relatório JUnit: {junit_path}")

    return resultado.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
