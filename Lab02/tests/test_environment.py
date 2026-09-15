from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from src.environment import (
    ALLOWED_EXTENSIONS,
    EXPECTED_VERSIONS,
    EnvironmentValidationError,
    empty_registry,
    extract_version,
    parse_extensions,
    record_environment,
    validate_environment,
    validate_treatment,
)


def _valid_record(participant: str = "P01") -> dict:
    return {
        "participant_id": participant,
        "captured_at": "2026-09-10T12:00:00-03:00",
        "operating_system": {
            "system": "Windows",
            "release": "11",
            "version": "10.0.26200",
            "architecture": "AMD64",
        },
        "hardware": {
            "processor": "CPU de teste",
            "logical_cpu_count": 8,
            "memory_bytes": 16 * 1024**3,
        },
        "versions": dict(EXPECTED_VERSIONS),
        "vscode_extensions": [
            {"id": item, "version": "1.0.0"} for item in sorted(ALLOWED_EXTENSIONS)
        ],
        "raw_version_outputs": {},
    }


def test_extrai_versoes_e_extensoes_de_saidas_reais():
    assert extract_version("Python 3.12.14") == "3.12.14"
    assert extract_version("v24.19.0") == "24.19.0"
    assert extract_version("sem versão") is None
    assert parse_extensions("MS-PYTHON.PYTHON@2026.1.0\ncontinue.continue") == [
        {"id": "ms-python.python", "version": "2026.1.0"},
        {"id": "continue.continue", "version": None},
    ]


def test_validador_aceita_registro_completo_e_rejeita_divergencias():
    assert validate_environment(_valid_record()) == []
    invalid = _valid_record()
    invalid["versions"]["python"] = "3.13.0"
    invalid["vscode_extensions"].append({"id": "github.copilot", "version": "1.0.0"})
    errors = validate_environment(invalid)
    assert any("python: esperado 3.12.14" in error for error in errors)
    assert any("github.copilot" in error for error in errors)


def test_extensoes_neutras_sao_livres_so_ia_generativa_e_proibida():
    # Decisão de 15/09/2026 (protocol-decisions.md, Seção 3): o grupo deixou
    # de exigir que só as duas extensões de baseline estejam habilitadas.
    record = _valid_record()
    record["vscode_extensions"].append({"id": "esbenp.prettier-vscode", "version": "9.0.0"})
    record["vscode_extensions"].append({"id": "ms-azuretools.vscode-docker", "version": "1.0.0"})
    assert validate_environment(record) == []

    record["vscode_extensions"].append({"id": "tabnine.tabnine-vscode", "version": "1.0.0"})
    errors = validate_environment(record)
    assert any("tabnine.tabnine-vscode" in error for error in errors)


def test_registro_exige_tres_participantes_e_nao_sobrescreve(tmp_path: Path):
    path = tmp_path / "environment.json"
    registry = empty_registry()
    assert registry["status"] == "pending_capture"

    for participant in ("P01", "P02", "P03"):
        registry = record_environment(path, _valid_record(participant))
    assert registry["status"] == "verified"
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert all(saved["participants"].values())

    with pytest.raises(EnvironmentValidationError, match="já possui inventário"):
        record_environment(path, _valid_record("P01"))


def test_registro_recusa_ambiente_incompativel(tmp_path: Path):
    record = _valid_record()
    record["versions"]["pytest"] = None
    with pytest.raises(EnvironmentValidationError, match="pytest"):
        record_environment(tmp_path / "environment.json", record)


def test_controle_dos_tratamentos_ai_e_manual():
    # Inclui uma extensão neutra fora do baseline para confirmar que ela não
    # é mais barrada (decisão de 15/09/2026, protocol-decisions.md Seção 3).
    extensions = sorted(ALLOWED_EXTENSIONS) + ["esbenp.prettier-vscode"]
    assert validate_treatment(
        "ai",
        extensions=extensions,
        processes=[],
        codex_version="0.154.0",
    ) == []
    assert validate_treatment(
        "manual",
        extensions=extensions,
        processes=["python"],
        codex_version="0.154.0",
        manual_confirmation=True,
    ) == []

    ai_errors = validate_treatment(
        "ai", extensions=extensions, processes=[], codex_version="0.155.0"
    )
    assert any("0.154.0" in error for error in ai_errors)
    manual_errors = validate_treatment(
        "manual",
        extensions=extensions,
        processes=["codex.exe"],
        codex_version="0.154.0",
    )
    assert any("processo do Codex" in error for error in manual_errors)
    assert any("confirmação explícita" in error for error in manual_errors)

    ai_extension_errors = validate_treatment(
        "manual",
        extensions=extensions + ["tabnine.tabnine-vscode"],
        processes=[],
        codex_version="0.154.0",
        manual_confirmation=True,
    )
    assert any("tabnine.tabnine-vscode" in error for error in ai_extension_errors)


def test_versoes_do_codigo_correspondem_ao_protocolo_e_ao_registro():
    protocol = json.loads((ROOT / "data/metadata/protocol.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "data/metadata/environment.json").read_text(encoding="utf-8"))
    actual = {
        "python": protocol["stack"]["language_version"],
        "pytest": protocol["stack"]["test_framework_version"],
        **protocol["stack"]["tool_versions"],
        "vscode": protocol["ide"]["version"],
        "codex": protocol["ai_treatment"]["version"],
    }
    assert actual == EXPECTED_VERSIONS
    assert registry["expected_versions"] == EXPECTED_VERSIONS


def test_locks_e_setup_usam_as_versoes_congeladas():
    requirements = (ROOT / "requirements.lock").read_text(encoding="utf-8")
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    setup = (ROOT / "scripts/setup.ps1").read_text(encoding="utf-8")
    assert "pytest==9.1.1" in requirements
    assert "radon==6.0.1" in requirements
    assert package["devDependencies"]["jscpd"] == "5.2.0"
    assert "requirements.lock" in setup
    for version in ("3.12.14", "0.12.10", "24.19.0", "1.137.0", "0.154.0"):
        assert version in setup
