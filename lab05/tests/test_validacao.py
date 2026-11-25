"""Validação real e falhas controladas, sem executar novamente o benchmark."""

import csv
import json
import shutil
from pathlib import Path

import pytest

from experimento import config
from experimento.benchmark import plano_execucoes
from experimento.validacao import (
    ARTEFATOS, COLUNAS, diagnosticar, diagnostico_temporal, sha256, validar,
)
from validar_dados import main, publicar

ORIGEM = Path(__file__).resolve().parents[1] / "data" / "coleta-completa-01"


@pytest.fixture
def coleta(tmp_path):
    pasta = tmp_path / "coleta-completa-01"
    pasta.mkdir()
    for nome in (*ARTEFATOS, "conferencia.json"):
        shutil.copyfile(ORIGEM / nome, pasta / nome)
    return pasta


def ler(pasta):
    with (pasta / "resultados.csv").open(encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def salvar(pasta, linhas, colunas=COLUNAS):
    with (pasta / "resultados.csv").open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(linhas)


def test_coleta_real_publicada_sem_alterar_entradas(coleta):
    antes = {p.name: p.read_bytes() for p in coleta.iterdir()}
    saida = coleta / "validacao"
    relatorio = publicar(coleta, saida)
    assert relatorio["status"] == "aprovada"
    assert relatorio["erros"] == []
    assert relatorio["medicoes_lidas"] == 360
    assert len(relatorio["grupos"]) == 12
    assert {g["n"] for g in relatorio["grupos"]} == {30}
    assert len(relatorio["diagnostico_temporal"]) == 33
    assert relatorio["observacoes_excluidas"] == 0
    manifesto = json.loads((saida / "manifesto.json").read_text(encoding="utf-8"))
    assert manifesto["dados"] == "../resultados.csv"
    assert manifesto["publicado_para_analise_exploratoria"] is True
    for nome, esperado in manifesto["relatorios_sha256"].items():
        assert sha256(saida / nome) == esperado
    for nome, conteudo in antes.items():
        assert (coleta / nome).read_bytes() == conteudo
    publicados = {p.name: p.read_bytes() for p in saida.iterdir()}
    publicar(coleta, saida)
    assert publicados == {p.name: p.read_bytes() for p in saida.iterdir()}


@pytest.mark.parametrize("alteracao,codigo", [
    ("linha_ausente", "completude"), ("duplicada", "completude"),
    ("aquecimento", "ordem"), ("reordenada", "ordem"),
    ("vazio", "ausente"), ("null", "ausente"), ("nan", "tipo"),
    ("infinito", "tipo"), ("zero", "dominio"), ("negativo", "dominio"),
    ("vazao", "vazao"), ("operacoes", "plano"), ("fator", "plano"),
    ("carga", "completude"), ("semente", "plano"), ("semente_float", "tipo"),
    ("semente_arredondada", "plano"), ("ambiente", "ambiente"),
    ("coluna_ausente", "schema"), ("coluna_duplicada", "schema"),
    ("coluna_extra", "schema"), ("valor_extra", "schema"),
])
def test_recusa_corrupcoes_sem_descartar_silenciosamente(coleta, alteracao, codigo):
    linhas = ler(coleta)
    colunas = list(COLUNAS)
    if alteracao == "linha_ausente":
        linhas.pop()
    elif alteracao == "duplicada":
        linhas[-1] = linhas[0].copy()
    elif alteracao == "aquecimento":
        linhas[0]["ordem_execucao"] = "1"
    elif alteracao == "reordenada":
        linhas[0], linhas[1] = linhas[1], linhas[0]
    elif alteracao in ("vazio", "null", "nan", "infinito", "zero", "negativo"):
        linhas[0]["tempo_total_s"] = {
            "vazio": "", "null": "null", "nan": "nan", "infinito": "inf",
            "zero": "0", "negativo": "-1",
        }[alteracao]
    elif alteracao == "vazao":
        linhas[0]["vazao_ops_s"] = "1"
    elif alteracao == "operacoes":
        linhas[0]["n_leituras"] = "999999"
    elif alteracao == "fator":
        linhas[0]["synchronous"] = "OFF"
    elif alteracao == "carga":
        linhas[0]["carga"] = "outra"
    elif alteracao.startswith("semente"):
        original = linhas[0]["semente_carga"]
        assert int(original) > 2**53  # Regressão: nunca passar sementes por float.
        linhas[0]["semente_carga"] = {
            "semente": str(int(original) + 1), "semente_float": original + ".0",
            "semente_arredondada": str(int(float(original))),
        }[alteracao]
    elif alteracao == "ambiente":
        linhas[0]["sqlite_version"] = "outro"
    elif alteracao == "coluna_ausente":
        colunas.remove("synchronous")
    elif alteracao == "coluna_duplicada":
        colunas.append("synchronous")
    elif alteracao == "coluna_extra":
        colunas.append("extra")
    salvar(coleta, linhas, colunas)
    if alteracao == "valor_extra":
        with (coleta / "resultados.csv").open("a", encoding="utf-8") as arquivo:
            arquivo.write("," * 28 + "extra\n")
    relatorio = validar(coleta)
    assert relatorio["status"] == "reprovada"
    assert codigo in {e["codigo"] for e in relatorio["erros"]}
    assert "integridade" in {e["codigo"] for e in relatorio["erros"]}
    assert relatorio["outliers"] == []


@pytest.mark.parametrize("nome,conteudo,codigo", [
    ("ambiente.json", "[]", "arquivo"),
    ("execucao.json", "null", "arquivo"),
    ("conferencia.json", '{"sha256_artefatos": []}', "integridade"),
    ("ambiente.json", "{", "arquivo"),
    ("execucao.json", '{"status": "falhou", "codigo_saida": 1}', "execucao"),
    ("lancador.py", "alterado", "integridade"),
])
def test_metadados_invalidos_retornam_erros(coleta, nome, conteudo, codigo):
    (coleta / nome).write_text(conteudo, encoding="utf-8")
    relatorio = validar(coleta)
    assert relatorio["status"] == "reprovada"
    assert codigo in {e["codigo"] for e in relatorio["erros"]}


def test_arquivo_ausente_e_falha_nao_deixam_publicacao_aprovada(coleta):
    saida = coleta / "validacao"
    assert main(["--diretorio", str(coleta)]) == 0
    (coleta / "resultados.csv").unlink()
    assert main(["--diretorio", str(coleta)]) == 1
    manifesto = json.loads((saida / "manifesto.json").read_text(encoding="utf-8"))
    assert manifesto["status"] == "reprovada"
    assert manifesto["publicado_para_analise_exploratoria"] is False
    with (saida / "outliers.csv").open(encoding="utf-8", newline="") as arquivo:
        assert list(csv.DictReader(arquivo)) == []


@pytest.mark.parametrize("alvo", ["mesmo", "pai"])
def test_saida_nao_pode_sobrescrever_entradas(coleta, alvo):
    with pytest.raises(ValueError, match="saída"):
        publicar(coleta, coleta if alvo == "mesmo" else coleta.parent)


def test_outliers_iqr_zero_preservados_e_diferencas_pareadas():
    linhas = []
    for ordem, e in enumerate(plano_execucoes(30, 3, 42), 1):
        if e.aquecimento:
            continue
        tempo = 100 if e.repeticao == 30 else 1
        linhas.append({
            "linha_csv": len(linhas) + 2, "ordem_execucao": ordem,
            "configuracao": e.configuracao.nome, "carga": e.carga.nome,
            "repeticao": e.repeticao, "tempo_total_s": tempo,
            "vazao_ops_s": e.carga.n_operacoes / tempo,
        })
    copia = [l.copy() for l in linhas]
    contagens, outliers, temporal = diagnosticar(linhas, "sintetica")
    assert len(contagens) == 12
    assert len(outliers) == 24  # Mesmas 12 execuções sinalizadas em M1 e M2.
    assert {o["repeticao"] for o in outliers} == {30}
    assert {o["iqr"] for o in outliers} == {0}
    assert {o["acao"] for o in outliers} == {"preservar"}
    assert linhas == copia
    pareadas = [t for t in temporal if t["serie"] == "diferenca_pareada"]
    assert len(pareadas) == 9
    assert {t["mediana_primeira_metade"] for t in pareadas} == {0}
    assert {t["correlacao_lag1"] for t in pareadas} == {None}


def test_diagnostico_temporal_valores_conhecidos_e_empates():
    resultado = diagnostico_temporal(
        list(range(1, 31)), list(range(1, 31)), serie="teste", carga="teste",
        nome="teste", metrica="teste",
    )
    assert resultado["spearman_ordem"] == pytest.approx(1)
    assert resultado["correlacao_lag1"] == pytest.approx(1)
    assert resultado["mediana_primeira_metade"] == 8
    assert resultado["mediana_segunda_metade"] == 23
    assert resultado["diferenca_entre_metades"] == 15
    from experimento.validacao import _postos
    assert _postos([3, 1, 1, 2]) == [4, 1.5, 1.5, 3]


def test_quartis_inclusivos_e_sentido_das_comparacoes_pareadas():
    linhas = []
    indices = {c.nome: i for i, c in enumerate(config.CONFIGURACOES)}
    for ordem, e in enumerate(plano_execucoes(30, 3, 42), 1):
        if e.aquecimento:
            continue
        linhas.append({
            "linha_csv": len(linhas) + 2, "ordem_execucao": ordem,
            "configuracao": e.configuracao.nome, "carga": e.carga.nome,
            "repeticao": e.repeticao,
            "tempo_total_s": 100 if e.repeticao == 30 else e.repeticao,
            "vazao_ops_s": 1000 * indices[e.configuracao.nome] + e.repeticao,
        })
    # Desordena as entradas para que a ordem de leitura não crie pares falsos.
    _, outliers, temporal = diagnosticar(list(reversed(linhas)), "sintetica")
    assert len(outliers) == 12
    for o in outliers:
        assert o["metrica"] == "tempo_total_s"
        assert o["q1"] == 8.25
        assert o["q3"] == 22.75
        assert o["iqr"] == 14.5
        assert o["limite_superior"] == 44.5
        assert o["valor"] == 100
    for t in temporal:
        if t["serie"] == "diferenca_pareada":
            esperado = 2000 if t["configuracao_ou_comparacao"] == "H1" else 1000
            assert t["mediana_primeira_metade"] == esperado
            assert t["mediana_segunda_metade"] == esperado
