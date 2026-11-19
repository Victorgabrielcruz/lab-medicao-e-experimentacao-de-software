import csv
import json

import pytest

from experimento import config
from resumir_piloto import resumir


@pytest.fixture
def piloto_sintetico(tmp_path):
    ambiente = {"sqlite_version": "teste", "experimento": {"repeticoes": 3, "aquecimentos": 1}}
    (tmp_path / "ambiente.json").write_text(json.dumps(ambiente), encoding="utf-8")
    (tmp_path / "execucao.json").write_text(
        json.dumps({"codigo_saida": 0, "duracao_parede_s": 48}), encoding="utf-8",
    )
    linhas = []
    for r in range(1, 4):
        for cfg, carga in config.combinacoes():
            leituras = round(carga.n_operacoes * carga.fracao_leitura)
            linhas.append({
                "configuracao": cfg.nome, "carga": carga.nome, "repeticao": r,
                "ordem_execucao": 13 + len(linhas), "tempo_total_s": r,
                "vazao_ops_s": carga.n_operacoes / r, "n_operacoes": carga.n_operacoes,
                "n_leituras": leituras, "n_escritas": carga.n_operacoes - leituras,
                "sqlite_version": "teste",
            })
    salvar_linhas(tmp_path, linhas)
    return tmp_path, linhas


def salvar_linhas(diretorio, linhas):
    with (diretorio / "resultados.csv").open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0]))
        escritor.writeheader()
        escritor.writerows(linhas)


def test_estatisticas_e_estimativa_com_valores_conhecidos(piloto_sintetico):
    pasta, _ = piloto_sintetico
    resumo = resumir(pasta)
    assert resumo["medicoes"] == 36
    assert resumo["estimativa_coleta_completa_s"] == 396
    assert resumo["reserva_operacional_s"] == 792
    assert resumo["soma_tempos_medidos_s"] == 72
    for grupo in resumo["grupos"]:
        assert grupo["tempo_mediana_s"] == 2
        assert grupo["tempo_q1_s"] == 1.5
        assert grupo["tempo_q3_s"] == 2.5
        assert grupo["tempo_iqr_s"] == 1
        assert grupo["tempo_desvio_padrao_s"] == 1
        assert grupo["tempo_cv_pct"] == 50


@pytest.mark.parametrize("alteracao", ["ausente", "duplicada", "vazao", "nao_finito", "ambiente"])
def test_recusa_dados_inconsistentes(piloto_sintetico, alteracao):
    pasta, linhas = piloto_sintetico
    if alteracao == "ausente":
        linhas.pop()
    elif alteracao == "duplicada":
        linhas.append(linhas[0].copy())
    elif alteracao == "vazao":
        linhas[0]["vazao_ops_s"] = 1
    elif alteracao == "nao_finito":
        linhas[0]["tempo_total_s"] = "nan"
    else:
        linhas[0]["sqlite_version"] = "outro"
    salvar_linhas(pasta, linhas)
    with pytest.raises(ValueError):
        resumir(pasta)
