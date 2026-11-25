import json
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from experimento import benchmark, config

APP = Path(__file__).resolve().parents[1] / "app.py"
PILOTO = config.DIR_DADOS / "piloto"
COMPLETA = config.DIR_DADOS / "coleta-completa-01"
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


def test_dashboard_usa_coleta_completa_por_padrao_sem_alterar_artefatos(monkeypatch):
    originais = {p: p.read_bytes() for pasta in (PILOTO, COMPLETA) for p in pasta.rglob("*") if p.is_file()}
    # O resumo publicado não deve substituir a leitura das medições brutas.
    read_text = Path.read_text

    def sem_resumo_publicado(caminho, *args, **kwargs):
        assert caminho.name not in {"resumo.csv", "resumo.json"}
        return read_text(caminho, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", sem_resumo_publicado)
    monkeypatch.setattr(benchmark, "coletar", lambda *a, **k: pytest.fail("Dashboard iniciou uma coleta"))
    app = executar()
    bruto = pd.read_csv(COMPLETA / "resultados.csv")
    assert app.selectbox(key="coleta").value == "Coleta completa"
    assert app.metric[0].value == str(len(bruto)) == "360"
    assert app.metric[2].value == "30"
    tabela = app.dataframe[0].value
    assert len(tabela) == 4
    for _, linha in tabela.iterrows():
        grupo = bruto[(bruto.configuracao == linha["Configuração"]) & (bruto.carga == "escrita")]
        assert linha["n"] == len(grupo) == 30
        assert linha["Mediana"] == pytest.approx(grupo.tempo_total_s.median())
    pd.testing.assert_frame_equal(app.dataframe[2].value, bruto[bruto.carga == "escrita"])
    assert "23 observações sinalizadas" in app.success[0].value
    assert "Nenhuma exclusão" in app.success[0].value
    assert not app.warning
    todas = app.dataframe[3].value
    assert len(todas) == 24
    assert set(todas["n"]) == {30}
    assert todas.groupby("Métrica")["n"].sum().tolist() == [360, 360]
    assert all(p.read_bytes() == conteudo for p, conteudo in originais.items())


@pytest.mark.parametrize("carga", ["escrita", "leitura", "mista"])
@pytest.mark.parametrize("metrica,coluna", [("Tempo total (M1)", "tempo_total_s"), ("Vazão (M2)", "vazao_ops_s")])
@pytest.mark.parametrize("fonte,pasta,n", [("Coleta completa", COMPLETA, 120), ("Piloto", PILOTO, 12)])
def test_filtros_atualizam_graficos_tabelas_e_comparacoes(carga, metrica, coluna, fonte, pasta, n):
    app = executar()
    app.selectbox(key="coleta").select(fonte)
    app.selectbox(key="carga").select(carga)
    app.selectbox(key="metrica").select(metrica).run()
    assert not app.exception
    bruto = pd.read_csv(pasta / "resultados.csv")
    bruto = bruto[bruto.carga == carga]
    figuras = [json.loads(g.proto.spec) for g in app.get("plotly_chart")]
    assert len(figuras) == 4
    assert all(carga in f["layout"]["title"]["text"] for f in figuras)
    assert sum(len(t["y"][0]) for t in figuras[0]["data"]) == n
    for trace in figuras[0]["data"]:
        esperado = bruto[bruto.configuracao == trace["name"]][coluna].tolist()
        assert trace["y"][0] == pytest.approx(esperado)
        assert trace["q1"] == pytest.approx([bruto[bruto.configuracao == trace["name"]][coluna].quantile(0.25)])
        assert trace["q3"] == pytest.approx([bruto[bruto.configuracao == trace["name"]][coluna].quantile(0.75)])
    resumo_grafico = figuras[1]["data"][0]
    for indice, cfg in enumerate(resumo_grafico["x"]):
        valores = bruto[bruto.configuracao == cfg][coluna]
        mediana = valores.median()
        assert resumo_grafico["y"][indice] == pytest.approx(mediana)
        assert resumo_grafico["error_y"]["array"][indice] == pytest.approx(valores.quantile(0.75) - mediana)
        assert resumo_grafico["error_y"]["arrayminus"][indice] == pytest.approx(mediana - valores.quantile(0.25))
    for trace in figuras[2]["data"]:
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
    assert [f["layout"]["yaxis"]["type"] for f in figuras] == ["log", "log", "log", "linear"]


def test_conteudo_documental_e_ambiente_da_coleta():
    app = executar()
    texto = "\n".join(m.value for m in app.markdown)
    for trecho in ("Como usar esta evidência", "Alcance dos resultados", "Holm", "bootstrap", "GQM"):
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


@pytest.mark.parametrize("fonte,pasta,nome", [("Coleta completa", COMPLETA, "coleta-completa-01"), ("Piloto", PILOTO, "piloto")])
@pytest.mark.parametrize("falha", ["ausente", "csv_invalido"])
def test_falha_da_coleta_mantem_roteiro_sem_troca_silenciosa(tmp_path, monkeypatch, falha, fonte, pasta, nome):
    if falha == "csv_invalido":
        import shutil
        shutil.copytree(pasta, tmp_path / nome)
        (tmp_path / nome / "resultados.csv").write_text("configuracao,carga\n", encoding="utf-8")
    monkeypatch.setattr(config, "DIR_DADOS", tmp_path)
    app = executar()
    app.selectbox(key="coleta").select(fonte).run(timeout=60)
    assert not app.exception
    assert [h.value for h in app.header] == SECOES_ESPERADAS
    assert len(app.error) == 1
    assert f"Não foi possível ler {fonte.lower()}" in app.error[0].value
    assert not app.metric
