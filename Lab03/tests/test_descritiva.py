import json
import math

import pandas as pd
import pytest

from pipeline.descritiva import (SEMANAS_POR_MES, carregar_dataset, comparar_variantes, episodios_recuperacao,
                                 exportar_episodios, pares_lead_time, pares_variantes, resumo, tabela_resumo)


def test_resumo_ignora_nulos_sem_imputar_zero():
    linha = resumo(pd.Series([1.0, None, 3.0, 2.0, 4.0, None], name="df"))
    assert (linha["n"], linha["ausentes"]) == (4, 2)
    assert (linha["minimo"], linha["mediana"], linha["maximo"]) == (1.0, 2.5, 4.0)
    assert (linha["q1"], linha["q3"], linha["iqr"]) == (1.75, 3.25, 1.5)
    assert linha["media"] == 2.5


def test_resumo_de_metrica_sem_valores():
    linha = resumo(pd.Series([None, None], dtype=float), "cfr_b")
    assert (linha["metrica"], linha["n"], linha["ausentes"]) == ("cfr_b", 0, 2)
    assert linha["mediana"] is None and linha["iqr"] is None


def test_tabela_resumo_usa_rotulos_na_ordem():
    dados = pd.DataFrame({"x": [1.0, 2.0], "y": [None, 5.0]})
    tabela = tabela_resumo(dados, {"Y": "y", "X": "x"})
    assert list(tabela["metrica"]) == ["Y", "X"]
    assert list(tabela["n"]) == [1, 2]


def test_pares_lead_time_exige_as_duas_variantes():
    dados = pd.DataFrame({
        "id": [1, 2, 3, 4], "full_name": ["a/a", "b/b", "c/c", "d/d"],
        "lead_time_a": [10.0, None, 30.0, 5.0], "lead_time_b": [4.0, 7.0, None, 5.0],
    })
    pares = pares_lead_time(dados)
    assert list(pares["id"]) == [1, 4]
    assert list(pares["diferenca"]) == [6.0, 0.0]
    assert list(pares["razao"]) == [2.5, 1.0]


def test_comparar_variantes_conta_sinais():
    pares = pd.DataFrame({"diferenca": [6.0, 0.0, -2.0, 3.0], "razao": [2.0, 1.0, 0.5, 1.5]})
    assert comparar_variantes(pares) == {
        "n_pares": 4, "a_maior": 2, "iguais": 1, "a_menor": 1, "mediana_diferenca": 1.5, "mediana_razao": 1.25,
    }


def test_comparar_variantes_sem_pares():
    pares = pd.DataFrame({"diferenca": [], "razao": []})
    resultado = comparar_variantes(pares)
    assert resultado["n_pares"] == 0 and resultado["mediana_diferenca"] is None


def test_carregar_dataset_decodifica_listas(tmp_path):
    caminho = tmp_path / "d.csv"
    caminho.write_text('id,deployment_frequency,metricas_ausentes\n1,0.5,"[""cfr_b""]"\n2,,[]\n', encoding="utf-8")
    dados = carregar_dataset(caminho)
    assert dados["metricas_ausentes"].tolist() == [["cfr_b"], []]
    assert math.isnan(dados.loc[1, "deployment_frequency"])


def test_semanas_por_mes():
    assert SEMANAS_POR_MES == pytest.approx(4.348, abs=1e-3)


def test_pares_variantes_razao_nula_quando_b_zero():
    dados = pd.DataFrame({"id": [1, 2, 3], "full_name": ["a/a", "b/b", "c/c"],
                          "cfr_a": [0.2, 0.1, None], "cfr_b": [0.0, 0.4, 0.3]})
    pares = pares_variantes(dados, "cfr_a", "cfr_b")
    assert list(pares["id"]) == [1, 2]
    assert pares["diferenca"].tolist() == pytest.approx([0.2, -0.3])
    assert math.isnan(pares.loc[0, "razao"]) and pares.loc[1, "razao"] == pytest.approx(0.25)
    assert comparar_variantes(pares)["mediana_razao"] == pytest.approx(0.25)


def _tempo_recuperacao():
    return {"repositorios": [
        {"id": 20, "full_name": "b/b", "total_episodios": 4, "episodios_recuperados": 3, "episodios_censurados": 1,
         "proporcao_censurados": 0.25, "historico_inicial_nao_observado": [{"workflow": 1}, {"workflow": 2}]},
        {"id": 10, "full_name": "a/a", "total_episodios": 0, "episodios_recuperados": 0, "episodios_censurados": 0,
         "proporcao_censurados": None, "historico_inicial_nao_observado": []},
    ]}


def test_episodios_recuperacao_conta_censura_a_esquerda_a_parte():
    episodios = episodios_recuperacao(_tempo_recuperacao())
    assert list(episodios["id"]) == [10, 20]
    linha = episodios.set_index("id").loc[20]
    assert (linha["episodios_censurados"], linha["sequencias_censura_esquerda"]) == (1, 2)
    assert pd.isna(episodios.set_index("id").loc[10, "proporcao_censurados"])


def test_exportar_episodios_registra_origem(tmp_path):
    entrada = tmp_path / "tempo_recuperacao.json"
    entrada.write_text(json.dumps(_tempo_recuperacao()), encoding="utf-8")
    saida = tmp_path / "dados" / "episodios.csv"
    exportar_episodios(entrada, saida)
    assert pd.read_csv(saida)["total_episodios"].tolist() == [0, 4]
    origem = json.loads(saida.with_suffix(".json").read_text(encoding="utf-8"))
    assert origem["origem"] == "tempo_recuperacao.json" and origem["repositorios"] == 2
    assert len(origem["origem_sha256"]) == 64
