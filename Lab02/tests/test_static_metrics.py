from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from src.metrics.static_metrics import (
    MetricsCollectionError,
    collect_static_metrics,
    consolidate_metrics,
    discover_production_files,
)


def test_descoberta_exclui_testes_dependencias_gerados_e_configuracao(tmp_path: Path):
    included = tmp_path / "src" / "service.py"
    excluded = [
        tmp_path / "tests" / "test_service.py",
        tmp_path / "node_modules" / "package.py",
        tmp_path / "generated" / "client.py",
        tmp_path / "src" / "conftest.py",
        tmp_path / "src" / "service_test.py",
    ]
    included.parent.mkdir()
    included.write_text("def service():\n    return 1\n", encoding="utf-8")
    for path in excluded:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("def excluded():\n    return 0\n", encoding="utf-8")

    assert discover_production_files(tmp_path) == [included.resolve()]


def test_descoberta_falha_quando_nao_existe_codigo_de_producao(tmp_path: Path):
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_only.py").write_text("def test_only(): pass\n", encoding="utf-8")

    with pytest.raises(MetricsCollectionError, match="Nenhum arquivo Python"):
        discover_production_files(tmp_path)


def test_consolidacao_preserva_funcoes_agregados_loc_mi_e_duplicacao(tmp_path: Path):
    source = tmp_path / "src"
    source.mkdir()
    production_file = source / "solution.py"
    production_file.write_text("def solve():\n    return True\n", encoding="utf-8")
    filename = str(production_file.resolve())
    cc_raw = {
        filename: [
            {
                "type": "F",
                "name": "solve",
                "lineno": 1,
                "endline": 2,
                "complexity": 3,
                "rank": "A",
                "closures": [],
            },
            {
                "type": "C",
                "name": "Worker",
                "lineno": 4,
                "endline": 8,
                "complexity": 4,
                "rank": "A",
                "methods": [
                    {
                        "type": "M",
                        "name": "run",
                        "lineno": 5,
                        "endline": 8,
                        "complexity": 5,
                        "rank": "A",
                        "closures": [],
                    }
                ],
            },
        ]
    }
    raw_raw = {
        filename: {
            "loc": 12,
            "lloc": 8,
            "sloc": 9,
            "comments": 1,
            "multi": 0,
            "blank": 2,
            "single_comments": 1,
        }
    }
    mi_raw = {filename: {"mi": 82.5, "rank": "A"}}
    duplication_raw = {
        "statistics": {
            "total": {
                "lines": 9,
                "duplicatedLines": 2,
                "percentage": 22.22,
                "clones": 1,
            }
        }
    }

    result = consolidate_metrics(
        "P01-K01-ai",
        source,
        [production_file.resolve()],
        cc_raw,
        raw_raw,
        mi_raw,
        duplication_raw,
        {"python": "3.12.14", "radon": "6.0.1", "jscpd": "5.2.0"},
    )

    assert result["complexity"]["function_count"] == 2
    assert result["complexity"]["mean_cyclomatic_complexity"] == 4
    assert result["complexity"]["max_cyclomatic_complexity"] == 5
    assert [item["name"] for item in result["complexity"]["functions"]] == [
        "solve",
        "Worker.run",
    ]
    assert result["loc"]["loc"] == 9
    assert result["maintainability"]["maintainability_index"] == 82.5
    assert result["duplication"] == {
        "analyzed_lines": 9,
        "duplicated_lines": 2,
        "duplication_percentage": 22.22,
        "duplicated_blocks": 1,
    }


def test_arquivo_de_validacao_das_referencias_e_consistente():
    validation = json.loads(
        (Path(__file__).parents[1] / "data/metadata/reference-solutions-validation.json")
        .read_text(encoding="utf-8")
    )

    assert validation["summary"] == {"total": 33, "passed": 33, "failed": 0}
    assert {item["kata_id"] for item in validation["results"]} == {
        "K01",
        "K02",
        "K03",
        "K04",
        "K05",
        "K06",
    }


def test_pipeline_real_coleta_duplicacao_e_nao_sobrescreve(tmp_path: Path):
    source = tmp_path / "production"
    source.mkdir()
    duplicated_code = """\
def calcular(valores):
    total = 0
    positivos = 0
    negativos = 0
    zeros = 0
    for valor in valores:
        if valor > 0:
            positivos += 1
            total += valor
        elif valor < 0:
            negativos += 1
            total -= valor
        else:
            zeros += 1
            total += 1
    quantidade = positivos + negativos + zeros
    if quantidade == 0:
        media = 0
    else:
        media = total / quantidade
    resumo = {
        "total": total,
        "positivos": positivos,
        "negativos": negativos,
        "zeros": zeros,
        "media": media,
    }
    return resumo
"""
    (source / "first.py").write_text(duplicated_code, encoding="utf-8")
    (source / "second.py").write_text(duplicated_code, encoding="utf-8")
    tests = source / "tests"
    tests.mkdir()
    (tests / "test_decoy.py").write_text(duplicated_code, encoding="utf-8")

    result_path = collect_static_metrics("integration", source, tmp_path / "metrics")
    result = json.loads(result_path.read_text(encoding="utf-8"))

    assert result["analyzed_files"] == ["first.py", "second.py"]
    assert result["complexity"]["function_count"] == 2
    assert result["loc"]["loc"] > 0
    assert result["duplication"]["duplicated_lines"] > 0
    assert result["duplication"]["duplication_percentage"] > 0
    assert (result_path.parent / "radon-cc.json").is_file()
    assert (result_path.parent / "jscpd/jscpd-report.json").is_file()

    with pytest.raises(MetricsCollectionError, match="não será sobrescrita"):
        collect_static_metrics("integration", source, tmp_path / "metrics")
