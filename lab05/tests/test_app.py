import json
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from experimento import benchmark, config

APP = Path(__file__).resolve().parents[1] / "app.py"
PILOTO = config.DIR_DADOS / "piloto"
SECOES_ESPERADAS = [
    "1. Software", "2. Pergunta de pesquisa", "3. Método", "4. Resultados",
    "5. Ameaças à validade", "6. Impacto para empresas e usuários",
]


def executar():
    app = AppTest.from_file(str(APP)).run(timeout=60)
    assert not app.exception
    return app


def test_secoes_na_ordem_do_documento_final_fora_do_diretorio_do_app(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert [h.value for h in executar().header] == SECOES_ESPERADAS


def test_dashboard_le_csv_bruto_e_recalcula_estatisticas_sem_alterar_piloto(monkeypatch):
    originais = {p: p.read_bytes() for p in PILOTO.iterdir() if p.is_file()}
    # O resumo publicado não deve substituir a leitura das medições brutas.
    read_text = Path.read_text

    def sem_resumo_publicado(caminho, *args, **kwargs):
        assert caminho.name not in {"resumo.csv", "resumo.json"}
        return read_text(caminho, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", sem_resumo_publicado)
    monkeypatch.setattr(benchmark, "coletar", lambda *a, **k: pytest.fail("Dashboard iniciou uma coleta"))
    app = executar()
    bruto = pd.read_csv(PILOTO / "resultados.csv")
    assert app.metric[0].value == str(len(bruto))
    tabela = app.dataframe[0].value
    assert len(tabela) == 4
    for _, linha in tabela.iterrows():
        grupo = bruto[(bruto.configuracao == linha["Configuração"]) & (bruto.carga == "escrita")]
        assert linha["n"] == len(grupo) == 3
        assert linha["Mediana"] == pytest.approx(grupo.tempo_total_s.median())
    pd.testing.assert_frame_equal(app.dataframe[2].value, bruto[bruto.carga == "escrita"])
    assert any("não respondem às hipóteses" in w.value for w in app.warning)
    assert all(p.read_bytes() == conteudo for p, conteudo in originais.items())


@pytest.mark.parametrize("carga", ["escrita", "leitura", "mista"])
@pytest.mark.parametrize("metrica,coluna", [("Tempo total (M1)", "tempo_total_s"), ("Vazão (M2)", "vazao_ops_s")])
def test_filtros_atualizam_graficos_tabelas_e_comparacoes(carga, metrica, coluna):
    app = executar()
    app.selectbox(key="carga").select(carga)
    app.selectbox(key="metrica").select(metrica).run()
    assert not app.exception
    bruto = pd.read_csv(PILOTO / "resultados.csv")
    bruto = bruto[bruto.carga == carga]
    figuras = [json.loads(g.proto.spec) for g in app.get("plotly_chart")]
    assert len(figuras) == 3
    assert all(carga in f["layout"]["title"]["text"] for f in figuras)
    assert sum(len(t["y"]) for t in figuras[0]["data"]) == 12
    for trace in figuras[0]["data"]:
        esperado = bruto[bruto.configuracao == trace["name"]][coluna].tolist()
        assert trace["y"] == pytest.approx(esperado)
    for trace in figuras[1]["data"]:
        assert trace["x"] == ["DELETE", "WAL"]
        for journal, mediana in zip(trace["x"], trace["y"]):
            grupo = bruto[(bruto.journal_mode == journal) & (bruto.synchronous == trace["name"])]
            assert mediana == pytest.approx(grupo[coluna].median())
    assert app.dataframe[2].value.carga.unique().tolist() == [carga]
    for _, linha in app.dataframe[0].value.iterrows():
        assert linha["Mediana"] == pytest.approx(bruto[bruto.configuracao == linha["Configuração"]][coluna].median())
    for _, linha in app.dataframe[1].value.iterrows():
        trat = bruto[bruto.configuracao == linha["Tratamento"]].vazao_ops_s.median()
        ref = bruto[bruto.configuracao == linha["Referência"]].vazao_ops_s.median()
        assert linha["M3 (×)"] == pytest.approx(trat / ref)


def test_escala_logaritmica_atualiza_distribuicao_e_interacao():
    app = executar()
    app.toggle(key="logaritmica").set_value(True).run()
    assert not app.exception
    figuras = [json.loads(g.proto.spec) for g in app.get("plotly_chart")]
    assert [f["layout"]["yaxis"]["type"] for f in figuras] == ["log", "log", "linear"]


def test_conteudo_documental_e_ambiente_da_coleta():
    app = executar()
    texto = "\n".join(m.value for m in app.markdown)
    for trecho in ("Como usar esta evidência", "Conclusão do piloto", "Holm", "bootstrap", "GQM"):
        assert trecho in texto
    tabelas = [t.value for t in app.table]
    ambiente = next(t for t in tabelas if "Item" in t.columns)
    assert dict(zip(ambiente.Item, ambiente.Valor))["Python da coleta"] == "3.12.14"
    categorias = next(t for t in tabelas if "Categoria" in t.columns)
    assert len(categorias) == 7
    ameacas = next(t for t in tabelas if "Validade" in t.columns)
    assert set(ameacas.Validade) == {"Interna", "Externa", "Construto", "Conclusão"}
    navegacao = "\n".join(m.value for m in app.sidebar.markdown)
    assert all(f"#{ancora}" in navegacao for ancora in ("software", "pergunta", "metodo", "resultados", "ameacas", "impacto"))


@pytest.mark.parametrize("falha", ["ausente", "csv_invalido"])
def test_falha_do_piloto_mantem_roteiro_completo(tmp_path, monkeypatch, falha):
    if falha == "csv_invalido":
        (tmp_path / "piloto").mkdir()
        for nome in ("ambiente.json", "execucao.json"):
            (tmp_path / "piloto" / nome).write_bytes((PILOTO / nome).read_bytes())
        (tmp_path / "piloto" / "resultados.csv").write_text("configuracao,carga\n", encoding="utf-8")
    monkeypatch.setattr(config, "DIR_DADOS", tmp_path)
    app = executar()
    assert [h.value for h in app.header] == SECOES_ESPERADAS
    assert len(app.error) == 1
    assert "Não foi possível ler o piloto" in app.error[0].value
