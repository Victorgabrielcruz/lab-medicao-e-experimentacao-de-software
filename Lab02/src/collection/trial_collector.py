"""Cronômetro e coletor padronizado de trials (RQ1/RQ2).

O cronômetro roda a suíte de aceitação de uma kata em segundo plano, em
intervalos regulares, até o primeiro momento em que todos os testes passarem
ou até o limite de 35 minutos (2.100 segundos) ser atingido — os dois
critérios de encerramento definidos em `methodology.md`, Seção 10.4. O
participante continua editando e rodando os próprios testes livremente; o
coletor apenas observa o resultado da suíte e não interfere no código.

O módulo separa duas camadas, no mesmo espírito de `src/metrics/static_metrics.py`:

- `run_trial`: lógica pura do cronômetro (sem I/O real), testável com
  relógios e suítes falsos;
- `collect_trial`: orquestração real — executa pytest via subprocesso, grava
  o relatório JUnit e o registro consolidado do trial em
  `data/raw/trials/<trial_id>/`.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, NamedTuple

ROOT = Path(__file__).resolve().parents[2]

TIME_LIMIT_SECONDS = 2100
DEFAULT_POLL_INTERVAL_SECONDS = 5.0
DEFAULT_OUTPUT_ROOT = ROOT / "data" / "raw" / "trials"
VALID_TREATMENTS = {"ai", "manual"}
TRIAL_ID_SEPARATOR = "-"


class TrialCollectionError(RuntimeError):
    """Erro controlado de cronometragem, execução da suíte ou registro do trial."""


class SuiteResult(NamedTuple):
    """Resumo de uma execução da suíte de aceitação."""

    total: int
    passed: int
    failed: int


def _now() -> datetime:
    return datetime.now().astimezone()


def build_trial_id(participant_id: str, kata_id: str, treatment: str) -> str:
    """Compõe o identificador único do trial a partir de participante + kata + tratamento.

    A combinação já é única por desenho (Seção 2.1 da metodologia: um
    participante nunca resolve a mesma kata mais de uma vez), então gerar o
    `trial_id` a partir dela evita digitação redundante e colisões.
    """
    fields = {"participant_id": participant_id, "kata_id": kata_id, "treatment": treatment}
    for label, value in fields.items():
        if not value or TRIAL_ID_SEPARATOR in value:
            raise TrialCollectionError(
                f"{label} inválido para compor o trial_id: {value!r} "
                f"(não pode ser vazio nem conter '{TRIAL_ID_SEPARATOR}')"
            )
    return TRIAL_ID_SEPARATOR.join((participant_id, kata_id, treatment))


def _attempt_entry(checked_at: datetime, elapsed_seconds: float, result: SuiteResult, note: str) -> dict[str, Any]:
    return {
        "checked_at": checked_at.isoformat(timespec="seconds"),
        "elapsed_seconds": round(elapsed_seconds, 3),
        "total_tests": result.total,
        "passed_tests": result.passed,
        "failed_tests": result.failed,
        "note": note,
    }


def run_trial(
    *,
    trial_id: str,
    participant_id: str,
    kata_id: str,
    treatment: str,
    run_suite: Callable[[], SuiteResult],
    run_final_check: Callable[[], SuiteResult] | None = None,
    time_limit_seconds: int = TIME_LIMIT_SECONDS,
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    wall_clock: Callable[[], datetime] = _now,
) -> dict[str, Any]:
    """Cronometra um trial até o sucesso ou o limite de tempo, sem tocar em disco.

    `run_suite` é chamado repetidamente (a cada `poll_interval_seconds`,
    limitado ao tempo restante) até relatar zero falhas com ao menos um
    teste, ou até `time_limit_seconds` ser atingido. `monotonic`/`sleep` são
    injetáveis para permitir testar o cronômetro sem esperar tempo real.

    Se um poll já reportou sucesso (zero falhas), o resultado final reaproveita
    esse poll em vez de rodar a suíte de novo: uma nova execução, ainda que
    milissegundos depois, cria uma janela de corrida entre o cronômetro e o
    último salvamento do participante — foi o que invalidou o final_check de
    `P01-K02-manual` (ver `Docs/protocol-decisions.md`, Seção 4). Só quando o
    trial é censurado (limite de tempo atingido sem sucesso) a suíte é rodada
    mais uma vez, para capturar o estado exato no corte.
    """
    if treatment not in VALID_TREATMENTS:
        raise TrialCollectionError(
            f"Tratamento inválido: {treatment!r} (use um de {sorted(VALID_TREATMENTS)})"
        )

    started_at = wall_clock()
    start_mono = monotonic()
    attempts: list[dict[str, Any]] = []
    completed = False
    duration_seconds = time_limit_seconds

    while True:
        elapsed = monotonic() - start_mono
        if elapsed >= time_limit_seconds:
            duration_seconds = time_limit_seconds
            break
        try:
            result = run_suite()
        except Exception as error:  # noqa: BLE001 - encerramento inesperado precisa de mensagem clara
            raise TrialCollectionError(
                f"Falha inesperada ao executar a suíte do trial {trial_id}: {error}"
            ) from error
        elapsed = monotonic() - start_mono
        attempts.append(_attempt_entry(wall_clock(), elapsed, result, "poll"))
        if result.total > 0 and result.failed == 0:
            completed = True
            duration_seconds = min(int(round(elapsed)), time_limit_seconds)
            break
        if elapsed >= time_limit_seconds:
            duration_seconds = time_limit_seconds
            break
        remaining = time_limit_seconds - elapsed
        sleep(min(poll_interval_seconds, remaining))

    finished_at = wall_clock()
    censored = not completed

    if completed:
        last_poll = attempts[-1]
        final_result = SuiteResult(
            total=last_poll["total_tests"],
            passed=last_poll["passed_tests"],
            failed=last_poll["failed_tests"],
        )
    else:
        final_runner = run_final_check or run_suite
        try:
            final_result = final_runner()
        except Exception as error:  # noqa: BLE001 - idem, na verificação final
            raise TrialCollectionError(
                f"Falha inesperada na verificação final do trial {trial_id}: {error}"
            ) from error
    attempts.append(_attempt_entry(wall_clock(), duration_seconds, final_result, "final_check"))

    total, passed, failed = final_result
    success_rate = round(passed / total * 100, 2) if total else None

    return {
        "schema_version": 1,
        "trial_id": trial_id,
        "participant_id": participant_id,
        "kata_id": kata_id,
        "treatment": treatment,
        "started_at": started_at.isoformat(timespec="seconds"),
        "finished_at": finished_at.isoformat(timespec="seconds"),
        "duration_seconds": duration_seconds,
        "completed": completed,
        "censored": censored,
        "total_tests": total,
        "passed_tests": passed,
        "failed_tests": failed,
        "success_rate": success_rate,
        "time_limit_seconds": time_limit_seconds,
        "poll_interval_seconds": poll_interval_seconds,
        "incident_flag": False,
        "attempts": attempts,
    }


def _read_junit_summary(junit_path: Path) -> SuiteResult:
    """Lê total, testes passando e testes falhando de um relatório JUnit XML.

    Mesma leitura usada por `scripts/run_tests.py`. Um relatório ausente é
    tratado como "nenhum teste ainda" (0/0/0), não como falha — só uma
    execução malsucedida da própria suíte é considerada inesperada.
    """
    if not junit_path.exists():
        return SuiteResult(total=0, passed=0, failed=0)
    try:
        root = ET.parse(junit_path).getroot()
    except ET.ParseError as error:
        raise TrialCollectionError(f"Relatório JUnit inválido: {junit_path}: {error}") from error
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    if suite is None:
        return SuiteResult(total=0, passed=0, failed=0)
    total = int(suite.get("tests", 0))
    failed = int(suite.get("failures", 0)) + int(suite.get("errors", 0))
    skipped = int(suite.get("skipped", 0))
    passed = total - failed - skipped
    return SuiteResult(total=total, passed=passed, failed=failed)


def _run_pytest(tests_dir: Path, src_dir: Path, junit_path: Path) -> SuiteResult:
    """Executa a suíte de aceitação uma vez e devolve o resumo do JUnit gerado."""
    junit_path.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["KATA_SRC_DIR"] = str(src_dir)
    try:
        subprocess.run(
            [sys.executable, "-m", "pytest", str(tests_dir), f"--junit-xml={junit_path}"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except OSError as error:
        raise TrialCollectionError(f"Não foi possível executar a suíte de testes: {error}") from error
    return _read_junit_summary(junit_path)


def _write_incident(output_dir: Path, trial_id: str, message: str) -> Path:
    incident_path = output_dir / "incident.json"
    incident = {
        "schema_version": 1,
        "trial_id": trial_id,
        "incident_flag": True,
        "recorded_at": _now().isoformat(timespec="seconds"),
        "message": message,
    }
    incident_path.write_text(json.dumps(incident, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return incident_path


def collect_trial(
    participant_id: str,
    kata_id: str,
    treatment: str,
    tests_dir: Path,
    src_dir: Path,
    *,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    time_limit_seconds: int = TIME_LIMIT_SECONDS,
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
) -> Path:
    """Cronometra e registra um trial real, gravando o resultado em disco.

    Cria `output_root/<trial_id>/` com `final_junit.xml` (saída bruta da
    última verificação da suíte) e `trial.json` (registro consolidado). Um
    encerramento inesperado — falha de infraestrutura ou interrupção manual —
    preserva um `incident.json` em vez do registro do trial. Em ambos os
    casos, um diretório de trial já existente nunca é sobrescrito: uma nova
    tentativa precisa de decisão explícita (Seção 10.5 da metodologia), não
    de repetição automática.
    """
    if treatment not in VALID_TREATMENTS:
        raise TrialCollectionError(
            f"Tratamento inválido: {treatment!r} (use um de {sorted(VALID_TREATMENTS)})"
        )
    tests_dir = Path(tests_dir).resolve()
    src_dir = Path(src_dir).resolve()
    if not tests_dir.is_dir():
        raise TrialCollectionError(f"Diretório de testes inexistente: {tests_dir}")
    if not src_dir.is_dir():
        raise TrialCollectionError(f"Diretório de implementação inexistente: {src_dir}")

    trial_id = build_trial_id(participant_id, kata_id, treatment)
    output_dir = Path(output_root).resolve() / trial_id
    if output_dir.exists():
        raise TrialCollectionError(f"Trial já coletado e não será sobrescrito: {output_dir}")
    output_dir.mkdir(parents=True)

    poll_junit_path = output_dir / "_poll_junit.xml"
    final_junit_path = output_dir / "final_junit.xml"

    def run_suite() -> SuiteResult:
        return _run_pytest(tests_dir, src_dir, poll_junit_path)

    def run_final_check() -> SuiteResult:
        return _run_pytest(tests_dir, src_dir, final_junit_path)

    try:
        record = run_trial(
            trial_id=trial_id,
            participant_id=participant_id,
            kata_id=kata_id,
            treatment=treatment,
            run_suite=run_suite,
            run_final_check=run_final_check,
            time_limit_seconds=time_limit_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )
    except KeyboardInterrupt:
        _write_incident(
            output_dir,
            trial_id,
            "Trial interrompido manualmente (KeyboardInterrupt) antes do encerramento padrão.",
        )
        raise TrialCollectionError(
            f"Trial {trial_id} interrompido manualmente. Estado parcial preservado em {output_dir}."
        ) from None
    except TrialCollectionError as error:
        _write_incident(output_dir, trial_id, str(error))
        raise

    if record["completed"] and not final_junit_path.exists() and poll_junit_path.exists():
        # Sucesso: run_trial reaproveitou o último poll em vez de rodar a
        # suíte de novo (ver docstring de run_trial), então o JUnit do
        # final_check nunca foi gravado — persistimos o do poll vencedor.
        final_junit_path.write_bytes(poll_junit_path.read_bytes())

    if poll_junit_path.exists():
        poll_junit_path.unlink()

    trial_path = output_dir / "trial.json"
    trial_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return trial_path
