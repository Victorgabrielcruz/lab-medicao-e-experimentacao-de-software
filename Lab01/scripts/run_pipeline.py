"""Pipeline único de execução pós-coleta do Lab01 (task S03-06).

Orquestra, em um único comando, os scripts Python já existentes do projeto,
na mesma ordem descrita em `docs/tutorial-execucao.md`:

    1. src/analysis/build_processed_dataset.py   -> dataset processado (RQ01-06)
    2. src/metrics/rq01_rq02_validation.py        -> validação RQ01/RQ02
       src/metrics/rq03_rq04_validation.py        -> validação RQ03/RQ04
       src/metrics/rq05_rq06_validation.py        -> validação RQ05/RQ06
    3. src/analysis/consolidate_rq07_dataset.py   -> dataset consolidado da RQ07
       src/analysis/rq07_analysis.py              -> análise da RQ07
       src/analysis/rq07_validation.py            -> validação da RQ07

Este orquestrador NÃO substitui nem recalcula nenhuma métrica: cada etapa é
executada como subprocesso, exatamente como documentado, e nenhuma regra de
processamento ou validação é reimplementada aqui.

A coleta (`dotnet run --project src/collector`) não faz parte deste pipeline:
é um passo manual, anterior e em C#/.NET, fora do escopo deste script Python
(ver docs/tasks.md, task S03-06). A entrada obrigatória é um CSV bruto já
coletado (`data/raw/repos_raw_<coleta>.csv`).

Uso:
    python scripts/run_pipeline.py data/raw/repos_raw_<coleta>.csv

A etapa de RQ07 (consolidação + análise + validação) roda sempre, no mesmo pé
de igualdade das demais RQs: `rq07_validation.py` valida `rq07_analysis.py`
exatamente como `rq01_rq02_validation.py`, `rq03_rq04_validation.py` e
`rq05_rq06_validation.py` já validam suas respectivas RQs, então esta etapa
não depende mais de nenhuma outra task para ser considerada concluída.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "src" / "analysis"
METRICS_DIR = ROOT / "src" / "metrics"

# Etapas de validação RQ01-06, na ordem em que devem rodar.
VALIDATION_STEPS = (
    ("validação RQ01/RQ02", METRICS_DIR / "rq01_rq02_validation.py"),
    ("validação RQ03/RQ04", METRICS_DIR / "rq03_rq04_validation.py"),
    ("validação RQ05/RQ06", METRICS_DIR / "rq05_rq06_validation.py"),
)

_ARTIFACT_LINE = re.compile(r"\.(csv|md|svg|json)\s*$")


class PipelineError(RuntimeError):
    """Erro em uma etapa do pipeline, guardando a etapa e o motivo da falha."""

    def __init__(self, step: str, reason: str) -> None:
        super().__init__(f"[{step}] {reason}")
        self.step = step
        self.reason = reason


def _validate_raw_csv(source: Path) -> None:
    """Confere que o CSV bruto informado existe e é legível antes de iniciar.

    Não é responsabilidade deste script rodar a coleta: se o arquivo não
    existir, a mensagem orienta a rodar `dotnet run --project src/collector`
    antes, sem tentar executá-lo automaticamente.
    """
    if not source.exists():
        raise PipelineError(
            "entrada",
            f"CSV bruto não encontrado: {source}. Rode a coleta antes "
            "(dotnet run --project src/collector) e informe o CSV gerado em "
            "data/raw/.",
        )
    if not source.is_file():
        raise PipelineError("entrada", f"Caminho informado não é um arquivo: {source}")
    try:
        with source.open("r", encoding="utf-8") as handle:
            header = handle.readline()
    except (OSError, UnicodeDecodeError) as exc:
        raise PipelineError("entrada", f"CSV bruto ilegível: {exc}") from exc
    if not header.strip():
        raise PipelineError("entrada", f"CSV bruto vazio ou sem cabeçalho: {source}")


def _run_step(step: str, script: Path, args: list[str]) -> str:
    """Executa uma etapa como subprocesso e devolve o stdout, se bem-sucedida.

    Interrompe o pipeline (PipelineError) assim que a etapa retornar código de
    saída diferente de zero — o que já acontece nos scripts de validação
    quando encontram inconsistência crítica, por exemplo.
    """
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    process = subprocess.run(
        [sys.executable, str(script), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    if process.stdout:
        print(process.stdout, end="" if process.stdout.endswith("\n") else "\n")
    if process.returncode != 0:
        reason = (
            process.stderr.strip()
            or process.stdout.strip()
            or f"código de saída {process.returncode}"
        )
        raise PipelineError(step, reason)
    return process.stdout


def _extract_path(step: str, stdout: str, label: str) -> Path:
    """Extrai o caminho impresso por uma etapa no formato 'Label: caminho'."""
    match = re.search(rf"^{re.escape(label)}:\s*(.+)$", stdout, flags=re.MULTILINE)
    if not match:
        raise PipelineError(
            step, f"não foi possível localizar a saída '{label}' no log da etapa."
        )
    return Path(match.group(1).strip())


def _collect_artifact_lines(stdout: str) -> list[str]:
    """Seleciona, do stdout de uma etapa, as linhas que apontam para artefatos."""
    return [
        line.strip() for line in stdout.splitlines() if _ARTIFACT_LINE.search(line.strip())
    ]


def run(source: Path) -> list[str]:
    """Executa o fluxo pós-coleta completo e devolve as linhas de artefatos gerados.

    Levanta PipelineError com a etapa e o motivo assim que qualquer passo falha.
    """
    artifacts: list[str] = []
    _validate_raw_csv(source)

    # 1. Dataset processado (RQ01-06)
    step = "processamento (build_processed_dataset)"
    stdout = _run_step(step, ANALYSIS_DIR / "build_processed_dataset.py", [str(source)])
    processed = _extract_path(step, stdout, "Saída")
    artifacts += _collect_artifact_lines(stdout)

    # 2. Validações RQ01-06. Cada script já retorna código de saída 1 quando
    # encontra inconsistência crítica (`result.passed` falso); isso já basta
    # para interromper o pipeline em _run_step, sem regra adicional aqui.
    for step, script in VALIDATION_STEPS:
        stdout = _run_step(step, script, [str(source), str(processed)])
        artifacts += _collect_artifact_lines(stdout)

    # 3. Consolidação, análise e validação da RQ07 — mesmo padrão das RQs
    # 01-06: cada etapa roda incondicionalmente e uma inconsistência crítica
    # na validação interrompe o pipeline, como nas demais validações.
    step = "consolidação RQ07 (consolidate_rq07_dataset)"
    stdout = _run_step(step, ANALYSIS_DIR / "consolidate_rq07_dataset.py", [str(processed)])
    consolidated = _extract_path(step, stdout, "Dataset consolidado")
    artifacts += _collect_artifact_lines(stdout)

    step = "análise RQ07 (rq07_analysis)"
    stdout = _run_step(step, ANALYSIS_DIR / "rq07_analysis.py", [str(consolidated)])
    statistics = _extract_path(step, stdout, "statistics")
    artifacts += _collect_artifact_lines(stdout)

    step = "validação RQ07 (rq07_validation)"
    stdout = _run_step(step, ANALYSIS_DIR / "rq07_validation.py", [str(consolidated), str(statistics)])
    artifacts += _collect_artifact_lines(stdout)

    return artifacts


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Executa, a partir de um CSV bruto já coletado, o processamento, as "
            "validações de RQ01-06 e a análise da RQ07 em um único comando. "
            "A coleta (dotnet run --project src/collector) é um passo manual "
            "anterior, fora do escopo deste script."
        )
    )
    parser.add_argument(
        "raw_csv",
        type=Path,
        help="CSV bruto já coletado (ex.: data/raw/repos_raw_<coleta>.csv)",
    )
    args = parser.parse_args()

    try:
        artifacts = run(args.raw_csv)
    except PipelineError as exc:
        print(f"\nPipeline interrompido na etapa: {exc.step}")
        print(f"Motivo: {exc.reason}")
        raise SystemExit(1) from exc

    print("\nPipeline concluído com sucesso.")
    print("Artefatos gerados:")
    for line in artifacts:
        print(f"- {line}")


if __name__ == "__main__":
    main()
