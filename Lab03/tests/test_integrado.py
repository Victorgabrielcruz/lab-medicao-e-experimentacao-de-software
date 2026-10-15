import copy
import datetime as dt
import json
from pathlib import Path
import pytest
import requests
from pipeline import integrado, releases, workflow_runs_completos as completos
from pipeline.cache import gravar_json
from pipeline.config import ConfigError, load_config

CONFIG = Path(__file__).resolve().parents[1] / "config.yaml"
INICIO = dt.datetime(2025, 10, 1, tzinfo=dt.timezone.utc)
FIM = dt.datetime(2025, 11, 1, tzinfo=dt.timezone.utc)


def run(i, data=None):
    return {"id": i + 1, "workflow_id": 7, "head_branch": "main", "event": "push",
            "created_at": data or (INICIO + dt.timedelta(minutes=i)).isoformat(),
            "run_started_at": data or (INICIO + dt.timedelta(minutes=i)).isoformat(),
            "updated_at": data or (INICIO + dt.timedelta(minutes=i)).isoformat(),
            "conclusion": "failure" if i == 1 else "success"}


def resposta(corpo, link=None):
    r = requests.Response()
    r.status_code = 200
    r._content = json.dumps(corpo).encode()
    if link:
        r.headers["Link"] = f'<{link}>; rel="next"'
    return r


class Api:
    def __init__(self, excluidos=0, nruns=50, falhar=None):
        self.chamadas = []
        self.excluidos = excluidos
        self.nruns = nruns
        self.falhar = falhar

    def get_resposta(self, path, params=None):
        self.chamadas.append((path, params))
        n = int(path.split("/")[3].removeprefix("repo"))
        if self.falhar == n:
            raise requests.ConnectionError("interrupção simulada")
        if "/compare/" in path:
            return resposta({"status": "ahead", "total_commits": 1,
                             "commits": [{"sha": f"sha-{path.rsplit('/', 1)[-1]}",
                                          "commit": {"author": {"date": "2025-10-01T00:00:00Z"}}}]})
        if path.endswith("/releases"):
            return resposta([{"id": i, "draft": False, "prerelease": i == 0,
                               "published_at": "2025-10-10T00:00:00Z", "tag_name": f"v{i}"}
                              for i in range(3 if n <= self.excluidos else 6)])
        if path.endswith("/contributors"):
            return resposta([])
        return resposta({"id": n, "full_name": f"org/repo{n}", "default_branch": "main",
                         "stargazers_count": 1000, "created_at": "2020-01-01T00:00:00Z"})

    def get(self, path, params=None):
        if path.endswith("/actions/workflows"):
            self.chamadas.append((path, params))
            return {"total_count": 1, "workflows": [{"path": ".github/workflows/ci.yml"}]}
        if path.endswith("/actions/runs"):
            self.chamadas.append((path, params))
            a, b = [dt.datetime.fromisoformat(x.replace("Z", "+00:00"))
                    for x in params["created"].split("..")]
            lista = [run(i) for i in range(self.nruns)
                     if a <= dt.datetime.fromisoformat(run(i)["created_at"]) <= b]
            page = params["page"]
            return {"total_count": len(lista), "workflow_runs": lista[(page-1)*100:page*100]}
        return self.get_resposta(path, params).json()


def configurar(tmp_path, n=120):
    cfg = load_config(CONFIG)
    # Os cenários legados exercitam a execução sequencial; concorrência abaixo
    # tem cenários próprios com conclusão fora de ordem e falhas simultâneas.
    cfg["api"]["repositorios_paralelos"] = 1
    cfg["caminhos"] = {k: str(tmp_path / k) for k in ("raw", "processed", "cache")}
    fonte = tmp_path / "fonte.json"
    gravar_json(fonte, {"candidatos": [{"id": i, "full_name": f"org/repo{i}"} for i in range(1, n+1)]})
    return cfg, fonte


def test_100_elegiveis_nao_100_candidatos_e_retomada_sem_api(tmp_path):
    cfg, fonte = configurar(tmp_path)
    api = Api(excluidos=20)
    original = fonte.read_bytes()
    result = integrado.executar(cfg, api, 100, 120, fonte)
    assert result["execucao_completa"]
    assert result["candidatos_avaliados"] == 120
    assert result["total_amostra_completa"] == 100
    assert result["total_comparacoes"] == 400
    assert result["releases_compare_ignoradas"] == 100
    assert result["coletas_compare_incompletas"] == 0
    assert result["repositorios_com_lead_time_release"] == 100
    lead = json.loads((tmp_path / "processed/lead_time_release.json").read_text(encoding="utf-8"))
    assert lead["releases_com_lead_time"] == 400
    assert lead["repositorios"][0]["lead_time_horas"] == 216
    assert result["dependencias_pendentes"] == ["CFR (b) #161"]
    assert result["metricas"] == ["deployment_frequency", "lead_time_a", "lead_time_b", "cfr_a", "tempo_recuperacao"]
    todas = json.loads((tmp_path / "processed/metricas.json").read_text(encoding="utf-8"))
    assert todas["total_repositorios"] == 100
    assert todas["variantes_pendentes"] == ["cfr_b"]
    assert todas["repositorios_por_metrica"] == {"deployment_frequency": 100, "lead_time_a": 100, "lead_time_b": 100,
                                                 "cfr_a": 100, "cfr_b": 0, "tempo_recuperacao": 100}
    primeiro = todas["repositorios"][0]
    assert (primeiro["lead_time_a"], primeiro["lead_time_b"], primeiro["cfr_a"]) == (216, 216, 1/50)
    assert primeiro["metricas_ausentes"] == ["cfr_b"]
    compares = json.loads((tmp_path / "raw/compare.json").read_text(encoding="utf-8"))
    assert compares["total_repositorios"] == 100
    assert compares["total_comparacoes"] == 400
    assert not any("repo1/compare/" in p for p, _ in api.chamadas)
    assert fonte.read_bytes() == original
    assert not any("repo1/actions/runs" in p for p, _ in api.chamadas)
    cfr = json.loads((tmp_path / "processed/cfr.json").read_text(encoding="utf-8"))
    assert cfr["total_repositorios"] == 100
    assert cfr["repositorios"][0]["change_failure_rate"] == 1/50
    recuperacao = json.loads((tmp_path / "processed/tempo_recuperacao.json").read_text(encoding="utf-8"))
    assert recuperacao["total_episodios"] == 100
    assert recuperacao["episodios_censurados"] == 0
    api2 = Api(falhar=21)
    assert integrado.executar(cfg, api2, 100, 120, fonte)["execucao_completa"]
    assert not api2.chamadas


def test_amostra_insuficiente_nao_declara_sucesso(tmp_path):
    cfg, fonte = configurar(tmp_path, 3)
    r = integrado.executar(cfg, Api(excluidos=2), 2, 3, fonte)
    assert r["total_amostra_completa"] == 1 and not r["execucao_completa"]


def test_runs_ficam_nos_checkpoints_e_os_consolidados_sao_gravados_por_linha(tmp_path, monkeypatch):
    from pipeline import consolidado, funil
    cfg, fonte = configurar(tmp_path, 6)
    recebidos = []
    montar = funil.montar_funil
    monkeypatch.setattr(funil, "montar_funil", lambda dados, *a, **k: recebidos.append(dados) or montar(dados, *a, **k))
    assert integrado.executar(cfg, Api(excluidos=2), 3, 6, fonte)["execucao_completa"]
    na_memoria = recebidos[0]["workflow_runs"]["repositorios"]
    assert len(na_memoria) == 3 and all("workflow_runs" not in r for r in na_memoria)
    assert all(r["resumo_runs"]["runs_validos"] == 50 and r["total_runs"] == 50 for r in na_memoria)
    for nome, total in (("workflow_runs.json", 3), ("amostra_workflow_runs.json", 3)):
        caminho = tmp_path / "raw" / nome
        assert caminho.read_bytes().count(b"\n") == total + 2
        lido = json.loads(caminho.read_text(encoding="utf-8"))
        assert lido["janela"] == recebidos[0]["workflow_runs"]["janela"]
        assert [len(r["workflow_runs"]) for r in lido["repositorios"]] == [50] * total
        assert all("resumo_runs" not in r for r in lido["repositorios"])
        assert list(consolidado.repositorios(caminho)) == lido["repositorios"]
    bruto = json.loads((tmp_path / "raw/workflow_runs.json").read_text(encoding="utf-8"))
    assert list(bruto) == ["janela", "repositorios", "descartes"] and len(bruto["descartes"]) == 2


def test_funil_integrado_e_igual_ao_funil_montado_com_os_runs_completos(tmp_path):
    from pipeline import funil
    cfg, fonte = configurar(tmp_path, 8)
    integrado.executar(cfg, Api(excluidos=3, nruns=60), 4, 8, fonte)
    gravado = json.loads((tmp_path / "processed/funil.json").read_text(encoding="utf-8"))
    completos_ = {nome: funil._ler(tmp_path / "raw", arquivo, nome) for nome, _, arquivo, _ in integrado.ETAPAS}
    assert all(len(r["workflow_runs"]) == 60 for r in completos_["workflow_runs"]["repositorios"])
    assert funil.montar_funil(completos_, cfg, integrado.ETAPAS) == gravado
    assert [r["runs_validos"] for r in gravado["amostra"]] == [60] * 4


def test_auditoria_usa_o_hash_do_arquivo_inteiro(tmp_path):
    import hashlib
    cfg, fonte = configurar(tmp_path, 2)
    integrado.executar(cfg, Api(), 2, 2, fonte)
    entrada = tmp_path / "raw/amostra_workflow_runs.json"
    registro = json.loads((tmp_path / "processed/auditoria.json").read_text(encoding="utf-8"))
    assert registro["entrada_sha256"] == hashlib.sha256(entrada.read_bytes()).hexdigest()
    assert registro["total_repositorios"] == 2 and registro["runs_no_recorte_deduplicados"] == 100


def test_interrupcao_preserva_checkpoint_e_retomada(tmp_path):
    cfg, fonte = configurar(tmp_path, 3)
    with pytest.raises(requests.ConnectionError):
        integrado.executar(cfg, Api(falhar=2), 3, 3, fonte)
    assert len(list((tmp_path / "raw/checkpoints").glob("*/*.json"))) == 1
    api = Api()
    assert integrado.executar(cfg, api, 3, 3, fonte)["execucao_completa"]
    assert all(p.endswith("/releases") or "/compare/" in p
               for p, _ in api.chamadas if "repo1/" in p)


def test_subdivide_mes_saturado_sem_perder_runs_nas_fronteiras():
    api = Api(nruns=1100)
    fatias, lista = completos.coletar_intervalo(api, "org/repo1", "main", INICIO, FIM)
    assert len(lista) == len({r["id"] for r in lista}) == 1100
    assert fatias[0]["subdividido"] and not fatias[0]["coleta_incompleta"]
    assert all(p["event"] == "push" and p["branch"] == "main" for _, p in api.chamadas)


def test_total_api_limitado_a_2500_confere_completude_nas_folhas():
    class TotalLimitado(Api):
        def get(self, path, params=None):
            dados = super().get(path, params)
            return {**dados, "total_count": min(2500, dados["total_count"])}

    fatias, runs = completos.coletar_intervalo(TotalLimitado(nruns=3500), "org/repo1", "main", INICIO, FIM)
    mes = fatias[0]
    assert len(runs) == len({r["id"] for r in runs}) == 3500
    assert mes["total_api"] == 2500 and mes["runs_retidos"] == 3500
    assert mes["total_api_limitado"]
    assert mes["ids_pagina_inicial_ausentes"] == 0
    assert not mes["coleta_incompleta"]


def test_total_limitado_nao_esconde_paginas_ausentes():
    class TotalLimitado(Api):
        def get(self, path, params=None):
            dados = super().get(path, params)
            return {**dados, "total_count": min(2500, dados["total_count"]),
                    "workflow_runs": [] if params["page"] == 2 else dados["workflow_runs"]}

    fatias, _ = completos.coletar_intervalo(TotalLimitado(nruns=3500), "org/repo1", "main", INICIO, FIM)
    assert fatias[0]["coleta_incompleta"]


def test_subdivisao_exige_ids_da_pagina_inicial_mesmo_com_contagens_iguais():
    intervalo_pai = f"{completos.wr._iso(INICIO)}..{completos.wr._iso(FIM-dt.timedelta(seconds=1))}"

    class IdAusente(Api):
        def get(self, path, params=None):
            dados = super().get(path, params)
            if params["created"] != intervalo_pai:
                dados["workflow_runs"] = [{**r, "id": 99999} if r["id"] == 1 else r
                                          for r in dados["workflow_runs"]]
            return dados

    fatias, runs = completos.coletar_intervalo(IdAusente(nruns=1100), "org/repo1", "main", INICIO, FIM)
    assert len(runs) == 1100
    assert fatias[0]["ids_pagina_inicial_ausentes"] == 1
    assert fatias[0]["coleta_incompleta"]


def test_outros_totais_divergentes_continuam_incompletos():
    intervalo_pai = f"{completos.wr._iso(INICIO)}..{completos.wr._iso(FIM-dt.timedelta(seconds=1))}"

    class ContagemDivergente(Api):
        def get(self, path, params=None):
            dados = super().get(path, params)
            if params["created"] == intervalo_pai:
                dados["total_count"] = 1099
            return dados

    fatias, _ = completos.coletar_intervalo(ContagemDivergente(nruns=1100), "org/repo1", "main", INICIO, FIM)
    assert not fatias[0]["total_api_limitado"]
    assert fatias[0]["coleta_incompleta"]


def test_versao_coletor_invalida_checkpoint_de_selecao(tmp_path, monkeypatch):
    cfg, fonte = configurar(tmp_path, 1)
    integrado.executar(cfg, Api(), 1, 1, fonte)
    monkeypatch.setattr(completos, "VERSAO_COLETOR", completos.VERSAO_COLETOR + 1)
    api = Api()
    assert integrado.executar(cfg, api, 1, 1, fonte)["execucao_completa"]
    assert api.chamadas
    assert len(list((tmp_path / "raw/checkpoints").glob("*/1.json"))) == 2


def test_segundo_saturado_mantem_incompletude():
    class Saturada:
        def get(self, *_):
            return {"total_count": 1001, "workflow_runs": [run(0)]}
    fatias, _ = completos.coletar_intervalo(Saturada(), "org/r", "main", INICIO,
                                          INICIO + dt.timedelta(seconds=1))
    assert fatias[0]["coleta_incompleta"]


def test_releases_pagina_filtra_drafts_janela_e_deduplica():
    r = {"id": 1, "draft": False, "prerelease": True, "tag_name": "v1",
         "published_at": "2025-10-01T00:00:00Z"}
    class Paginada:
        def __init__(self):
            self.paginas = []
        def get_resposta(self, path, params):
            self.paginas.append(params["page"])
            if params["page"] == 1:
                return resposta([r, {**r, "id": 2, "draft": True},
                                  {**r, "id": 3, "published_at": "2025-09-30T23:59:59Z"}], "https://api.github.com/next?page=2")
            return resposta([r, {**r, "id": 4, "published_at": "2025-10-31T23:59:59Z"}])
    client = Paginada()
    repo = releases.coletar_repositorio(client, {"id": 1, "full_name": "org/r"}, INICIO, FIM)
    assert client.paginas == [1, 2]
    assert [r["id"] for r in repo["releases"]] == [1, 4]
    assert repo["releases"][0]["prerelease"]


def test_reutiliza_meses_completos_mas_recoleta_incompletos(tmp_path):
    cfg, _ = configurar(tmp_path, 1)
    inicio, fim = integrado.janela_utc(cfg)
    repo = {"id": 1, "full_name": "org/repo1", "default_branch": "main"}
    anterior = completos.coletar_repositorio(Api(), repo, inicio, fim)
    anterior["meses"][0]["coleta_incompleta"] = True
    api = Api()
    atual = completos.coletar_repositorio(api, repo, inicio, fim, anterior)
    assert len(api.chamadas) == 1
    assert atual["total_runs"] == 50 and not atual["coleta_incompleta"]


@pytest.mark.parametrize("alvo,limite", [(0, 1), (2, 1)])
def test_parametros_invalidos(tmp_path, alvo, limite):
    cfg, fonte = configurar(tmp_path)
    with pytest.raises(ConfigError):
        integrado.executar(cfg, Api(), alvo, limite, fonte)


def test_incompleta_nao_conta_para_alvo(tmp_path, monkeypatch):
    cfg, fonte = configurar(tmp_path, 1)
    original = completos.coletar_repositorio
    def parcial(*args, **kwargs):
        r = original(*args, **kwargs)
        r["coleta_incompleta"] = True
        return r
    monkeypatch.setattr(completos, "coletar_repositorio", parcial)
    r = integrado.executar(cfg, Api(), 1, 1, fonte)
    assert r["total_amostra_completa"] == 0
    assert r["coletas_incompletas"] == 1
    assert not r["execucao_completa"]


def test_404_e_sem_actions_sao_descartados_e_continua(tmp_path):
    cfg, fonte = configurar(tmp_path, 3)
    class Erros(Api):
        def get(self, path, params=None):
            if path.endswith("repo1/actions/workflows"):
                return {"total_count": 0, "workflows": []}
            return super().get(path, params)
        def get_resposta(self, path, params=None):
            if path.endswith("repo2/releases"):
                r = requests.Response()
                r.status_code = 404
                raise requests.HTTPError(response=r)
            return super().get_resposta(path, params)
    r = integrado.executar(cfg, Erros(), 1, 3, fonte)
    assert r["execucao_completa"] and r["candidatos_avaliados"] == 3
    funil = json.loads((tmp_path / "processed/funil.json").read_text(encoding="utf-8"))
    assert {d["motivo"] for d in funil["descartes"]} == {"sem_github_actions", "repositorio_inacessivel"}


def test_mudar_criterio_nao_reutiliza_checkpoint_antigo(tmp_path):
    cfg, fonte = configurar(tmp_path, 1)
    assert integrado.executar(cfg, Api(), 1, 1, fonte)["execucao_completa"]
    cfg["inclusao"]["min_releases"] = 6
    api = Api()
    assert not integrado.executar(cfg, api, 1, 1, fonte)["execucao_completa"]
    assert api.chamadas


def test_reutilizar_janela_divergente_e_recusado(tmp_path):
    cfg, fonte = configurar(tmp_path, 1)
    seed = tmp_path / "seed.json"
    gravar_json(seed, {"janela": {}, "repositorios": []})
    with pytest.raises(ConfigError, match="Janela"):
        integrado.executar(cfg, Api(), 1, 1, fonte, seed)


@pytest.mark.parametrize("arquivo,campo,valor", [
    ("cfr.json", "falhas", 999),
    ("cfr.json", "change_failure_rate", .9),
    ("tempo_recuperacao.json", "iqr_horas", 999),
    ("tempo_recuperacao.json", "episodios_censurados", 999),
])
def test_auditoria_recusa_resultados_corrompidos(tmp_path, arquivo, campo, valor):
    from pipeline import auditoria
    cfg, fonte = configurar(tmp_path, 1)
    integrado.executar(cfg, Api(), 1, 1, fonte)
    saida = tmp_path / "processed" / arquivo
    documento = json.loads(saida.read_text(encoding="utf-8"))
    documento["repositorios"][0][campo] = valor
    gravar_json(saida, documento)
    with pytest.raises(ConfigError, match="Auditoria"):
        auditoria.validar(cfg, tmp_path / "raw/amostra_workflow_runs.json",
                         tmp_path / "processed/cfr.json", tmp_path / "processed/tempo_recuperacao.json")


def test_cli_relata_amostra_insuficiente_e_erros(tmp_path, monkeypatch, capsys):
    import yaml
    cfg, fonte = configurar(tmp_path, 1)
    caminho = tmp_path / "config.yaml"
    caminho.write_text(yaml.safe_dump(cfg))
    monkeypatch.setenv("GITHUB_TOKEN", "fixture")
    monkeypatch.setattr(integrado, "GitHubClient", lambda *a, **k: Api(excluidos=1))
    assert integrado.main(["--config", str(caminho), "--alvo", "1", "--max-candidatos", "1",
                           "--candidatos", str(fonte)]) == 3
    monkeypatch.delenv("GITHUB_TOKEN")
    assert integrado.main(["--config", str(caminho)]) == 2
    assert "GITHUB_TOKEN" in capsys.readouterr().err


def test_auditoria_confere_censura_e_rejeita_run_duplicado(tmp_path):
    from pipeline import auditoria
    cfg, fonte = configurar(tmp_path, 1)
    class Censura(Api):
        def get(self, path, params=None):
            r = super().get(path, params)
            if path.endswith("/actions/runs"):
                for run in r["workflow_runs"]:
                    if run["id"] == 49:
                        run["workflow_id"] = 8
                    if run["id"] == 50:
                        run["workflow_id"] = 8
                        run["conclusion"] = "failure"
            return r
    integrado.executar(cfg, Censura(), 1, 1, fonte)
    entrada = tmp_path / "raw/amostra_workflow_runs.json"
    taxas = tmp_path / "processed/cfr.json"
    tempos = tmp_path / "processed/tempo_recuperacao.json"
    assert auditoria.validar(cfg, entrada, taxas, tempos)["episodios_censurados"] == 1
    dados = json.loads(entrada.read_text(encoding="utf-8"))
    dados["repositorios"][0]["workflow_runs"].append(dados["repositorios"][0]["workflow_runs"][0])
    gravar_json(entrada, dados)
    with pytest.raises(ConfigError, match="duplicados"):
        auditoria.validar(cfg, entrada, taxas, tempos)


def test_busca_padrao_preservada_para_ampliacao_sem_busca_nova(tmp_path):
    cfg, fonte = configurar(tmp_path, 3)
    gravar_json(tmp_path / "raw/candidatos.json", json.loads(fonte.read_text(encoding="utf-8")))
    primeira = integrado.executar(cfg, Api(excluidos=1), 1, 3)
    assert primeira["candidatos_avaliados"] == 2
    busca = json.loads((tmp_path / "raw/candidatos_busca.json").read_text(encoding="utf-8"))
    assert len(busca["candidatos"]) == 3
    segunda = integrado.executar(cfg, Api(excluidos=1), 2, 3)
    assert segunda["execucao_completa"] and segunda["candidatos_avaliados"] == 3
    assert json.loads((tmp_path / "raw/candidatos_busca.json").read_text(encoding="utf-8")) == busca


def test_fonte_explicita_ausente_nao_dispara_busca(tmp_path):
    cfg, fonte = configurar(tmp_path)
    with pytest.raises(FileNotFoundError, match="Fonte"):
        integrado.executar(cfg, Api(), 1, 1, fonte.with_name("ausente.json"))


def test_retomada_mesma_entrada_audita_sem_recalcular_metricas(tmp_path, monkeypatch):
    cfg, fonte = configurar(tmp_path, 1)
    integrado.executar(cfg, Api(), 1, 1, fonte)
    def proibido(*args, **kwargs):
        raise AssertionError("não deveria repetir cálculo")
    monkeypatch.setattr(integrado.cfr, "executar", proibido)
    monkeypatch.setattr(integrado.tempo_recuperacao, "executar", proibido)
    monkeypatch.setattr(integrado.lead_time_release, "executar", proibido)
    original = integrado.compare.gravar_consolidado
    def nova_gravacao(*args, **kwargs):
        saida, lista = original(*args, **kwargs)
        dados = json.loads(saida.read_text(encoding="utf-8"))
        dados["gerado_em"] = "2030-01-01T00:00:00Z"
        gravar_json(saida, dados)
        return saida, lista
    monkeypatch.setattr(integrado.compare, "gravar_consolidado", nova_gravacao)
    assert integrado.executar(cfg, Api(), 1, 1, fonte)["execucao_completa"]


def test_fonte_explicita_sobre_saida_e_recusada(tmp_path):
    cfg, fonte = configurar(tmp_path, 1)
    destino = tmp_path / "raw/candidatos.json"
    gravar_json(destino, json.loads(fonte.read_text(encoding="utf-8")))
    with pytest.raises(ConfigError, match="Fonte explícita"):
        integrado.executar(cfg, Api(), 1, 1, destino)


def test_regra_estavel_explicita_alinha_inclusao_e_frequencia(tmp_path):
    cfg, fonte = configurar(tmp_path, 1)
    cfg["inclusao"]["incluir_prereleases"] = False
    class QuatroEstaveis(Api):
        def get_resposta(self, path, params=None):
            r = super().get_resposta(path, params)
            return resposta(r.json()[:5]) if path.endswith("/releases") else r
    assert not integrado.executar(cfg, QuatroEstaveis(), 1, 1, fonte)["execucao_completa"]
    cfg["inclusao"]["incluir_prereleases"] = True
    assert integrado.executar(cfg, QuatroEstaveis(), 1, 1, fonte)["execucao_completa"]
    df = json.loads((tmp_path / "processed/deployment_frequency.json").read_text(encoding="utf-8"))
    assert df["repositorios"][0]["releases_ano"] == 5
    assert df["unidade"] == "releases_por_semana"
    assert df["repositorios"][0]["deployment_frequency"] == pytest.approx(5/(365/7))
    cfg["inclusao"]["incluir_prereleases"] = False
    # Novo contexto/raw para coletor atualizado, sem reutilizar fixture com 4 estáveis.
    cfg["caminhos"]["raw"] = str(tmp_path / "raw2")
    assert integrado.executar(cfg, Api(), 1, 1, fonte)["execucao_completa"]
    df = json.loads((tmp_path / "processed/deployment_frequency.json").read_text(encoding="utf-8"))
    assert df["repositorios"][0]["releases_ano"] == 5
    assert df["unidade"] == "releases_por_semana"
    assert df["repositorios"][0]["deployment_frequency"] == pytest.approx(5/(365/7))


def test_interrupcao_compare_retoma_sem_recoletar_repo_ou_recalcular_metricas(tmp_path, monkeypatch):
    cfg, fonte = configurar(tmp_path, 2)
    class Interrompida(Api):
        def get_resposta(self, path, params=None):
            if "repo2/compare/" in path:
                raise requests.ConnectionError("interrupção no compare")
            return super().get_resposta(path, params)
    with pytest.raises(requests.ConnectionError, match="compare"):
        integrado.executar(cfg, Interrompida(), 2, 2, fonte)
    assert len(list((tmp_path / "raw/checkpoints/compare").glob("*/*.json"))) == 1
    taxas = (tmp_path / "processed/cfr.json").read_bytes()
    tempos = (tmp_path / "processed/tempo_recuperacao.json").read_bytes()
    def proibido(*args, **kwargs):
        raise AssertionError("métricas auditadas não devem ser recalculadas")
    monkeypatch.setattr(integrado.cfr, "executar", proibido)
    monkeypatch.setattr(integrado.tempo_recuperacao, "executar", proibido)
    api = Api()
    assert integrado.executar(cfg, api, 2, 2, fonte)["execucao_completa"]
    assert not any("repo1/" in p for p, _ in api.chamadas)
    assert (tmp_path / "processed/cfr.json").read_bytes() == taxas
    assert (tmp_path / "processed/tempo_recuperacao.json").read_bytes() == tempos


def test_compare_404_mantem_amostra_e_incompletude_explicita(tmp_path):
    cfg, fonte = configurar(tmp_path, 1)
    class Inacessivel(Api):
        def get_resposta(self, path, params=None):
            if path.endswith("/compare/v1...v2"):
                r = requests.Response()
                r.status_code = 404
                raise requests.HTTPError(response=r)
            return super().get_resposta(path, params)
    resultado = integrado.executar(cfg, Inacessivel(), 1, 1, fonte)
    assert resultado["total_amostra_completa"] == 1
    assert resultado["coletas_compare_incompletas"] == 1
    assert resultado["releases_compare_ignoradas"] == 2
    compare = json.loads((tmp_path / "raw/compare.json").read_text(encoding="utf-8"))
    assert compare["total_releases_ignoradas_404"] == 1
    assert compare["total_comparacoes"] == 3


@pytest.mark.parametrize("nivel,campo,valor", [
    ("repo", "lead_time_horas", 1),
    ("repo", "classe_lead_time", "Elite"),
    ("repo", "coleta_incompleta", True),
    ("release", "lead_time_horas", 1),
    ("documento", "releases_com_lead_time", 999),
])
def test_retomada_recusa_lead_time_corrompido_sem_recalcular(tmp_path, monkeypatch, nivel, campo, valor):
    cfg, fonte = configurar(tmp_path, 1)
    integrado.executar(cfg, Api(), 1, 1, fonte)
    caminho = tmp_path / "processed/lead_time_release.json"
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    alvo = dados if nivel == "documento" else dados["repositorios"][0]
    if nivel == "release":
        alvo = alvo["releases"][1]
    alvo[campo] = valor
    gravar_json(caminho, dados)
    def proibido(*args, **kwargs):
        raise AssertionError("não sobrescrever resultados auditados divergentes")
    monkeypatch.setattr(integrado.lead_time_release, "executar", proibido)
    with pytest.raises(ConfigError, match="Auditoria"):
        integrado.executar(cfg, Api(), 1, 1, fonte)


def test_versao_antiga_reprocessa_so_recuperacao_preservando_coleta_e_cfr(tmp_path, monkeypatch):
    cfg, fonte = configurar(tmp_path, 1)
    integrado.executar(cfg, Api(), 1, 1, fonte)
    caminho = tmp_path / "processed/tempo_recuperacao.json"
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    del dados["versao_metrica"]
    gravar_json(caminho, dados)
    legado = caminho.read_bytes()
    taxas = (tmp_path / "processed/cfr.json").read_bytes()
    def proibido(*args, **kwargs):
        raise AssertionError("CFR não deve ser repetida")
    monkeypatch.setattr(integrado.cfr, "executar", proibido)
    api = Api()
    integrado.executar(cfg, api, 1, 1, fonte)
    assert not api.chamadas
    assert (tmp_path / "processed/cfr.json").read_bytes() == taxas
    assert (tmp_path / "processed/tempo_recuperacao-legado-created-at.json").read_bytes() == legado
    assert json.loads(caminho.read_text(encoding="utf-8"))["versao_metrica"] == integrado.tempo_recuperacao.VERSAO_METRICA


@pytest.mark.parametrize("campo,valor", [
    ("proporcao_censurados", .5), ("historico_inicial_nao_observado", [{"inventado": True}]),
    ("dados_temporais_incompletos", True)])
def test_auditoria_temporal_recusa_diagnosticos_corrompidos(tmp_path, campo, valor):
    from pipeline import auditoria
    cfg, fonte = configurar(tmp_path, 1)
    integrado.executar(cfg, Api(), 1, 1, fonte)
    saida = tmp_path / "processed/tempo_recuperacao.json"
    dados = json.loads(saida.read_text(encoding="utf-8"))
    dados["repositorios"][0][campo] = valor
    gravar_json(saida, dados)
    with pytest.raises(ConfigError, match="Auditoria"):
        auditoria.validar(cfg, tmp_path / "raw/amostra_workflow_runs.json",
                         tmp_path / "processed/cfr.json", saida)


def test_migracao_classe_lt_preserva_valores_sem_recalcular(tmp_path, monkeypatch):
    cfg, fonte = configurar(tmp_path,1)
    integrado.executar(cfg,Api(),1,1,fonte)
    saida = tmp_path/"processed/lead_time_release.json"
    dados = json.loads(saida.read_text(encoding="utf-8"))
    del dados["versao_classificacao"]
    dados["repositorios"][0]["classe_lead_time"] = "Low"
    gravar_json(saida,dados)
    valores = dados["repositorios"][0]["releases"]
    def proibido(*args,**kwargs):
        raise AssertionError("Lead time já auditado não deve ser recalculado")
    monkeypatch.setattr(integrado.lead_time_release,"executar",proibido)
    integrado.executar(cfg,Api(),1,1,fonte)
    migrado = json.loads(saida.read_text(encoding="utf-8"))
    assert migrado["repositorios"][0]["releases"] == valores
    assert migrado["repositorios"][0]["classe_lead_time"] == "Medium"
    assert migrado["versao_classificacao"] == integrado.VERSAO_REFERENCIA



def test_migracao_classe_antiga_recusa_valor_lt_corrompido(tmp_path):
    cfg, fonte = configurar(tmp_path,1)
    integrado.executar(cfg,Api(),1,1,fonte)
    saida = tmp_path/"processed/lead_time_release.json"
    dados = json.loads(saida.read_text(encoding="utf-8"))
    del dados["versao_classificacao"]
    dados["repositorios"][0]["lead_time_horas"] = 999
    gravar_json(saida,dados)
    anterior = saida.read_bytes()
    with pytest.raises(ConfigError,match="mediana"):
        integrado.executar(cfg,Api(),1,1,fonte)
    assert saida.read_bytes() == anterior


REPO = {"id": 1, "full_name": "org/repo1", "default_branch": "main"}


def test_paginas_em_paralelo_dao_o_mesmo_resultado_e_as_mesmas_consultas():
    sequencial, paralelo = Api(nruns=950), Api(nruns=950)
    paralelo.paralelismo = 4
    esperado = completos.coletar_repositorio(sequencial, REPO, INICIO, FIM)
    assert completos.coletar_repositorio(paralelo, REPO, INICIO, FIM) == esperado
    assert esperado["total_runs"] == 950 and not esperado["coleta_incompleta"]
    assert len(sequencial.chamadas) == 10
    assert sorted(p["page"] for _, p in paralelo.chamadas) == list(range(1, 11))


def test_paginas_em_paralelo_respeitam_o_limite_de_conexoes():
    import threading
    import time

    class Lenta(Api):
        paralelismo = 3
        ativas = maximo = 0
        trava = threading.Lock()

        def get(self, path, params=None):
            if params["page"] == 1:
                return super().get(path, params)
            with self.trava:
                self.ativas += 1
                self.maximo = max(self.maximo, self.ativas)
            time.sleep(0.05)
            try:
                return super().get(path, params)
            finally:
                with self.trava:
                    self.ativas -= 1

    api = Lenta(nruns=950)
    assert completos.coletar_repositorio(api, REPO, INICIO, FIM)["total_runs"] == 950
    assert api.maximo == 3


def test_pagina_vazia_em_paralelo_encerra_a_fatia_como_incompleta():
    class Truncada(Api):
        paralelismo = 4

        def get(self, path, params=None):
            corpo = super().get(path, params)
            return {**corpo, "workflow_runs": []} if params["page"] >= 4 else corpo

    registro = completos.coletar_repositorio(Truncada(nruns=950), REPO, INICIO, FIM)
    assert registro["total_runs"] == 300 and registro["coleta_incompleta"]


def test_erro_em_uma_pagina_paralela_e_propagado():
    class Falha(Api):
        paralelismo = 4

        def get(self, path, params=None):
            if params["page"] == 7:
                raise requests.ConnectionError("interrupção simulada")
            return super().get(path, params)

    with pytest.raises(requests.ConnectionError):
        completos.coletar_repositorio(Falha(nruns=950), REPO, INICIO, FIM)


def test_paralelismo_maior_que_as_paginas_restantes(tmp_path):
    api = Api(nruns=150)
    api.paralelismo = 8
    assert completos.coletar_repositorio(api, REPO, INICIO, FIM)["total_runs"] == 150
    assert len(api.chamadas) == 2


@pytest.mark.parametrize("valor", [0, 9, -1, 2.0, "4", True, None])
def test_paralelismo_invalido_e_recusado_pelo_cliente(valor):
    from pipeline.github_api import GitHubClient
    with pytest.raises(ValueError, match="paralelismo"):
        GitHubClient("fixture", paralelismo=valor)


def test_cli_le_paralelismo_da_configuracao(tmp_path, monkeypatch, capsys):
    import yaml
    cfg, fonte = configurar(tmp_path, 1)
    caminho = tmp_path / "config.yaml"
    recebidos = []

    def cliente(*a, **k):
        recebidos.append(k["paralelismo"])
        return Api(excluidos=1)

    monkeypatch.setenv("GITHUB_TOKEN", "fixture")
    monkeypatch.setattr(integrado, "GitHubClient", cliente)
    argumentos = ["--config", str(caminho), "--alvo", "1", "--max-candidatos", "1", "--candidatos", str(fonte)]
    for api, esperado in (({**cfg["api"], "paralelismo": 6}, 6), ({k: v for k, v in cfg["api"].items() if k != "paralelismo"}, 1)):
        caminho.write_text(yaml.safe_dump({**cfg, "api": api}))
        assert integrado.main(argumentos) == 3
        assert recebidos[-1] == esperado
    monkeypatch.undo()
    monkeypatch.setenv("GITHUB_TOKEN", "fixture")
    caminho.write_text(yaml.safe_dump({**cfg, "api": {**cfg["api"], "paralelismo": 99}}))
    assert integrado.main(argumentos) == 2
    assert "paralelismo" in capsys.readouterr().err


def test_consultas_de_runs_dispensam_a_lista_de_pull_requests():
    api = Api(nruns=150)
    completos.coletar_repositorio(api, REPO, INICIO, FIM)
    assert [p["exclude_pull_requests"] for _, p in api.chamadas] == ["true", "true"]


def test_contribuidores_so_para_elegiveis_e_sem_cache_parcial(tmp_path):
    cfg, fonte = configurar(tmp_path, 3)
    api = Api(excluidos=1)
    integrado.executar(cfg, api, 2, 3, fonte)
    assert [p for p, _ in api.chamadas if p.endswith("/contributors")] == [
        "/repos/org/repo2/contributors", "/repos/org/repo3/contributors"]
    assert not (tmp_path / "cache/metadados/org__repo1.json").exists()
    metas = integrado._ler(tmp_path / "raw/metadados.json")["repositorios"]
    assert metas[0]["contribuidores_pendentes"] is True
    assert all("contribuidores_pendentes" not in m for m in metas[1:])


def test_contribuidores_nao_consultados_quando_runs_insuficientes(tmp_path):
    cfg, fonte = configurar(tmp_path, 2)
    api = Api(nruns=49)
    resultado = integrado.executar(cfg, api, 1, 2, fonte)
    assert not resultado["execucao_completa"]
    assert not any(p.endswith("/contributors") for p, _ in api.chamadas)


def test_contribuidores_inacessiveis_descartam_sem_quebrar_funil(tmp_path):
    cfg, fonte = configurar(tmp_path, 2)

    class Inacessivel(Api):
        def get_resposta(self, path, params=None):
            if path.endswith("repo1/contributors"):
                r = requests.Response()
                r.status_code = 404
                raise requests.HTTPError(response=r)
            return super().get_resposta(path, params)

    assert integrado.executar(cfg, Inacessivel(), 1, 2, fonte)["execucao_completa"]
    funil = integrado._ler(tmp_path / "processed/funil.json")
    assert funil["descartes"][0]["etapa"] == "metadados"
    assert [r["id"] for r in funil["amostra"]] == [2]


def _sem_datas_e_origem(valor):
    if isinstance(valor, dict):
        return {k: _sem_datas_e_origem(v) for k, v in valor.items()
                if k not in ("gerado_em", "coletado_em", "origem", "origens")}
    if isinstance(valor, list):
        return [_sem_datas_e_origem(v) for v in valor]
    return valor


def test_selecao_e_compare_paralelos_preservam_amostra_e_metricas(tmp_path):
    import threading

    cfg_s, fonte_s = configurar(tmp_path / "sequencial", 6)
    integrado.executar(cfg_s, Api(excluidos=2), 3, 6, fonte_s)
    cfg, fonte = configurar(tmp_path / "paralelo", 6)
    cfg["api"]["repositorios_paralelos"] = 2

    class ForaDeOrdem(Api):
        segundo = threading.Event()

        def get(self, path, params=None):
            if path.endswith("repo1/actions/workflows"):
                assert self.segundo.wait(5)
            if path.endswith("repo2/actions/workflows"):
                self.segundo.set()
            return super().get(path, params)

    api = ForaDeOrdem(excluidos=2)
    resultado = integrado.executar(cfg, api, 3, 6, fonte)
    assert resultado["candidatos_avaliados"] == 5
    assert not any("repo6/" in p for p, _ in api.chamadas)
    for pasta in ("raw", "processed"):
        for arquivo in (tmp_path / "sequencial" / pasta).glob("*.json"):
            if arquivo.name.startswith("auditoria") or arquivo.name in ("execucao.json", "progresso.json"):
                continue
            esperado = _sem_datas_e_origem(integrado._ler(arquivo))
            atual = _sem_datas_e_origem(integrado._ler(tmp_path / "paralelo" / pasta / arquivo.name))
            assert atual == esperado, arquivo.name
    # A retomada concorrente usa os checkpoints de seleção e de compare.
    nova_api = Api(falhar=3)
    assert integrado.executar(cfg, nova_api, 3, 6, fonte)["execucao_completa"]
    assert nova_api.chamadas == []


def test_interrupcao_paralela_preserva_checkpoints_e_retoma(tmp_path):
    cfg, fonte = configurar(tmp_path, 4)
    cfg["api"]["repositorios_paralelos"] = 2
    with pytest.raises(requests.ConnectionError):
        integrado.executar(cfg, Api(falhar=2), 4, 4, fonte)
    assert (next((tmp_path / "raw/checkpoints").glob("*/1.json"))).is_file()
    api = Api()
    assert integrado.executar(cfg, api, 4, 4, fonte)["execucao_completa"]
    assert not any(p == "/repos/org/repo1" for p, _ in api.chamadas)


@pytest.mark.parametrize("valor", [0, 9, -1, 2.0, "2", True, None])
def test_workers_invalidos_recusados_antes_da_coleta(tmp_path, valor):
    cfg, fonte = configurar(tmp_path, 1)
    cfg["api"]["repositorios_paralelos"] = valor
    api = Api()
    with pytest.raises(ConfigError, match="repositorios_paralelos"):
        integrado.executar(cfg, api, 1, 1, fonte)
    assert not api.chamadas


def test_compare_processa_repositorios_simultaneamente_em_ordem(tmp_path, monkeypatch):
    import threading
    cfg, _ = configurar(tmp_path, 2)
    cfg["api"]["repositorios_paralelos"] = 2
    inicio, fim = integrado.janela_utc(cfg)
    repos = [releases.coletar_repositorio(Api(), {"id": i, "full_name": f"org/repo{i}"}, inicio, fim)
             for i in (1, 2)]
    barreira = threading.Barrier(2, timeout=5)
    original = integrado.compare.coletar_repositorio

    def coletar(*args):
        barreira.wait()
        return original(*args)

    monkeypatch.setattr(integrado.compare, "coletar_repositorio", coletar)
    assert [r["id"] for r in integrado._coletar_compares(cfg, Api(), repos, inicio, fim)] == [1, 2]


@pytest.mark.parametrize("paralelismo", [1, 2, 4])
def test_teto_global_inclui_repositorios_paginas_e_telemetria(tmp_path, paralelismo):
    import threading
    import time
    from urllib.parse import urlsplit
    from pipeline.cache import CacheDisco
    from pipeline.github_api import GitHubClient

    cfg, fonte = configurar(tmp_path, 2)
    cfg["api"]["repositorios_paralelos"] = 2
    api = Api(nruns=250)
    trava = threading.Lock()
    ativas = maximo = 0

    class Sessao:
        def __init__(self):
            self.headers = {}

        def get(self, url, params, timeout):
            nonlocal ativas, maximo
            with trava:
                ativas += 1
                maximo = max(maximo, ativas)
            try:
                time.sleep(0.01)
                return resposta(api.get(urlsplit(url).path, params))
            finally:
                with trava:
                    ativas -= 1

        def close(self):
            pass

    client = GitHubClient("fixture", paralelismo=paralelismo, session_factory=Sessao,
                          cache=CacheDisco(cfg["caminhos"]["cache"]))
    try:
        resultado = integrado.executar(cfg, client, 2, 2, fonte)
        assert resultado["execucao_completa"]
        assert maximo == paralelismo
        http = resultado["desempenho"]["http"]
        assert http["requisicoes"] == len(api.chamadas)
        assert http["cache_hits"] == 2  # Histórico de releases reutiliza as páginas.
        assert http["espera_rate_limit_s"] == 0
        assert all(v >= 0 for v in resultado["desempenho"]["tempos"].values())
        chamadas = len(api.chamadas)
        retomada = integrado.executar(cfg, client, 2, 2, fonte)
        assert len(api.chamadas) == chamadas
        assert retomada["desempenho"]["http"]["requisicoes"] == 0
    finally:
        client.close()


@pytest.mark.parametrize("nome_atual", ["org/renomeado", "outra-org/transferido"])
def test_renomeacao_com_mesmo_id_preserva_fonte_e_retomada(tmp_path, caplog, nome_atual):
    class Renomeado(Api):
        def get_resposta(self, path, params=None):
            result = super().get_resposta(path, params)
            if path == "/repos/org/repo1":
                result = resposta({**result.json(), "full_name": nome_atual})
            return result

    cfg, fonte = configurar(tmp_path, 2)
    fonte_original = fonte.read_bytes()
    resultado = integrado.executar(cfg, Renomeado(), 2, 2, fonte)
    assert resultado["execucao_completa"]
    assert resultado["total_amostra_completa"] == 2
    assert fonte.read_bytes() == fonte_original
    checkpoint = next((tmp_path / "raw/checkpoints").glob("*/1.json"))
    registro = integrado._ler(checkpoint)
    assert registro["renomeacao"] == {"id": 1, "full_name_fonte": "org/repo1",
                                      "full_name_atual": nome_atual}
    assert registro["candidato"]["full_name"] == "org/repo1"
    for etapa in ("actions", "metadados", "releases", "workflow_runs"):
        assert registro["aprovados"][etapa]["id"] == 1
        assert registro["aprovados"][etapa]["full_name"] == "org/repo1"
    metas = integrado._ler(tmp_path / "raw/metadados.json")["repositorios"]
    assert metas[0]["full_name_atual"] == nome_atual
    assert "agora se chama" in caplog.text
    antes = checkpoint.read_bytes()
    sem_api = Api(falhar=1)
    assert integrado.executar(cfg, sem_api, 2, 2, fonte)["execucao_completa"]
    assert not sem_api.chamadas
    assert checkpoint.read_bytes() == antes


def test_metadados_com_id_diferente_continuam_rejeitados(tmp_path):
    class IdentidadeTrocada(Api):
        def get_resposta(self, path, params=None):
            result = super().get_resposta(path, params)
            if path == "/repos/org/repo1":
                result = resposta({**result.json(), "id": 99})
            return result

    cfg, fonte = configurar(tmp_path, 1)
    with pytest.raises(ConfigError, match="ID esperado 1, recebido 99"):
        integrado.executar(cfg, IdentidadeTrocada(), 1, 1, fonte)
    assert not list((tmp_path / "raw/checkpoints").glob("*/1.json"))
