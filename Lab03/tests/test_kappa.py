import csv
import json

import pytest

from pipeline.config import ConfigError
from pipeline.kappa import (ARQUIVO_JSON, ARQUIVO_MD, CATEGORIAS_TIPO, SIM_NAO, calcular_dimensao, executar,
                            interpretar)

ITENS = [("1",), ("2",), ("3",), ("4",)]


def _rotulos(*colunas):
    return {r: dict(zip(ITENS, valores)) for r, valores in zip("ABC", colunas)}


def test_kappa_calculado_a_mao():
    # Contagens (sim, nao): (3,0), (0,3), (2,1), (1,2) -> P̄ = 2/3, Pe = 1/2, κ = 1/3.
    rotulos = _rotulos(["sim", "nao", "sim", "sim"], ["sim", "nao", "sim", "nao"], ["sim", "nao", "nao", "nao"])
    d = calcular_dimensao(rotulos, SIM_NAO)
    assert d["p_observado"] == pytest.approx(2 / 3)
    assert d["p_esperado"] == pytest.approx(0.5)
    assert d["kappa"] == pytest.approx(1 / 3)
    assert d["interpretacao"] == "razoável"
    assert d["concordancia_itens"] == {"unanimes": 2, "maioria": 2, "todos_diferentes": 0}
    assert d["distribuicao"] == {"sim": 6, "nao": 6}


def test_concordancia_perfeita():
    rotulos = _rotulos(["sim", "nao", "sim", "nao"], ["sim", "nao", "sim", "nao"], ["sim", "nao", "sim", "nao"])
    d = calcular_dimensao(rotulos, SIM_NAO)
    assert d["kappa"] == pytest.approx(1.0) and d["interpretacao"] == "quase perfeita"


def test_ausencia_exclui_o_item_sem_virar_categoria():
    rotulos = _rotulos(["sim", "nao", "sim", None], ["sim", "nao", "sim", "nao"], ["sim", "nao", None, "nao"])
    d = calcular_dimensao(rotulos, SIM_NAO)
    assert (d["itens"], d["itens_completos"]) == (4, 2)
    assert d["ausentes_por_rotulador"] == {"A": 1, "B": 0, "C": 1}
    assert d["kappa"] == pytest.approx(1.0)


def test_nao_estimavel_sem_itens_completos():
    rotulos = _rotulos([None] * 4, ["sim"] * 4, ["sim"] * 4)
    d = calcular_dimensao(rotulos, SIM_NAO)
    assert d["kappa"] is None and d["motivo_nao_estimavel"] == "nenhum item com os três julgamentos"


def test_nao_estimavel_com_uma_so_categoria():
    rotulos = _rotulos(["sim"] * 4, ["sim"] * 4, ["sim"] * 4)
    d = calcular_dimensao(rotulos, SIM_NAO)
    assert d["kappa"] is None and "P_e = 1" in d["motivo_nao_estimavel"]
    assert d["p_esperado"] == pytest.approx(1.0)


def test_tres_categorias_diferentes():
    rotulos = _rotulos(["biblioteca"] * 4, ["framework"] * 4, ["aplicacao"] * 4)
    d = calcular_dimensao(rotulos, CATEGORIAS_TIPO)
    assert d["concordancia_itens"]["todos_diferentes"] == 4
    assert d["kappa"] == pytest.approx(-0.5) and d["interpretacao"] == "pobre"


@pytest.mark.parametrize("kappa, esperado", [
    (-0.01, "pobre"), (0.0, "leve"), (0.20, "leve"), (0.21, "razoável"), (0.40, "razoável"),
    (0.41, "moderada"), (0.60, "moderada"), (0.61, "substancial"), (0.80, "substancial"),
    (0.81, "quase perfeita"), (1.0, "quase perfeita"), (None, None),
])
def test_faixas_landis_koch(kappa, esperado):
    assert interpretar(kappa) == esperado


def _gravar(caminho, colunas, linhas):
    with open(caminho, "w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, colunas, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)


def _pasta(tmp_path, tipos, corretivas):
    manifesto = {"repositorios": [{"repo_id": 10, "releases": [{"release_id": 100}, {"release_id": 101}]},
                                  {"repo_id": 20, "releases": [{"release_id": 200}, {"release_id": 201}]}]}
    (tmp_path / "amostra_ouro.json").write_text(json.dumps(manifesto), encoding="utf-8")
    for rotulador in "ABC":
        _gravar(tmp_path / f"rotulador_{rotulador}_repositorios.csv",
                ["repo_id", "tipo_projeto", "releases_sao_entregas_reais", "observacoes"],
                [{"repo_id": i, "tipo_projeto": tipos[rotulador][n], "releases_sao_entregas_reais": "sim",
                  "observacoes": ""} for n, i in enumerate((10, 20))])
        _gravar(tmp_path / f"rotulador_{rotulador}_releases.csv",
                ["repo_id", "release_id", "corretiva", "observacoes"],
                [{"repo_id": r, "release_id": rel, "corretiva": corretivas[rotulador][n], "observacoes": ""}
                 for n, (r, rel) in enumerate(((10, 100), (10, 101), (20, 200), (20, 201)))])
    return tmp_path


def test_executar_grava_json_e_markdown(tmp_path):
    tipos = {r: ["biblioteca", "aplicacao"] for r in "ABC"}
    corretivas = {"A": ["sim", "nao", "sim", "nao"], "B": ["sim", "nao", "sim", "nao"], "C": ["sim", "nao", "", "nao"]}
    pasta = _pasta(tmp_path, tipos, corretivas)
    resultado = executar(pasta, tmp_path / "saida")
    assert resultado["completo"] is False
    assert resultado["dimensoes"]["corretiva"]["itens_completos"] == 3
    assert resultado["dimensoes"]["tipo_projeto"]["kappa"] == pytest.approx(1.0)
    assert resultado["dimensoes"]["releases_sao_entregas_reais"]["kappa"] is None
    assert set(resultado["entradas_sha256"]) == {"amostra_ouro.json"} | {
        f"rotulador_{r}_{p}.csv" for r in "ABC" for p in ("repositorios", "releases")}
    gravado = json.loads((tmp_path / "saida" / ARQUIVO_JSON).read_text(encoding="utf-8"))
    assert gravado["dimensoes"]["corretiva"]["ausentes_por_rotulador"] == {"A": 0, "B": 0, "C": 1}
    assert "Atenção" in (tmp_path / "saida" / ARQUIVO_MD).read_text(encoding="utf-8")


def test_executar_recusa_categoria_fora_do_livro(tmp_path):
    tipos = {"A": ["biblioteca", "aplicacao"], "B": ["biblioteca", "aplicacao"], "C": ["Biblioteca", "aplicacao"]}
    corretivas = {r: ["sim", "nao", "sim", "nao"] for r in "ABC"}
    with pytest.raises(ConfigError, match="fora do livro"):
        executar(_pasta(tmp_path, tipos, corretivas))


def test_executar_recusa_item_fora_do_sorteio(tmp_path):
    tipos = {r: ["biblioteca", "aplicacao"] for r in "ABC"}
    corretivas = {r: ["sim", "nao", "sim", "nao"] for r in "ABC"}
    pasta = _pasta(tmp_path, tipos, corretivas)
    _gravar(pasta / "rotulador_B_repositorios.csv", ["repo_id", "tipo_projeto", "releases_sao_entregas_reais"],
            [{"repo_id": 10, "tipo_projeto": "biblioteca", "releases_sao_entregas_reais": "sim"},
             {"repo_id": 99, "tipo_projeto": "aplicacao", "releases_sao_entregas_reais": "sim"}])
    with pytest.raises(ConfigError, match="ausentes"):
        executar(pasta)


def test_executar_recusa_chave_repetida(tmp_path):
    tipos = {r: ["biblioteca", "aplicacao"] for r in "ABC"}
    corretivas = {r: ["sim", "nao", "sim", "nao"] for r in "ABC"}
    pasta = _pasta(tmp_path, tipos, corretivas)
    _gravar(pasta / "rotulador_A_repositorios.csv", ["repo_id", "tipo_projeto", "releases_sao_entregas_reais"],
            [{"repo_id": 10, "tipo_projeto": "biblioteca", "releases_sao_entregas_reais": "sim"}] * 2)
    with pytest.raises(ConfigError, match="repetida"):
        executar(pasta)
