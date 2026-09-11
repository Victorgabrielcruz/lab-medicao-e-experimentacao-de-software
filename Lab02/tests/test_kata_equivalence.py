from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]


def _rows() -> list[dict[str, str]]:
    with (ROOT / "data/metadata/kata-equivalence.csv").open(
        encoding="utf-8", newline=""
    ) as file:
        return list(csv.DictReader(file))


def test_matriz_possui_seis_katas_em_tres_pares():
    rows = _rows()

    assert len(rows) == 6
    assert {row["kata_id"] for row in rows} == {
        "K01", "K02", "K03", "K04", "K05", "K06"
    }
    assert {
        block: [row["kata_id"] for row in rows if row["block"] == block]
        for block in ("B1", "B2", "B3")
    } == {
        "B1": ["K01", "K02"],
        "B2": ["K03", "K04"],
        "B3": ["K05", "K06"],
    }
    assert all(row["pair_assessment"] == "compatible" for row in rows)


def test_matriz_corresponde_as_metricas_e_a_validacao_das_referencias():
    rows = {row["kata_id"]: row for row in _rows()}
    metrics = json.loads(
        (ROOT / "data/metadata/static-metrics-sanity.json").read_text(encoding="utf-8")
    )
    validation = json.loads(
        (ROOT / "data/metadata/reference-solutions-validation.json").read_text(
            encoding="utf-8"
        )
    )

    for metric in metrics["results"]:
        row = rows[metric["kata_id"]]
        assert int(row["function_count"]) == metric["function_count"]
        assert int(row["sloc"]) == metric["loc"]
        assert float(row["mean_cc"]) == metric["mean_cc"]
        assert int(row["max_cc"]) == metric["max_cc"]
    assert validation["summary"] == {"total": 33, "passed": 33, "failed": 0}


def test_fontes_de_referencia_nao_sao_rastreadas_e_hashes_sao_auditaveis():
    tracked = subprocess.run(
        ["git", "ls-files", "reference-solutions/**/*.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert tracked.stdout.strip() == ""

    validation = json.loads(
        (ROOT / "data/metadata/reference-solutions-validation.json").read_text(
            encoding="utf-8"
        )
    )
    for result in validation["results"]:
        source = ROOT / "reference-solutions" / result["kata_id"] / "solution.py"
        if source.exists():
            assert hashlib.sha256(source.read_bytes()).hexdigest() == result["sha256"]
            ignored = subprocess.run(
                ["git", "check-ignore", str(source)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            assert ignored.returncode == 0
