from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from src.collection import trial_collector
from src.collection.trial_collector import (
    TIME_LIMIT_SECONDS,
    SuiteResult,
    TrialCollectionError,
    build_trial_id,
    collect_trial,
    run_trial,
)


class FakeClock:
    """Relógio monotônico falso, avançado manualmente pelos testes."""

    def __init__(self, start: float = 0.0) -> None:
        self.value = start

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def _wall_clock(clock: FakeClock):
    base = datetime(2026, 9, 13, 9, 0, 0, tzinfo=timezone.utc)

    def _now() -> datetime:
        return base + timedelta(seconds=clock.value)

    return _now


def _sleep_recorder(clock: FakeClock):
    sleeps: list[float] = []

    def _sleep(seconds: float) -> None:
        sleeps.append(seconds)
        clock.advance(seconds)

    return _sleep, sleeps


def test_build_trial_id_compoe_participante_kata_e_tratamento():
    assert build_trial_id("P01", "K01", "ai") == "P01-K01-ai"


@pytest.mark.parametrize(
    "participant_id, kata_id, treatment",
    [("", "K01", "ai"), ("P01", "", "ai"), ("P01", "K01", ""), ("P01-P02", "K01", "ai")],
)
def test_build_trial_id_rejeita_campos_vazios_ou_com_separador(participant_id, kata_id, treatment):
    with pytest.raises(TrialCollectionError):
        build_trial_id(participant_id, kata_id, treatment)


def test_run_trial_encerra_no_sucesso_na_primeira_execucao_verde():
    clock = FakeClock()
    sleep, sleeps = _sleep_recorder(clock)

    def run_suite() -> SuiteResult:
        clock.advance(42.7)  # simula o tempo gasto rodando a suíte
        return SuiteResult(total=3, passed=3, failed=0)

    record = run_trial(
        trial_id="P01-K01-ai",
        participant_id="P01",
        kata_id="K01",
        treatment="ai",
        run_suite=run_suite,
        time_limit_seconds=2100,
        poll_interval_seconds=5,
        monotonic=clock,
        sleep=sleep,
        wall_clock=_wall_clock(clock),
    )

    assert record["completed"] is True
    assert record["censored"] is False
    assert record["duration_seconds"] == 43
    assert record["total_tests"] == 3
    assert record["passed_tests"] == 3
    assert record["failed_tests"] == 0
    assert record["success_rate"] == 100.0
    assert sleeps == []  # sucesso na primeira checagem, sem espera
    assert [attempt["note"] for attempt in record["attempts"]] == ["poll", "final_check"]
    assert record["started_at"] < record["finished_at"]


def test_run_trial_censura_no_limite_configurado():
    clock = FakeClock()
    sleep, sleeps = _sleep_recorder(clock)

    def run_suite() -> SuiteResult:
        clock.advance(1.0)
        return SuiteResult(total=4, passed=1, failed=3)

    record = run_trial(
        trial_id="P02-K02-manual",
        participant_id="P02",
        kata_id="K02",
        treatment="manual",
        run_suite=run_suite,
        time_limit_seconds=10,
        poll_interval_seconds=5,
        monotonic=clock,
        sleep=sleep,
        wall_clock=_wall_clock(clock),
    )

    assert record["completed"] is False
    assert record["censored"] is True
    assert record["duration_seconds"] == 10
    assert record["total_tests"] == 4
    assert record["passed_tests"] == 1
    assert record["failed_tests"] == 3
    assert sum(sleeps) <= 10


def test_run_trial_censura_produz_exatamente_2100_segundos_por_padrao():
    clock = FakeClock()
    sleep, _ = _sleep_recorder(clock)

    def run_suite() -> SuiteResult:
        clock.advance(1.0)
        return SuiteResult(total=2, passed=0, failed=2)

    record = run_trial(
        trial_id="P03-K03-manual",
        participant_id="P03",
        kata_id="K03",
        treatment="manual",
        run_suite=run_suite,
        time_limit_seconds=TIME_LIMIT_SECONDS,
        poll_interval_seconds=TIME_LIMIT_SECONDS,
        monotonic=clock,
        sleep=sleep,
        wall_clock=_wall_clock(clock),
    )

    assert record["censored"] is True
    assert record["duration_seconds"] == 2100


def test_run_trial_propaga_falha_inesperada_com_mensagem_clara():
    def run_suite() -> SuiteResult:
        raise RuntimeError("ambiente indisponível")

    clock = FakeClock()
    sleep, _ = _sleep_recorder(clock)

    with pytest.raises(TrialCollectionError, match="Falha inesperada.*P04-K04-ai"):
        run_trial(
            trial_id="P04-K04-ai",
            participant_id="P04",
            kata_id="K04",
            treatment="ai",
            run_suite=run_suite,
            time_limit_seconds=2100,
            poll_interval_seconds=5,
            monotonic=clock,
            sleep=sleep,
            wall_clock=_wall_clock(clock),
        )


def test_run_trial_rejeita_tratamento_invalido():
    clock = FakeClock()
    with pytest.raises(TrialCollectionError, match="Tratamento inválido"):
        run_trial(
            trial_id="P01-K01-x",
            participant_id="P01",
            kata_id="K01",
            treatment="x",
            run_suite=lambda: SuiteResult(1, 1, 0),
            monotonic=clock,
            sleep=lambda seconds: None,
            wall_clock=_wall_clock(clock),
        )


def _write_passing_suite(base: Path) -> tuple[Path, Path]:
    tests_dir = base / "tests"
    src_dir = base / "src"
    tests_dir.mkdir(parents=True)
    src_dir.mkdir(parents=True)
    (tests_dir / "test_ok.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    return tests_dir, src_dir


def test_collect_trial_grava_registro_de_sucesso_e_nao_sobrescreve(tmp_path: Path):
    tests_dir, src_dir = _write_passing_suite(tmp_path / "kata")
    output_root = tmp_path / "trials"

    trial_path = collect_trial(
        "P01",
        "K01",
        "ai",
        tests_dir,
        src_dir,
        output_root=output_root,
        time_limit_seconds=30,
        poll_interval_seconds=1,
    )

    assert trial_path == output_root / "P01-K01-ai" / "trial.json"
    record = json.loads(trial_path.read_text(encoding="utf-8"))
    assert record["trial_id"] == "P01-K01-ai"
    assert record["completed"] is True
    assert record["censored"] is False
    assert record["total_tests"] == 1
    assert record["passed_tests"] == 1
    assert record["failed_tests"] == 0
    assert (trial_path.parent / "final_junit.xml").is_file()
    assert not (trial_path.parent / "_poll_junit.xml").exists()

    with pytest.raises(TrialCollectionError, match="não será sobrescrit"):
        collect_trial("P01", "K01", "ai", tests_dir, src_dir, output_root=output_root)


def test_collect_trial_grava_incidente_e_preserva_em_nova_tentativa(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    tests_dir, src_dir = _write_passing_suite(tmp_path / "kata")
    output_root = tmp_path / "trials"

    def _boom(*args, **kwargs):
        raise TrialCollectionError("ambiente indisponível para executar pytest")

    monkeypatch.setattr(trial_collector, "_run_pytest", _boom)

    with pytest.raises(TrialCollectionError, match="ambiente indisponível"):
        collect_trial("P09", "K09", "ai", tests_dir, src_dir, output_root=output_root)

    incident_path = output_root / "P09-K09-ai" / "incident.json"
    assert incident_path.is_file()
    incident = json.loads(incident_path.read_text(encoding="utf-8"))
    assert incident["incident_flag"] is True
    assert "ambiente indisponível" in incident["message"]
    assert not (output_root / "P09-K09-ai" / "trial.json").exists()

    with pytest.raises(TrialCollectionError, match="não será sobrescrit"):
        collect_trial("P09", "K09", "ai", tests_dir, src_dir, output_root=output_root)
