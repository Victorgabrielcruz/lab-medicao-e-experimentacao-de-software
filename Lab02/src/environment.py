"""Instalação, inventário e validação do ambiente experimental da S01-08."""
from __future__ import annotations

import ctypes
import importlib.metadata
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable

EXPECTED_VERSIONS = {
    "python": "3.12.14",
    "pytest": "9.1.1",
    "radon": "6.0.1",
    "node": "24.19.0",
    "npm": "11.17.0",
    "jscpd": "5.2.0",
    "uv": "0.12.10",
    "vscode": "1.137.0",
    "codex": "0.154.0",
}
# Desvio registrado em 15/09/2026 (protocol-decisions.md, Seção 3): P01 usa
# Claude Code em vez do Codex CLI no tratamento IA; P02 e P03 permanecem no
# assistente congelado originalmente. Não faz parte de EXPECTED_VERSIONS
# porque só se aplica a quem usa esse assistente, não aos três participantes.
EXPECTED_CLAUDE_VERSION = "2.1.273"
PARTICIPANT_AI_ASSISTANT = {
    "P01": "claude",
    "P02": "codex",
    "P03": "codex",
}
PARTICIPANTS = ("P01", "P02", "P03")
# Extensões instaladas por padrão pelo setup.ps1. Desde 15/09/2026
# (protocol-decisions.md, Seção 3) o grupo não exige mais que sejam as
# ÚNICAS extensões habilitadas — qualquer extensão é permitida, exceto as
# de IA generativa listadas em KNOWN_AI_EXTENSIONS.
ALLOWED_EXTENSIONS = {
    "ms-python.python",
    "ms-python.vscode-pylance",
}
KNOWN_AI_EXTENSIONS = {
    "github.copilot",
    "github.copilot-chat",
    "tabnine.tabnine-vscode",
    "codeium.codeium",
    "continue.continue",
}


class EnvironmentValidationError(RuntimeError):
    """Falha controlada ao verificar ou registrar o ambiente."""


CommandRunner = Callable[[list[str]], str]


def run_command(command: list[str]) -> str:
    """Executa um comando de inventário e devolve stdout normalizado."""
    executable = shutil.which(command[0])
    if executable is None and os.name == "nt":
        # Windows tools installed as command wrappers may expose only .cmd.
        executable = shutil.which(f"{command[0]}.cmd")
    if executable is None:
        raise EnvironmentValidationError(f"Comando não encontrado: {command[0]}")
    resolved_command = [executable, *command[1:]]
    try:
        result = subprocess.run(
            resolved_command,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise EnvironmentValidationError(
            f"Não foi possível executar {' '.join(command)!r}: {error}"
        ) from error
    return result.stdout.strip() or result.stderr.strip()


def extract_version(text: str) -> str | None:
    """Extrai a primeira versão semântica de uma saída de ferramenta."""
    match = re.search(r"(?<!\d)(\d+\.\d+\.\d+)(?!\d)", text)
    return match.group(1) if match else None


def _package_version(package: str) -> str | None:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


def _memory_bytes() -> int | None:
    if os.name == "nt":
        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("length", ctypes.c_ulong),
                ("memory_load", ctypes.c_ulong),
                ("total_physical", ctypes.c_ulonglong),
                ("available_physical", ctypes.c_ulonglong),
                ("total_page_file", ctypes.c_ulonglong),
                ("available_page_file", ctypes.c_ulonglong),
                ("total_virtual", ctypes.c_ulonglong),
                ("available_virtual", ctypes.c_ulonglong),
                ("available_extended_virtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatus()
        status.length = ctypes.sizeof(MemoryStatus)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.total_physical)
        return None
    try:
        return int(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"))
    except (AttributeError, OSError, ValueError):
        return None


def parse_extensions(output: str) -> list[dict[str, str | None]]:
    extensions: list[dict[str, str | None]] = []
    for raw_line in output.splitlines():
        line = raw_line.strip().lower()
        if not line:
            continue
        extension_id, separator, version = line.partition("@")
        extensions.append(
            {"id": extension_id, "version": version if separator else None}
        )
    return extensions


def collect_environment(
    participant_id: str,
    *,
    runner: CommandRunner = run_command,
) -> dict:
    """Coleta versões e hardware reais da máquina do participante."""
    if participant_id not in PARTICIPANTS:
        raise EnvironmentValidationError(
            f"Participante inválido: {participant_id!r}; use P01, P02 ou P03"
        )

    commands = {
        "uv": ["uv", "--version"],
        "node": ["node", "--version"],
        "npm": ["npm", "--version"],
        "jscpd": ["npx", "--no-install", "jscpd", "--version"],
        "vscode": ["code", "--version"],
        "codex": ["codex", "--version"],
        "claude": ["claude", "--version"],
    }
    versions = {
        "python": ".".join(map(str, sys.version_info[:3])),
        "pytest": _package_version("pytest"),
        "radon": _package_version("radon"),
    }
    raw_outputs: dict[str, str] = {}
    for name, command in commands.items():
        try:
            output = runner(command)
        except EnvironmentValidationError as error:
            raw_outputs[name] = str(error)
            versions[name] = None
        else:
            raw_outputs[name] = output
            versions[name] = extract_version(output)

    try:
        extension_output = runner(["code", "--list-extensions", "--show-versions"])
        extensions = parse_extensions(extension_output)
    except EnvironmentValidationError as error:
        extensions = []
        raw_outputs["vscode_extensions"] = str(error)

    return {
        "participant_id": participant_id,
        "captured_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "operating_system": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "architecture": platform.machine(),
        },
        "hardware": {
            "processor": platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER"),
            "logical_cpu_count": os.cpu_count(),
            "memory_bytes": _memory_bytes(),
        },
        "versions": versions,
        "vscode_extensions": extensions,
        "raw_version_outputs": raw_outputs,
    }


def validate_environment(record: dict) -> list[str]:
    """Compara um inventário com o protocolo congelado."""
    errors: list[str] = []
    versions = record.get("versions", {})
    assistant = PARTICIPANT_AI_ASSISTANT.get(record.get("participant_id"), "codex")
    for tool, expected in EXPECTED_VERSIONS.items():
        if tool == "codex" and assistant != "codex":
            continue
        actual = versions.get(tool)
        if actual != expected:
            errors.append(f"{tool}: esperado {expected}, encontrado {actual or 'ausente'}")

    if assistant == "claude":
        actual_claude = versions.get("claude")
        if actual_claude != EXPECTED_CLAUDE_VERSION:
            errors.append(
                f"claude: esperado {EXPECTED_CLAUDE_VERSION}, encontrado {actual_claude or 'ausente'}"
            )

    extension_ids = {
        item.get("id", "").lower() for item in record.get("vscode_extensions", [])
    }
    prohibited = extension_ids & KNOWN_AI_EXTENSIONS
    if prohibited:
        errors.append("extensões de IA proibidas: " + ", ".join(sorted(prohibited)))
    # Qualquer outra extensão é permitida (decisão de 15/09/2026, ver
    # protocol-decisions.md, Seção 3) — só a IA generativa é controlada.

    for field in ("processor", "logical_cpu_count", "memory_bytes"):
        if not record.get("hardware", {}).get(field):
            errors.append(f"hardware sem valor para {field}")
    return errors


def empty_registry() -> dict:
    return {
        "schema_version": 1,
        "task": "S01-08",
        "expected_versions": EXPECTED_VERSIONS,
        "baseline_vscode_extensions": sorted(ALLOWED_EXTENSIONS),
        "prohibited_vscode_extensions": sorted(KNOWN_AI_EXTENSIONS),
        "participants": {participant: None for participant in PARTICIPANTS},
        "status": "pending_capture",
    }


def record_environment(
    registry_path: Path,
    record: dict,
    *,
    replace: bool = False,
) -> dict:
    """Registra uma máquina válida sem substituir evidência por acidente."""
    errors = validate_environment(record)
    if errors:
        raise EnvironmentValidationError(
            "Ambiente divergente do protocolo:\n- " + "\n- ".join(errors)
        )
    registry_path = Path(registry_path)
    registry = (
        json.loads(registry_path.read_text(encoding="utf-8"))
        if registry_path.exists()
        else empty_registry()
    )
    participant_id = record["participant_id"]
    if participant_id not in PARTICIPANTS:
        raise EnvironmentValidationError(f"Participante inválido: {participant_id}")
    if registry["participants"].get(participant_id) is not None and not replace:
        raise EnvironmentValidationError(
            f"{participant_id} já possui inventário; use --replace somente após registrar o motivo"
        )
    registry["participants"][participant_id] = record
    completed = all(registry["participants"].get(item) for item in PARTICIPANTS)
    registry["status"] = "verified" if completed else "pending_capture"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return registry


def running_process_names(runner: CommandRunner = run_command) -> set[str]:
    command = ["tasklist", "/fo", "csv", "/nh"] if os.name == "nt" else ["ps", "-eo", "comm="]
    output = runner(command)
    names: set[str] = set()
    for line in output.splitlines():
        first = line.strip().split(",", 1)[0].strip('" ')
        if first:
            names.add(Path(first).stem.lower())
    return names


def validate_treatment(
    treatment: str,
    *,
    extensions: Iterable[str],
    processes: Iterable[str],
    codex_version: str | None = None,
    claude_version: str | None = None,
    assistant: str = "codex",
    manual_confirmation: bool = False,
) -> list[str]:
    """Verifica controles observáveis dos tratamentos IA e Manual.

    ``assistant`` identifica o assistente congelado para o participante do
    trial (ver ``PARTICIPANT_AI_ASSISTANT``). O padrão é ``codex`` para não
    quebrar chamadas existentes; o desvio de 15/09/2026 (protocol-decisions.md,
    Seção 3) introduziu ``claude`` como opção válida só para P01.
    """
    if treatment not in {"ai", "manual"}:
        return [f"tratamento inválido: {treatment}"]
    if assistant not in {"codex", "claude"}:
        return [f"assistente de IA desconhecido: {assistant}"]
    extension_ids = {item.lower().split("@", 1)[0] for item in extensions}
    process_names = {Path(item).stem.lower() for item in processes}
    errors: list[str] = []
    prohibited = extension_ids & KNOWN_AI_EXTENSIONS
    if prohibited:
        errors.append(
            "extensões de IA proibidas habilitadas: " + ", ".join(sorted(prohibited))
        )
    codex_running = any(name == "codex" or name.startswith("codex-") for name in process_names)
    claude_running = any(name == "claude" or name.startswith("claude-") for name in process_names)
    if treatment == "ai":
        if assistant == "codex" and codex_version != EXPECTED_VERSIONS["codex"]:
            errors.append(
                f"Codex CLI deve estar na versão {EXPECTED_VERSIONS['codex']} no tratamento IA"
            )
        if assistant == "claude" and claude_version != EXPECTED_CLAUDE_VERSION:
            errors.append(
                f"Claude Code deve estar na versão {EXPECTED_CLAUDE_VERSION} no tratamento IA "
                "(assistente de P01, ver protocol-decisions.md, Seção 3)"
            )
    if treatment == "manual":
        if codex_running:
            errors.append("processo do Codex está ativo no tratamento Manual")
        if claude_running:
            errors.append("processo do Claude está ativo no tratamento Manual")
        if not manual_confirmation:
            errors.append("falta a confirmação explícita de ausência de IA no tratamento Manual")
    return errors
