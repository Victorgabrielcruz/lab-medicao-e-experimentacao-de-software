import json
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from experimento import config

APP = Path(__file__).resolve().parents[1] / "app.py"
PILOTO = config.DIR_DADOS / "piloto"
SECOES_ESPERADAS = [
    "1. Software", "2. Pergunta de pesquisa", "3. Método", "4. Resultados",
    "5. Ameaças à validade", "6. Impacto para empresas e usuários",
]


def executar():
    app = AppTest.from_file(str(APP)).run(timeout=30)
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
    app = executar()
    bruto = pd.read_csv(PILOTO / "resultados.csv")
    assert app.metric[0].value == str(len(bruto))
    tabela = app.dataframe[0].value
    assert len(tabela) == 12
    for _, linha in tabela.iterrows():
        grupo = bruto[(bruto.configuracao == linha["Configuração"]) & (bruto.carga == linha["Carga"])]
        assert linha["n"] == len(grupo) == 3
        assert linha["Mediana M1 (s)"] == pytest.approx(grupo.tempo_total_s.median())
        assert linha["Mediana M2 (ops/s)"] == pytest.approx(grupo.vazao_ops_s.median())
    pd.testing.assert_frame_equal(app.dataframe[1].value, bruto)
    assert any("não respondem às hipóteses" in w.value for w in app.warning)
    assert all(p.read_bytes() == conteudo for p, conteudo in originais.items())


def test_grafico_muda_com_a_carga_e_preserva_todas_as_observacoes():
    app = executar()
    app.selectbox[0].select("mista").run()
    assert not app.exception
    figura = json.loads(app.get("plotly_chart")[0].proto.spec)
    assert "mista" in figura["layout"]["title"]["text"]
    assert sum(len(t["x"]) for t in figura["data"]) == 12


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
