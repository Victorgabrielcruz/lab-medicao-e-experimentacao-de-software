import datetime as dt
import json
import runpy
import sys
from pathlib import Path

import pytest
import yaml

from pipeline import metricas
from pipeline.config import ConfigError

JANELA = {"inicio": "2025-10-01T00:00:00Z", "fim_exclusivo": "2026-10-01T00:00:00Z"}
SAIDAS = {
    "deployment_frequency": ("deployment_frequency.json", "deployment_frequency", "classe", 2.0, "High"),
    "lead_time_a": ("lead_time_release.json", "lead_time_horas", "classe_lead_time", 216.0, "Medium"),
    "lead_time_b": ("lead_time_commit.json", "lead_time_horas", "classe_lead_time", 30.0, "High"),
    "cfr_a": ("cfr.json", "change_failure_rate", "classe_cfr", 0.1, "Elite"),
    "cfr_b": ("cfr_b.json", "change_failure_rate", "classe_cfr", 0.4, "Medium"),
    "tempo_recuperacao": ("tempo_recuperacao.json", "tempo_recuperacao", "classe_tempo_recuperacao", 0.5, "Elite"),
}
OBRIGATORIAS = [m for m in SAIDAS if m != "cfr_b"]


@pytest.fixture
def config(tmp_path):
    return {"api": {"base_url": "https://api.github.com"},
            "janela": {"inicio": dt.date(2025, 10, 1), "fim": dt.date(2026, 9, 30)},
            "inclusao": {"min_releases": 5, "min_runs_validos": 50},
            "runs": {"evento": "push", "somente_default_branch": True,
                     "conclusoes_sucesso": ["success"],
                     "conclusoes_falha": ["failure", "timed_out", "startup_failure"]},
            "caminhos": {"raw": str(tmp_path / "raw"), "processed": str(tmp_path / "processed"),
                         "cache": str(tmp_path / "cache")}}


def linha(metrica, id=10, nome="org/projeto", **campos):
    _, campo, campo_classe, valor, classe = SAIDAS[metrica]
    return {"id": id, "full_name": nome, campo: valor, campo_classe: classe, **campos}


def gravar(config, metrica, repos=None, janela=JANELA):
    caminho = Path(config["caminhos"]["processed"]) / SAIDAS[metrica][0]
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps({"janela": janela,
                                   "repositorios": [linha(metrica)] if repos is None else repos}),
                       encoding="utf-8")
    return caminho


def gravar_todas(config, metricas_gravadas=OBRIGATORIAS):
    for metrica in metricas_gravadas:
        gravar(config, metrica)


def gravar_config(config, tmp_path):
    caminho = tmp_path / "config.yaml"
    caminho.write_text(yaml.safe_dump(config), encoding="utf-8")
    return str(caminho)


def test_junta_todas_as_variantes_por_repositorio(config):
    gravar_todas(config, list(SAIDAS))
    saida, lista, pendentes = metricas.executar(config)
    assert pendentes == []
    assert lista == [{
        "id": 10, "full_name": "org/projeto",
        "deployment_frequency": 2.0, "classe_deployment_frequency": "High",
        "lead_time_a": 216.0, "classe_lead_time_a": "Medium",
        "lead_time_b": 30.0, "classe_lead_time_b": "High",
        "cfr_a": 0.1, "classe_cfr_a": "Elite",
        "cfr_b": 0.4, "classe_cfr_b": "Medium",
        "tempo_recuperacao": 0.5, "classe_tempo_recuperacao": "Elite",
        "coleta_incompleta": False, "calculo_parcial": False, "metricas_ausentes": []}]
    gravado = json.loads(saida.read_text(encoding="utf-8"))
    assert saida == Path(config["caminhos"]["processed"]) / "metricas.json"
    assert gravado["janela"] == JANELA
    assert gravado["repositorios"] == lista
    assert gravado["total_repositorios"] == gravado["repositorios_com_todas_as_metricas"] == 1
    assert gravado["repositorios_por_metrica"] == dict.fromkeys(SAIDAS, 1)
    assert set(gravado["origens"]) == set(gravado["unidades"]) == set(SAIDAS)


def test_cfr_b_ausente_fica_pendente_sem_virar_zero(config):
    gravar_todas(config)
    saida, lista, pendentes = metricas.executar(config)
    assert pendentes == ["cfr_b"]
    assert lista[0]["cfr_b"] is None and lista[0]["classe_cfr_b"] is None
    assert lista[0]["metricas_ausentes"] == ["cfr_b"]
    gravado = json.loads(saida.read_text(encoding="utf-8"))
    assert gravado["variantes_pendentes"] == ["cfr_b"]
    assert gravado["repositorios_por_metrica"]["cfr_b"] == 0
    assert gravado["repositorios_com_todas_as_metricas"] == 0
    assert "cfr_b" not in gravado["origens"]


@pytest.mark.parametrize("metrica", OBRIGATORIAS)
def test_saida_obrigatoria_ausente_e_recusada(config, metrica):
    gravar_todas(config, [m for m in OBRIGATORIAS if m != metrica])
    with pytest.raises(FileNotFoundError, match=metrica):
        metricas.executar(config)
    assert not (Path(config["caminhos"]["processed"]) / "metricas.json").exists()


def test_valor_nulo_e_repositorio_fora_de_uma_saida_ficam_ausentes(config):
    gravar_todas(config)
    gravar(config, "lead_time_a", [linha("lead_time_a", lead_time_horas=None, classe_lead_time=None),
                                   linha("lead_time_a", id=20, nome="org/outro")])
    _, lista, _ = metricas.executar(config)
    por_id = {r["id"]: r for r in lista}
    assert por_id[10]["lead_time_a"] is None
    assert por_id[10]["metricas_ausentes"] == ["lead_time_a", "cfr_b"]
    assert por_id[20]["lead_time_a"] == 216.0
    assert por_id[20]["metricas_ausentes"] == ["deployment_frequency", "lead_time_b", "cfr_a", "cfr_b",
                                               "tempo_recuperacao"]


def test_zero_e_valor_calculado_e_nao_ausencia(config):
    gravar_todas(config)
    gravar(config, "cfr_a", [linha("cfr_a", change_failure_rate=0.0)])
    _, lista, _ = metricas.executar(config)
    assert lista[0]["cfr_a"] == 0.0
    assert "cfr_a" not in lista[0]["metricas_ausentes"]


def test_propaga_coleta_incompleta_e_calculo_parcial(config):
    gravar_todas(config)
    gravar(config, "tempo_recuperacao", [linha("tempo_recuperacao", coleta_incompleta=True)])
    gravar(config, "lead_time_b", [linha("lead_time_b", calculo_parcial=True)])
    saida, lista, _ = metricas.executar(config)
    assert lista[0]["coleta_incompleta"] and lista[0]["calculo_parcial"]
    gravado = json.loads(saida.read_text(encoding="utf-8"))
    assert gravado["repositorios_com_coleta_incompleta"] == 1
    assert gravado["repositorios_com_calculo_parcial"] == 1


def test_janela_divergente_e_recusada(config):
    gravar_todas(config)
    gravar(config, "cfr_a", janela={**JANELA, "inicio": "2025-01-01T00:00:00Z"})
    with pytest.raises(ConfigError, match="cfr.json"):
        metricas.executar(config)


def test_repositorio_duplicado_na_mesma_saida_e_recusado(config):
    gravar_todas(config)
    gravar(config, "cfr_a", [linha("cfr_a"), linha("cfr_a")])
    with pytest.raises(ConfigError, match="duplicado"):
        metricas.executar(config)


def test_identidade_divergente_entre_saidas_e_recusada(config):
    gravar_todas(config)
    gravar(config, "cfr_a", [linha("cfr_a", nome="org/renomeado")])
    with pytest.raises(ConfigError, match="Identidade divergente"):
        metricas.executar(config)


def test_nome_com_caixa_diferente_e_o_mesmo_repositorio(config):
    gravar_todas(config)
    gravar(config, "cfr_a", [linha("cfr_a", nome="Org/Projeto")])
    _, lista, _ = metricas.executar(config)
    assert len(lista) == 1 and lista[0]["full_name"] == "org/projeto"


def test_saida_sobre_arquivo_de_entrada_e_recusada(config):
    gravar_todas(config)
    with pytest.raises(ConfigError, match="diferente"):
        metricas.executar(config, Path(config["caminhos"]["processed"]) / "cfr.json")


def test_calcula_lead_time_por_commit_do_compare_local_quando_falta(config):
    gravar_todas(config, [m for m in OBRIGATORIAS if m != "lead_time_b"])
    raw = Path(config["caminhos"]["raw"])
    raw.mkdir(parents=True)
    anterior = {"id": 1, "tag_name": "v1", "published_at": "2026-01-01T00:00:00Z"}
    release = {"id": 2, "tag_name": "v2", "published_at": "2026-01-03T00:00:00Z"}
    (raw / "compare.json").write_text(json.dumps({
        "janela": JANELA, "definicao_deploy": "release_estavel",
        "repositorios": [{"id": 10, "full_name": "org/projeto", "default_branch": "main", "comparacoes": [{
            "release": release, "release_anterior": anterior, "total_commits_api": 1,
            "commits": [{"sha": "abc", "commit": {"author": {"date": "2026-01-02T00:00:00Z"}}}]}]}]}),
        encoding="utf-8")
    _, lista, _ = metricas.executar(config)
    assert lista[0]["lead_time_b"] == 24.0
    assert lista[0]["classe_lead_time_b"] == "High"
    assert (Path(config["caminhos"]["processed"]) / "lead_time_commit.json").is_file()


def test_cli_grava_resultado_e_relata_pendencias(config, tmp_path, capsys):
    gravar_todas(config)
    saida = tmp_path / "saida" / "metricas.json"
    assert metricas.main(["--config", gravar_config(config, tmp_path), "--saida", str(saida)]) == 0
    assert "1 repositórios, 0 com todas as variantes, 1 variantes pendentes" in capsys.readouterr().out
    assert json.loads(saida.read_text(encoding="utf-8"))["total_repositorios"] == 1


def test_cli_relata_erro_sem_gravar(config, tmp_path, capsys):
    assert metricas.main(["--config", gravar_config(config, tmp_path)]) == 2
    assert "deployment_frequency.json" in capsys.readouterr().err


def test_modulo_executavel(config, tmp_path, monkeypatch):
    gravar_todas(config)
    monkeypatch.setattr(sys, "argv", ["pipeline.metricas", "--config", gravar_config(config, tmp_path)])
    monkeypatch.delitem(sys.modules, "pipeline.metricas")
    with pytest.raises(SystemExit) as saida:
        runpy.run_module("pipeline.metricas", run_name="__main__")
    assert saida.value.code == 0
