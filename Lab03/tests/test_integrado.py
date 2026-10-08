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
            "conclusion": "failure" if i == 0 else "success"}


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
        if path.endswith("/releases"):
            return resposta([{"id": i, "draft": False, "prerelease": i == 0,
                               "published_at": "2025-10-10T00:00:00Z", "tag_name": f"v{i}"}
                              for i in range(3 if n <= self.excluidos else 5)])
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
    assert fonte.read_bytes() == original
    assert not any("repo1/actions/runs" in p for p, _ in api.chamadas)
    cfr = json.loads((tmp_path / "processed/cfr.json").read_text())
    assert cfr["total_repositorios"] == 100
    assert cfr["repositorios"][0]["change_failure_rate"] == 1/50
    recuperacao = json.loads((tmp_path / "processed/tempo_recuperacao.json").read_text())
    assert recuperacao["total_episodios"] == 100
    assert recuperacao["episodios_censurados"] == 0
    api2 = Api(falhar=21)
    assert integrado.executar(cfg, api2, 100, 120, fonte)["execucao_completa"]
    assert not api2.chamadas


def test_amostra_insuficiente_nao_declara_sucesso(tmp_path):
    cfg, fonte = configurar(tmp_path, 3)
    r = integrado.executar(cfg, Api(excluidos=2), 2, 3, fonte)
    assert r["total_amostra_completa"] == 1 and not r["execucao_completa"]


def test_interrupcao_preserva_checkpoint_e_retomada(tmp_path):
    cfg, fonte = configurar(tmp_path, 3)
    with pytest.raises(requests.ConnectionError):
        integrado.executar(cfg, Api(falhar=2), 3, 3, fonte)
    assert len(list((tmp_path / "raw/checkpoints").rglob("*.json"))) == 1
    api = Api()
    assert integrado.executar(cfg, api, 3, 3, fonte)["execucao_completa"]
    assert not any("repo1/" in p for p, _ in api.chamadas)


def test_subdivide_mes_saturado_sem_perder_runs_nas_fronteiras():
    api = Api(nruns=1100)
    fatias, lista = completos.coletar_intervalo(api, "org/repo1", "main", INICIO, FIM)
    assert len(lista) == len({r["id"] for r in lista}) == 1100
    assert fatias[0]["subdividido"] and not fatias[0]["coleta_incompleta"]
    assert all(p["event"] == "push" and p["branch"] == "main" for _, p in api.chamadas)


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
        def get_resposta(self, path, params):
            if params["page"] == 1:
                return resposta([r, {**r, "id": 2, "draft": True},
                                  {**r, "id": 3, "published_at": "2025-09-30T23:59:59Z"}], "https://api.github.com/next")
            return resposta([r, {**r, "id": 4, "published_at": "2025-10-31T23:59:59Z"}])
    repo = releases.coletar_repositorio(Paginada(), {"id": 1, "full_name": "org/r"}, INICIO, FIM)
    assert repo["paginas"] == 2
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
    funil = json.loads((tmp_path / "processed/funil.json").read_text())
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
    documento = json.loads(saida.read_text())
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
                    if run["id"] == 50:
                        run["workflow_id"] = 8
                        run["conclusion"] = "failure"
            return r
    integrado.executar(cfg, Censura(), 1, 1, fonte)
    entrada = tmp_path / "raw/amostra_workflow_runs.json"
    taxas = tmp_path / "processed/cfr.json"
    tempos = tmp_path / "processed/tempo_recuperacao.json"
    assert auditoria.validar(cfg, entrada, taxas, tempos)["episodios_censurados"] == 1
    dados = json.loads(entrada.read_text())
    dados["repositorios"][0]["workflow_runs"].append(dados["repositorios"][0]["workflow_runs"][0])
    gravar_json(entrada, dados)
    with pytest.raises(ConfigError, match="duplicados"):
        auditoria.validar(cfg, entrada, taxas, tempos)


def test_busca_padrao_preservada_para_ampliacao_sem_busca_nova(tmp_path):
    cfg, fonte = configurar(tmp_path, 3)
    gravar_json(tmp_path / "raw/candidatos.json", json.loads(fonte.read_text()))
    primeira = integrado.executar(cfg, Api(excluidos=1), 1, 3)
    assert primeira["candidatos_avaliados"] == 2
    busca = json.loads((tmp_path / "raw/candidatos_busca.json").read_text())
    assert len(busca["candidatos"]) == 3
    segunda = integrado.executar(cfg, Api(excluidos=1), 2, 3)
    assert segunda["execucao_completa"] and segunda["candidatos_avaliados"] == 3
    assert json.loads((tmp_path / "raw/candidatos_busca.json").read_text()) == busca


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
    assert integrado.executar(cfg, Api(), 1, 1, fonte)["execucao_completa"]


def test_fonte_explicita_sobre_saida_e_recusada(tmp_path):
    cfg, fonte = configurar(tmp_path, 1)
    destino = tmp_path / "raw/candidatos.json"
    gravar_json(destino, json.loads(fonte.read_text()))
    with pytest.raises(ConfigError, match="Fonte explícita"):
        integrado.executar(cfg, Api(), 1, 1, destino)
