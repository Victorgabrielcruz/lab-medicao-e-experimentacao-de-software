import csv
import json

import pytest

from pipeline.config import ConfigError
from pipeline.consenso import COLUNAS_DECISOES, executar, maioria


def _gravar(caminho, colunas, linhas):
    with open(caminho, "w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, colunas, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)


def _pasta(tmp_path, tipos, corretivas):
    manifesto = {"repositorios": [
        {"repo_id": 10, "full_name": "a/a", "releases": [{"release_id": 100, "tag_name": "v1"}]},
        {"repo_id": 20, "full_name": "b/b", "releases": [{"release_id": 200, "tag_name": "v2"}]}]}
    (tmp_path / "amostra_ouro.json").write_text(json.dumps(manifesto), encoding="utf-8")
    for r in "ABC":
        _gravar(tmp_path / f"rotulador_{r}_repositorios.csv", ["repo_id", "tipo_projeto", "releases_sao_entregas_reais"],
                [{"repo_id": i, "tipo_projeto": tipos[r][n], "releases_sao_entregas_reais": "sim"}
                 for n, i in enumerate((10, 20))])
        _gravar(tmp_path / f"rotulador_{r}_releases.csv", ["repo_id", "release_id", "corretiva"],
                [{"repo_id": i, "release_id": rel, "corretiva": corretivas[r][n]}
                 for n, (i, rel) in enumerate(((10, 100), (20, 200)))])
    return tmp_path


def _decisoes(pasta, linhas):
    base = {"release_id": "", "justificativa": "", "participantes": "A, B, C", "data": "2026-10-21"}
    _gravar(pasta / "decisoes-consenso.csv", COLUNAS_DECISOES, [base | linha for linha in linhas])


TIPOS = {"A": ["biblioteca", "aplicacao"], "B": ["biblioteca", "framework"], "C": ["biblioteca", "outro"]}
CORRETIVAS = {"A": ["sim", "nao"], "B": ["sim", "sim"], "C": ["sim", "sim"]}


def test_maioria():
    assert maioria({"A": "sim", "B": "nao", "C": "sim"}) == "sim"
    assert maioria({"A": "aplicacao", "B": "biblioteca", "C": "outro"}) is None


def test_consenso_com_unanimes_maioria_e_discussao(tmp_path):
    pasta = _pasta(tmp_path, TIPOS, CORRETIVAS)
    _decisoes(pasta, [
        {"dimensao": "tipo_projeto", "repo_id": "20", "decisao": "aplicacao", "justificativa": "sem maioria"},
        {"dimensao": "corretiva", "repo_id": "20", "release_id": "200", "decisao": "sim"},
    ])
    resultado = executar(pasta)
    assert resultado["origens"]["tipo_projeto"] == {"unanime": 1, "discussao": 1}
    assert resultado["origens"]["corretiva"] == {"unanime": 1, "maioria": 1}
    with open(pasta / "consenso_repositorios.csv", encoding="utf-8-sig") as arquivo:
        linhas = list(csv.DictReader(arquivo))
    assert [(l["full_name"], l["tipo_projeto"], l["origem_tipo_projeto"]) for l in linhas] == [
        ("a/a", "biblioteca", "unanime"), ("b/b", "aplicacao", "discussao")]
    with open(pasta / "consenso_releases.csv", encoding="utf-8-sig") as arquivo:
        releases = list(csv.DictReader(arquivo))
    assert [(r["tag_name"], r["corretiva"], r["origem_corretiva"]) for r in releases] == [
        ("v1", "sim", "unanime"), ("v2", "sim", "maioria")]
    divergencia = next(d for d in resultado["divergencias"] if d["dimensao"] == "corretiva")
    assert (divergencia["A"], divergencia["maioria"], divergencia["decisao"]) == ("nao", "sim", "sim")
    assert "decisoes-consenso.csv" in resultado["entradas_sha256"]


def test_item_pendente_exige_justificativa(tmp_path):
    pasta = _pasta(tmp_path, TIPOS, CORRETIVAS)
    _decisoes(pasta, [{"dimensao": "tipo_projeto", "repo_id": "20", "decisao": ""},
                      {"dimensao": "corretiva", "repo_id": "20", "release_id": "200", "decisao": "sim"}])
    with pytest.raises(ConfigError, match="pendente exige justificativa"):
        executar(pasta)
    _decisoes(pasta, [{"dimensao": "tipo_projeto", "repo_id": "20", "decisao": "", "justificativa": "sem acordo"},
                      {"dimensao": "corretiva", "repo_id": "20", "release_id": "200", "decisao": "sim"}])
    resultado = executar(pasta)
    assert resultado["origens"]["tipo_projeto"]["pendente"] == 1


@pytest.mark.parametrize("linhas, mensagem", [
    ([{"dimensao": "corretiva", "repo_id": "20", "release_id": "200", "decisao": "sim"}], "sem decisão registrada"),
    ([{"dimensao": "tipo_projeto", "repo_id": "20", "decisao": "Aplicacao", "justificativa": "x"},
      {"dimensao": "corretiva", "repo_id": "20", "release_id": "200", "decisao": "sim"}], "fora do livro"),
    ([{"dimensao": "tipo_projeto", "repo_id": "10", "decisao": "biblioteca"}], "unânime"),
    ([{"dimensao": "tipo", "repo_id": "20", "decisao": "outro"}], "dimensão desconhecida"),
])
def test_decisoes_invalidas(tmp_path, linhas, mensagem):
    pasta = _pasta(tmp_path, TIPOS, CORRETIVAS)
    _decisoes(pasta, linhas)
    with pytest.raises(ConfigError, match=mensagem):
        executar(pasta)


def test_decisao_exige_participantes_e_data(tmp_path):
    pasta = _pasta(tmp_path, TIPOS, CORRETIVAS)
    _decisoes(pasta, [{"dimensao": "tipo_projeto", "repo_id": "20", "decisao": "aplicacao", "justificativa": "x"},
                      {"dimensao": "corretiva", "repo_id": "20", "release_id": "200", "decisao": "sim",
                       "participantes": ""}])
    with pytest.raises(ConfigError, match="participantes e data"):
        executar(pasta)


def test_consenso_exige_planilhas_completas(tmp_path):
    corretivas = {"A": ["sim", ""], "B": ["sim", "sim"], "C": ["sim", "sim"]}
    pasta = _pasta(tmp_path, TIPOS, corretivas)
    _decisoes(pasta, [{"dimensao": "tipo_projeto", "repo_id": "20", "decisao": "aplicacao", "justificativa": "x"}])
    with pytest.raises(ConfigError, match="julgamento ausente"):
        executar(pasta)
