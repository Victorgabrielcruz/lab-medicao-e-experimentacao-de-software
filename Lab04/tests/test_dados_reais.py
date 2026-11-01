"""Integridade da coleta e casos relevantes para a calibração da #263."""

from copy import deepcopy
import csv
import json
from pathlib import Path

import pytest

from hipotese.dados_reais import (
    COLUNAS,
    PASTA_DADOS,
    gerar_artefatos,
    resumir_amostra,
    selecionar_execucoes,
)


def snapshot_exemplo(conclusoes):
    snapshot = {
        "repositorio": "exemplo/projeto", "workflow_id": 1, "workflow": "test",
        "branch": "main", "evento": "push", "corte_criado_em_utc": "2026-11-01T00:00:00Z",
        "limite_execucoes": len(conclusoes), "paginas": [{"quantidade": len(conclusoes)}],
        "execucoes": [],
    }
    for indice, conclusao in enumerate(conclusoes, 1):
        snapshot["execucoes"].append({
            "id": indice, "workflow_id": 1, "name": "test", "head_branch": "main",
            "event": "push", "head_repository": "exemplo/projeto",
            "created_at": f"2026-10-01T00:00:{indice:02d}Z",
            "status": "completed" if conclusao else "in_progress", "conclusion": conclusao,
            "html_url": f"https://github.com/exemplo/projeto/actions/runs/{indice}",
        })
    return snapshot


def test_descartes_preservam_a_ordem_e_nao_viram_sucessos():
    snapshot = snapshot_exemplo([
        "failure", "cancelled", "success", "skipped", "timed_out", "neutral", None, "failure"
    ])
    snapshot["execucoes"].reverse()  # A API entrega primeiro os mais recentes.
    linhas, descartes = selecionar_execucoes(snapshot)
    assert [linha["run_id"] for linha in linhas] == [1, 3, 8]
    assert [linha["falhou"] for linha in linhas] == [1, 0, 1]
    assert descartes == {"cancelled": 1, "skipped": 1, "timed_out": 1, "neutral": 1, "in_progress": 1}


@pytest.mark.parametrize("campo,valor", [
    ("workflow_id", 2), ("name", "deploy"), ("head_branch", "feature"),
    ("event", "pull_request"), ("head_repository", "outro/projeto"),
])
def test_rejeita_mistura_de_origens(campo, valor):
    snapshot = snapshot_exemplo(["success", "failure"])
    snapshot["execucoes"][0][campo] = valor
    with pytest.raises(ValueError, match="fora do workflow"):
        selecionar_execucoes(snapshot)


def test_rejeita_duplicatas_corte_incorreto_e_janela_incompleta():
    original = snapshot_exemplo(["success", "failure"])
    duplicado = deepcopy(original)
    duplicado["execucoes"][1]["id"] = 1
    with pytest.raises(ValueError, match="duplicado"):
        selecionar_execucoes(duplicado)
    depois_do_corte = deepcopy(original)
    depois_do_corte["execucoes"][0]["created_at"] = "2026-12-01T00:00:00Z"
    with pytest.raises(ValueError, match="posterior ao corte"):
        selecionar_execucoes(depois_do_corte)
    original["execucoes"].pop()
    with pytest.raises(ValueError, match="janela de coleta completa"):
        selecionar_execucoes(original)


def test_sequencias_e_acf_conhecidas():
    resumo = resumir_amostra([{"falhou": x} for x in [0, 0, 1, 1]])
    assert resumo["maior_sequencia_falhas"] == 2
    assert resumo["autocorrelacao_lag1"] == pytest.approx(0.25)
    assert resumo["transicoes"] == {"00": 1, "01": 1, "10": 0, "11": 1}
    assert resumo["p_falha_apos_sucesso"] == 0.5
    assert resumo["p_falha_apos_falha"] == 1.0


def test_ausencia_de_falhas_tem_ic_nao_degenerado_e_acf_indefinida():
    resumo = resumir_amostra([{"falhou": 0}] * 100)
    assert resumo["maior_sequencia_falhas"] == 0
    assert resumo["autocorrelacao_lag1"] is None
    assert resumo["p_falha_apos_falha"] is None
    assert resumo["ic_taxa_falha"]["inferior"] == pytest.approx(0.0, abs=1e-15)
    assert resumo["ic_taxa_falha"]["superior"] == pytest.approx(0.0369934982069857)


def test_somente_falhas_e_amostra_vazia():
    resumo = resumir_amostra([{"falhou": 1}] * 5)
    assert resumo["maior_sequencia_falhas"] == 5
    assert resumo["autocorrelacao_lag1"] is None
    with pytest.raises(ValueError, match="vazia"):
        resumir_amostra([])


def test_artefatos_versionados_reproduzem_a_coleta_sem_rede(tmp_path: Path):
    snapshot = (PASTA_DADOS / "ci_pytest_snapshot.json").read_bytes()
    (tmp_path / "ci_pytest_snapshot.json").write_bytes(snapshot)
    resumo = gerar_artefatos(tmp_path)
    for nome in ("ci_pytest.csv", "ci_pytest_resumo.json"):
        assert (tmp_path / nome).read_bytes() == (PASTA_DADOS / nome).read_bytes()
    with (tmp_path / "ci_pytest.csv").open(encoding="utf-8", newline="") as arquivo:
        reader = csv.DictReader(arquivo)
        assert reader.fieldnames == list(COLUNAS)
        linhas = list(reader)
    assert len(linhas) == len({linha["run_id"] for linha in linhas}) == 243
    assert sum(int(linha["falhou"]) for linha in linhas) == 10
    assert [(l["criado_em"], int(l["run_id"])) for l in linhas] == sorted(
        (l["criado_em"], int(l["run_id"])) for l in linhas
    )
    assert all(int(l["falhou"]) == int(l["conclusao"] == "failure") for l in linhas)
    assert resumo["n_candidatas"] == len(linhas) + resumo["n_descartadas"] == 300
    assert resumo["descartadas_por_motivo"] == {"cancelled": 57}
    assert resumo["maior_sequencia_falhas_sem_descartes_intermediarios"] == 2
    assert resumo["estatisticas"]["maior_sequencia_falhas"] == 3
    assert resumo["estatisticas"]["autocorrelacao_lag1"] == pytest.approx(0.2740723078825129)
    assert json.loads((tmp_path / "ci_pytest_resumo.json").read_text())["estatisticas"]["n_falhas"] == 10
