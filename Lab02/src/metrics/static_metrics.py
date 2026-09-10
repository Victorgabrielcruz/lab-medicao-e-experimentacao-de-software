"""Pipeline reproduzível de métricas estáticas para código Python de produção."""
from __future__ import annotations

import json
import hashlib
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_RADON_VERSION = "6.0.1"
EXPECTED_JSCPD_VERSION = "5.2.0"
EXPECTED_PYTHON_VERSION = "3.12.14"
IGNORED_DIRECTORIES = {
    ".venv",
    "venv",
    "tests",
    "test",
    "node_modules",
    "vendor",
    "generated",
    "dist",
    "build",
    "__pycache__",
}
IGNORED_FILENAMES = {"conftest.py", "setup.py"}
TRIAL_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class MetricsCollectionError(RuntimeError):
    """Erro controlado durante a execução ou leitura de uma ferramenta."""


def discover_production_files(source: Path) -> list[Path]:
    """Lista somente arquivos Python de produção, aplicando exclusões fixas."""
    source = source.resolve()
    if not source.is_dir():
        raise MetricsCollectionError(f"Diretório de código inexistente: {source}")

    files: list[Path] = []
    for path in source.rglob("*.py"):
        relative = path.relative_to(source)
        if any(part.lower() in IGNORED_DIRECTORIES for part in relative.parts[:-1]):
            continue
        name = path.name.lower()
        if name in IGNORED_FILENAMES or name.startswith("test_") or name.endswith("_test.py"):
            continue
        files.append(path.resolve())

    if not files:
        raise MetricsCollectionError(
            f"Nenhum arquivo Python de produção encontrado em: {source}"
        )
    return sorted(files)


def _run(command: Sequence[str], *, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            list(command),
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "RADONFILESENCODING": "UTF-8"},
        )
    except FileNotFoundError as error:
        raise MetricsCollectionError(f"Ferramenta não encontrada: {command[0]}") from error
    except subprocess.CalledProcessError as error:
        details = (error.stderr or error.stdout or "sem detalhes").strip()
        raise MetricsCollectionError(
            f"Comando falhou ({error.returncode}): {' '.join(command)}\n{details}"
        ) from error


def _require_version(command: Sequence[str], expected: str, tool: str) -> str:
    output = _run([*command, "--version"]).stdout.strip()
    match = re.search(r"\d+\.\d+\.\d+", output)
    actual = match.group(0) if match else output
    if actual != expected:
        raise MetricsCollectionError(
            f"Versão incompatível de {tool}: esperada {expected}, encontrada {actual}"
        )
    return actual


def _jscpd_command() -> list[str]:
    script = ROOT / "node_modules" / "jscpd" / "run-jscpd.js"
    if not script.is_file():
        raise MetricsCollectionError(
            "JSCPD não instalado. Execute: npm install --ignore-scripts"
        )
    return ["node", str(script)]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_raw_json(command: Sequence[str], destination: Path) -> Any:
    output = _run(command).stdout
    destination.write_text(output, encoding="utf-8")
    try:
        return json.loads(output)
    except json.JSONDecodeError as error:
        raise MetricsCollectionError(
            f"Saída inválida em JSON produzida por {' '.join(command[:4])}"
        ) from error


def _complexity_rows(raw: dict[str, list[dict[str, Any]]], source: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def visit(block: dict[str, Any], file_name: str, parent: str | None = None) -> None:
        block_type = str(block.get("type", "")).lower()
        name = str(block.get("name", ""))
        qualified_name = f"{parent}.{name}" if parent else name
        if block_type in {"f", "m", "function", "method"}:
            rows.append(
                {
                    "file": _relative_file(file_name, source),
                    "name": qualified_name,
                    "kind": "method" if block_type in {"m", "method"} else "function",
                    "line": int(block["lineno"]),
                    "end_line": int(block["endline"]),
                    "complexity": int(block["complexity"]),
                    "rank": block["rank"],
                }
            )
        child_parent = (
            qualified_name
            if block_type in {"c", "f", "m", "class", "function", "method"}
            else parent
        )
        for method in block.get("methods", []):
            visit(method, file_name, qualified_name)
        for closure in block.get("closures", []):
            visit(closure, file_name, child_parent)

    for file_name, blocks in raw.items():
        for block in blocks:
            visit(block, file_name)
    return sorted(rows, key=lambda item: (item["file"], item["line"], item["name"]))


def _relative_file(file_name: str, source: Path) -> str:
    path = Path(file_name)
    try:
        return path.resolve().relative_to(source.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def consolidate_metrics(
    trial_id: str,
    source: Path,
    files: list[Path],
    cc_raw: dict[str, list[dict[str, Any]]],
    raw_raw: dict[str, dict[str, int]],
    mi_raw: dict[str, dict[str, Any]],
    duplication_raw: dict[str, Any],
    versions: dict[str, str],
) -> dict[str, Any]:
    """Consolida os JSON brutos sem descartar os valores por arquivo/função."""
    functions = _complexity_rows(cc_raw, source)
    complexities = [item["complexity"] for item in functions]
    raw_totals = {
        key: sum(int(metrics.get(key, 0)) for metrics in raw_raw.values())
        for key in ("loc", "lloc", "sloc", "comments", "multi", "blank", "single_comments")
    }
    mi_files = [
        {
            "file": _relative_file(file_name, source),
            "maintainability_index": float(metrics["mi"]),
            "rank": metrics["rank"],
        }
        for file_name, metrics in mi_raw.items()
    ]
    mi_values = [item["maintainability_index"] for item in mi_files]
    duplicate_total = duplication_raw.get("statistics", {}).get("total", {})

    return {
        "schema_version": 1,
        "trial_id": trial_id,
        "source_path": str(source.resolve()),
        "collected_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "tool_versions": versions,
        "configuration": {
            "radon_config_sha256": _sha256(ROOT / "radon.cfg"),
            "jscpd_config_sha256": _sha256(ROOT / ".jscpd.json"),
            "loc_definition": "Radon SLOC (source lines of code)",
            "maintainability_aggregation": "arithmetic mean of per-file Radon MI",
            "jscpd_min_lines": 5,
            "jscpd_min_tokens": 50,
            "jscpd_mode": "mild",
            "excluded_directories": sorted(IGNORED_DIRECTORIES),
            "excluded_files": sorted(IGNORED_FILENAMES),
        },
        "analyzed_files": [path.relative_to(source.resolve()).as_posix() for path in files],
        "complexity": {
            "function_count": len(functions),
            "mean_cyclomatic_complexity": (
                sum(complexities) / len(complexities) if complexities else None
            ),
            "max_cyclomatic_complexity": max(complexities) if complexities else None,
            "functions": functions,
            "missing": not functions,
        },
        "loc": {
            "loc": raw_totals["sloc"],
            "logical_loc": raw_totals["lloc"],
            "physical_lines": raw_totals["loc"],
            "blank_lines": raw_totals["blank"],
            "comment_lines": raw_totals["comments"],
            "single_comment_lines": raw_totals["single_comments"],
            "multiline_string_lines": raw_totals["multi"],
            "files": raw_raw,
        },
        "maintainability": {
            "maintainability_index": sum(mi_values) / len(mi_values) if mi_values else None,
            "files": sorted(mi_files, key=lambda item: item["file"]),
            "missing": not mi_values,
        },
        "duplication": {
            "analyzed_lines": int(duplicate_total.get("lines", 0)),
            "duplicated_lines": int(duplicate_total.get("duplicatedLines", 0)),
            "duplication_percentage": float(duplicate_total.get("percentage", 0.0)),
            "duplicated_blocks": int(duplicate_total.get("clones", 0)),
        },
    }


def collect_static_metrics(
    trial_id: str,
    source: Path,
    output_root: Path = ROOT / "data" / "raw" / "metrics",
) -> Path:
    """Executa Radon/JSCPD e devolve o caminho do JSON consolidado."""
    if not TRIAL_ID_PATTERN.fullmatch(trial_id):
        raise MetricsCollectionError(
            "trial_id deve conter somente letras, números, ponto, hífen e sublinhado"
        )
    source = source.resolve()
    files = discover_production_files(source)
    python_version = ".".join(map(str, sys.version_info[:3]))
    if python_version != EXPECTED_PYTHON_VERSION:
        raise MetricsCollectionError(
            "Versão incompatível de Python: "
            f"esperada {EXPECTED_PYTHON_VERSION}, encontrada {python_version}"
        )
    output_dir = output_root.resolve() / trial_id
    if output_dir.exists():
        raise MetricsCollectionError(f"Saída já existe e não será sobrescrita: {output_dir}")
    output_dir.mkdir(parents=True)

    radon = [sys.executable, "-m", "radon"]
    jscpd = _jscpd_command()
    versions = {
        "python": python_version,
        "radon": _require_version(radon, EXPECTED_RADON_VERSION, "Radon"),
        "jscpd": _require_version(jscpd, EXPECTED_JSCPD_VERSION, "JSCPD"),
    }
    file_args = [str(path) for path in files]
    cc_raw = _write_raw_json([*radon, "cc", "-j", "-s", *file_args], output_dir / "radon-cc.json")
    raw_raw = _write_raw_json([*radon, "raw", "-j", *file_args], output_dir / "radon-raw.json")
    mi_raw = _write_raw_json([*radon, "mi", "-j", "-s", *file_args], output_dir / "radon-mi.json")

    jscpd_output = output_dir / "jscpd"
    jscpd_file_args = [str(path.relative_to(source)) for path in files]
    result = _run(
        [
            *jscpd,
            "--config",
            str(ROOT / ".jscpd.json"),
            "--reporters",
            "json",
            "--output",
            str(jscpd_output),
            *jscpd_file_args,
        ],
        cwd=source,
    )
    (output_dir / "jscpd-stdout.txt").write_text(result.stdout, encoding="utf-8")
    jscpd_report = jscpd_output / "jscpd-report.json"
    if not jscpd_report.is_file():
        raise MetricsCollectionError(f"JSCPD não gerou o relatório esperado: {jscpd_report}")
    duplication_raw = json.loads(jscpd_report.read_text(encoding="utf-8"))

    consolidated = consolidate_metrics(
        trial_id, source, files, cc_raw, raw_raw, mi_raw, duplication_raw, versions
    )
    consolidated_path = output_dir / "metrics.json"
    consolidated_path.write_text(
        json.dumps(consolidated, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return consolidated_path
