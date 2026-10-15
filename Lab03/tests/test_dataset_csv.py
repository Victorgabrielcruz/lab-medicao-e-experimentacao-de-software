import copy
import csv
import hashlib
import io
import json
from pathlib import Path
import pytest
import yaml
from pipeline import dataset_csv as csvmod, amostra_encerrada
from pipeline.config import ConfigError
from pipeline.metricas import METRICAS
from test_integrado import configurar, Api
from pipeline import integrado

def documentos():
    janela = {"inicio": "2025-10-01T00:00:00Z", "fim_exclusivo": "2026-10-01T00:00:00Z"}
    meta = {"id": 1, "full_name": "org/répo", "estrelas": 0, "linguagem": None,
            "created_at": "2020-01-01T00:00:00+00:00", "idade_dias": 2100, "idade_anos": 5.75,
            "default_branch": "main", "contribuidores": None, "contribuidores_obs": 'texto,"linha"\nsegunda',
            "coletado_em": "2026-10-15T15:00:00-03:00"}
    r = {"id": 1, "full_name": meta["full_name"], "coleta_incompleta": True, "calculo_parcial": True,
         **{k: None for m in METRICAS for k in (m, f"classe_{m}")}}
    r.update(deployment_frequency=0.0, classe_deployment_frequency="Low", cfr_a=0.0, classe_cfr_a="Elite")
    r["metricas_ausentes"] = [m for m in METRICAS if r[m] is None]
    p = {"janela": janela, "repositorios": [{"id": 1, "full_name": meta["full_name"], "deployment_frequency": 0.0, "classe": "Low"}]}
    return p, {"repositorios": [meta]}, {"janela": janela, "repositorios": [r]}

def test_csv_nulos_zero_utf8_listas_e_determinismo():
    docs = documentos()
    linhas = csvmod.montar_linhas(*docs)
    saida = csvmod.serializar(linhas)
    row = list(csv.DictReader(io.StringIO(saida.decode("utf-8"))))[0]
    assert len(row) == len(csvmod.COLUNAS) == 28
    assert row["cfr_a"] == "0.0" and row["cfr_b"] == ""
    assert row["linguagem"] == row["contribuidores"] == ""
    assert row["contribuidores_obs"] == docs[1]["repositorios"][0]["contribuidores_obs"]
    assert json.loads(row["metricas_ausentes"]) == linhas[0]["metricas_ausentes"]
    assert row["coleta_incompleta"] == "true" and row["calculo_parcial"] == "true"
    assert row["coletado_em"] == "2026-10-15T18:00:00Z"
    assert saida == csvmod.serializar(csvmod.montar_linhas(*copy.deepcopy(docs)))

@pytest.mark.parametrize("idx", [0,1,2])
def test_duplicata_falha(idx):
    docs = documentos()
    docs[idx]["repositorios"] *= 2
    with pytest.raises(ConfigError, match="duplicado"):
        csvmod.montar_linhas(*docs)

@pytest.mark.parametrize("idx", [0,1,2])
def test_nome_divergente_falha(idx):
    docs = documentos()
    docs[idx]["repositorios"][0]["full_name"] = "org/outro"
    with pytest.raises(ConfigError, match="Identidade"):
        csvmod.montar_linhas(*docs)

def test_janela_divergente():
    docs = documentos()
    docs[0]["janela"] = {}
    with pytest.raises(ConfigError, match="Janela"):
        csvmod.montar_linhas(*docs)

@pytest.mark.parametrize("campo,valor", [("cfr_a",float("nan")), ("cfr_a",1.1), ("classe_cfr_b","Low"),
                                         ("coleta_incompleta",1), ("metricas_ausentes",[])])
def test_contrato_valores_invalidos(campo,valor):
    docs = documentos()
    docs[2]["repositorios"][0][campo] = valor
    with pytest.raises(ConfigError):
        csvmod.montar_linhas(*docs)

def test_metadados_pendentes_e_populacao():
    docs = documentos()
    docs[1]["repositorios"][0]["contribuidores_pendentes"] = True
    with pytest.raises(ConfigError, match="pendentes"):
        csvmod.montar_linhas(*docs)
    docs = documentos()
    docs[2]["repositorios"] = []
    with pytest.raises(ConfigError, match="Populacao"):
        csvmod.montar_linhas(*docs)

def test_ordem_por_id():
    docs = documentos()
    for d in docs:
        novo = {**copy.deepcopy(d["repositorios"][0]), "id": 2, "full_name": "a/primeiro"}
        d["repositorios"].insert(0,novo)
    assert [r["id"] for r in csvmod.montar_linhas(*docs)] == [1,2]

def test_exportacao_gravada_repetivel_e_protege_entradas(tmp_path):
    p,m,r = documentos()
    raw,proc = tmp_path/"raw",tmp_path/"processed"
    raw.mkdir(); proc.mkdir()
    for f,d in ((raw/"metadados.json",m),(proc/"metricas.json",r),(proc/"deployment_frequency.json",p)):
        f.write_text(json.dumps(d),encoding="utf-8")
    c,manifesto = tmp_path/"csv/a.csv",tmp_path/"csv/manifesto.json"
    resumo = csvmod.exportar(raw,proc,c,manifesto)
    bytes_antes = c.read_bytes(),manifesto.read_bytes()
    assert csvmod.exportar(raw,proc,c,manifesto) == resumo
    assert bytes_antes == (c.read_bytes(),manifesto.read_bytes())
    assert resumo["csv_sha256"] == hashlib.sha256(c.read_bytes()).hexdigest()
    with pytest.raises(ConfigError,match="fora"):
        csvmod.exportar(raw,proc,raw/"csv.csv",manifesto)
    with pytest.raises(ConfigError,match="diferentes"):
        csvmod.exportar(raw,proc,c,c)

@pytest.mark.parametrize("n_compares", [0,1,2])
def test_reconstrucao_encerrada_sem_compare_nao_fabrica_dados(tmp_path,monkeypatch,n_compares):
    cfg,fonte = configurar(tmp_path,n=2)
    integrado.executar(cfg,Api(),alvo=2,max_candidatos=2,fonte=fonte)
    raw = Path(cfg["caminhos"]["raw"])
    (raw/"config.yaml").write_text(yaml.safe_dump(cfg),encoding="utf-8")
    p = json.loads((raw/"progresso.json").read_text(encoding="utf-8"))
    cp_files = list(raw.glob("checkpoints/*/*.json"))
    locais = sorted(raw.glob("checkpoints/compare/*/*.json"))[:n_compares]
    com_compare = {json.loads(p.read_text(encoding="utf-8"))["id"] for p in locais}
    hashes = {f.relative_to(raw).as_posix():hashlib.sha256(f.read_bytes()).hexdigest()
              for f in [raw/"progresso.json",raw/"config.yaml",*cp_files,*locais]}
    autoridade = {"snapshot":str(raw),"origem":str(raw),"coleta_externa_encerrada":True,
                  "novas_consultas_api_autorizadas":False,"contexto":p["contexto"],
                  "contexto_sha256":cp_files[0].parent.name,"ids_amostra":[1,2],
                  "total_amostra":2,"candidatos_avaliados":2,"arquivos_sha256":hashes,
                  "encerrado_utc":"2026-10-15T18:09:11+00:00","decisao":"Excecao humana",
                  "meta_original":500,"minimo_original":300}
    a = tmp_path/"encerramento.json"
    a.write_text(json.dumps(autoridade),encoding="utf-8")
    def sem_api(*args,**kwargs):
        pytest.fail("A reconstrucao nao pode acessar rede")
    monkeypatch.setattr("requests.sessions.Session.request",sem_api)
    out = tmp_path/"offline"
    result = amostra_encerrada.executar(a,out)
    assert result["consolidacao_offline_completa"] and not result["execucao_completa"]
    assert result["repositorios_sem_compare"] == 2-n_compares
    assert len(json.loads((out/"raw/compare.json").read_text(encoding="utf-8"))["repositorios"]) == n_compares
    rows = json.loads((out/"processed/metricas.json").read_text(encoding="utf-8"))["repositorios"]
    assert all(r["lead_time_a"] is None and r["lead_time_b"] is None and r["cfr_b"] is None
               and r["coleta_incompleta"] and r["calculo_parcial"] for r in rows if r["id"] not in com_compare)
    assert all(r["lead_time_a"] is not None and r["lead_time_b"] is not None for r in rows if r["id"] in com_compare)
    assert all(hashlib.sha256((raw/k).read_bytes()).hexdigest()==v for k,v in hashes.items())
    with pytest.raises(ConfigError, match="ja existe"):
        amostra_encerrada.executar(a,out)


def test_funil_exclui_runs_incompletos_sem_incluir_novos_ids():
    funil = {"amostra": [{"id":1,"full_name":"o/a","coleta_runs_incompleta":False},
                         {"id":2,"full_name":"o/b","coleta_runs_incompleta":True}],
             "etapas":[],"descartes":[]}
    resultado = amostra_encerrada.finalizar_funil(copy.deepcopy(funil),[1])
    assert resultado["total_amostra"] == 1
    assert resultado["etapas"][-1]["descartados"] == 1
    assert resultado["descartes"][0]["motivo"] == "coleta_runs_incompleta"
    with pytest.raises(ConfigError,match="oficial"):
        amostra_encerrada.finalizar_funil(copy.deepcopy(funil),[1,2])
