"""Q1 deve usar H₀ independente e respeitar a margem inclusiva (#270)."""

import csv

import pytest
from scipy.stats import binom

from hipotese.config import TESTE_BINOMIAL, TESTE_Z
from hipotese.erro_tipo_i import analisar_erro_tipo_i, classificar_erro_tipo_i
from hipotese.simulacao import ARQUIVO


@pytest.mark.parametrize("rejeicoes,esperado", [
    (459, "Conservador"), (460, "Dentro da margem"), (500, "Dentro da margem"),
    (540, "Dentro da margem"), (541, "Liberal"),
])
def test_margem_inclui_460_e_540_sem_classificar_por_taxas_arredondadas(rejeicoes, esperado):
    assert classificar_erro_tipo_i(rejeicoes, 10_000) == esperado


def test_q1_usa_apenas_h0_independente_sem_repetir_monte_carlo(monkeypatch):
    from hipotese import simulacao

    def nao_simular(*args, **kwargs):
        raise AssertionError("Q1 deve ler o resultado congelado, sem novos sorteios.")

    monkeypatch.setattr(simulacao, "gerar_lote", nao_simular)
    resultados = analisar_erro_tipo_i()
    z, exato = resultados
    assert [r.teste for r in resultados] == [TESTE_Z, TESTE_BINOMIAL]
    assert [(r.n, r.repeticoes) for r in resultados] == [(243, 10_000), (243, 10_000)]
    assert (z.rejeicoes, exato.rejeicoes) == (655, 396)
    assert (z.taxa_erro, exato.taxa_erro) == (0.0655, 0.0396)
    assert (z.desvio_pp, exato.desvio_pp) == pytest.approx((1.55, -1.04))
    assert (z.classificacao, exato.classificacao) == ("Liberal", "Conservador")
    assert (z.primeira_contagem_rejeitada, exato.primeira_contagem_rejeitada) == (18, 19)
    # Soma da cauda binomial, independente da enumeração usada na análise.
    assert z.taxa_teorica == pytest.approx(binom.sf(17, 243, 0.05))
    assert exato.taxa_teorica == pytest.approx(binom.sf(18, 243, 0.05))


def escrever_csv(tmp_path, alterar):
    with ARQUIVO.open(encoding="utf-8", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        colunas = leitor.fieldnames
        linhas = list(leitor)
    alterar(linhas)
    caminho = tmp_path / "simulacao.csv"
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        escritor.writeheader()
        escritor.writerows(linhas)
    return caminho


@pytest.mark.parametrize("campo,valor", [
    ("correlacao", "0.3"), ("taxa_verdadeira", "0.09"),
    ("n", "20"), ("repeticoes", "9999"),
])
def test_nao_apresenta_como_q1_uma_configuracao_fora_do_protocolo(tmp_path, campo, valor):
    caminho = escrever_csv(tmp_path, lambda linhas: linhas[0].update({campo: valor}))
    with pytest.raises(ValueError, match="protocolo independente"):
        analisar_erro_tipo_i(caminho)


def test_rejeita_proporcao_que_nao_corresponde_aos_falsos_positivos(tmp_path):
    caminho = escrever_csv(tmp_path, lambda linhas: linhas[0].update({"proporcao_rejeicao": "0.05"}))
    with pytest.raises(ValueError, match="não corresponde às contagens"):
        analisar_erro_tipo_i(caminho)


@pytest.mark.parametrize("duplicar", [False, True])
def test_requer_os_dois_testes_sem_duplicatas(tmp_path, duplicar):
    def alterar(linhas):
        if duplicar:
            linhas.append(linhas[0].copy())
        else:
            linhas.pop(0)

    caminho = escrever_csv(tmp_path, alterar)
    with pytest.raises(ValueError, match="uma linha para cada"):
        analisar_erro_tipo_i(caminho)
