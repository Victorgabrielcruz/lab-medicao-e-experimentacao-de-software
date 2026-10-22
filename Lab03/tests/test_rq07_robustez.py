import json

import pytest

from pipeline.rq07 import classificar_linhas
from pipeline.rq07_robustez import analisar, comparar, executar
from test_rq07 import linha


def test_concordancia_perfeita_com_classes_variadas():
    r = comparar(["Low", "High", "Elite"], ["Low", "High", "Elite"])
    assert r["n"] == 3 and r["mudaram"] == 0
    assert r["percentual_mudanca"] == 0
    assert r["kappa_quadratico"] == r["kappa_linear"] == 1


def test_discordancia_extrema_e_matriz_ordinal_fixa():
    r = comparar(["Low", "Elite"], ["Elite", "Low"])
    assert r["kappa_quadratico"] == pytest.approx(-1)
    assert r["kappa_linear"] == pytest.approx(-1)
    assert r["percentual_mudanca"] == 100
    assert r["matriz_transicao"][0][3] == r["matriz_transicao"][3][0] == 1


def test_oraculo_statsmodels_para_pesos_quadraticos_e_lineares():
    import numpy as np
    from statsmodels.stats.inter_rater import cohens_kappa
    r = comparar(["Low", "Medium", "High", "Elite", "Elite", "Low"],
                 ["Medium", "Medium", "Elite", "Elite", "Low", "Low"])
    for wt, campo in (("quadratic", "kappa_quadratico"), ("linear", "kappa_linear")):
        esperado = cohens_kappa(np.array(r["matriz_transicao"]), weights=np.arange(4), wt=wt).kappa
        assert r[campo] == pytest.approx(esperado)


def test_pares_ausentes_sao_excluidos_do_denominador():
    r = comparar(["Low", None, "Elite", "High"], ["High", "Elite", "Elite", None])
    assert (r["total"], r["n"], r["excluidos"], r["mudaram"]) == (4, 2, 2, 1)
    assert r["percentual_mudanca"] == 50


@pytest.mark.parametrize("a,b", [([], []), ([None], ["High"]), (["Elite"], ["Elite"])])
def test_kappa_nao_estimavel(a, b):
    r = comparar(a, b)
    assert r["kappa_quadratico"] is None and r["kappa_linear"] is None
    assert r["motivo_nao_estimavel"]


def test_rejeita_vetores_invalidos():
    with pytest.raises(ValueError, match="tamanho"):
        comparar(["Low"], [])
    with pytest.raises(ValueError, match="Categoria"):
        comparar(["alta"], [None])


def test_coortes_e_identidade_pareada():
    linhas = classificar_linhas([linha(), linha(id="2", cfr_b="", classe_cfr_b=""),
                                linha(id="3", calculo_parcial="true")])
    resultados = analisar(list(reversed(linhas)))
    geral = {(r["par"], r["coorte"]): r for r in resultados if r["dimensao"] == "geral"}
    assert geral["C1xC2", "completos_por_par"]["n"] == 3
    assert geral["C1xC3", "completos_por_par"]["n"] == 2
    assert geral["C1xC2", "completos_nas_tres"]["n"] == 2
    assert geral["C1xC3", "notas_disponiveis"]["n"] == 3
    assert geral["C1xC3", "sem_alertas"]["n"] == 1
    with pytest.raises(ValueError, match="Populações"):
        analisar(linhas[:-1])
    with pytest.raises(ValueError, match="duplicado"):
        analisar(linhas + [linhas[0]])


def test_execucao_real_reproduzivel(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    resultado = executar(saida=a)
    executar(saida=b)
    assert len(resultado["resultados"]) == 3 * 5 * 4
    principais = [r for r in resultado["resultados"] if r["dimensao"] == "geral"
                  and r["coorte"] == "completos_por_par"]
    assert [r["total"] for r in principais] == [500, 500, 500]
    assert [r["n"] for r in principais] == [468, 467, 467]
    assert [r["mudaram"] for r in principais] == [68, 179, 197]
    assert [r["kappa_quadratico"] for r in principais] == pytest.approx(
        [0.8410881744914163, 0.5634680983306497, 0.4494002300748937])
    for p in a.iterdir():
        assert p.read_bytes() == (b / p.name).read_bytes()
    assert json.loads((a / "robustez.json").read_text(encoding="utf-8"))["issue"] == 174
