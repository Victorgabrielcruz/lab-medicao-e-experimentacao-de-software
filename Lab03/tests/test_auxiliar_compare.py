import copy
import datetime as dt
import json
from pathlib import Path

import pytest
import requests

from pipeline import auxiliar_compare as aux, integrado
from pipeline.cache import gravar_json
from pipeline.config import ConfigError, janela_utc, load_config

CONFIG = Path(__file__).resolve().parents[1] / "config.yaml"


def configurar(tmp_path):
    cfg = load_config(CONFIG)
    cfg["caminhos"] = {k: str(tmp_path / k) for k in ("raw", "processed", "cache")}
    cfg["api"]["repositorios_paralelos"] = 1
    fonte = tmp_path / "fonte.json"
    gravar_json(fonte, {"candidatos": [{"id": i, "full_name": f"org/repo{i}"} for i in range(1, 4)]})
    principal = aux.Principal(cfg, fonte, relogio=lambda: 1000)
    gravar_json(principal.raw / "processo.json", {"estado": "executando", "atualizado_utc":
               dt.datetime.fromtimestamp(1000, dt.timezone.utc).isoformat()})
    progresso = {"contexto": copy.deepcopy(principal.contexto), "alvo": 3, "candidatos_avaliados": 2,
                 "elegiveis_com_coleta_completa": 1}
    gravar_json(principal.raw / "progresso.json", progresso)
    return cfg, principal, progresso


def repo(i=1):
    return {"id": i, "full_name": f"org/repo{i}", "default_branch": "main", "total_releases": 1,
            "releases": [{"id": 10, "tag_name": "v1", "draft": False, "prerelease": False,
                          "published_at": "2025-10-10T00:00:00Z"}]}


def checkpoint(principal, i, elegivel=True):
    gravar_json(principal.pasta / f"{i}.json", {"candidato": {"id": i, "full_name": f"org/repo{i}"},
               "elegivel": elegivel, "aprovados": {"releases": repo(i)}, "descartes": {}})


def test_descobre_so_aprovados_confirmados_e_nao_muda_estado_principal(tmp_path):
    cfg, p, _ = configurar(tmp_path)
    checkpoint(p, 1)
    checkpoint(p, 2, False)
    checkpoint(p, 3)  # Ainda está em processamento; não foi consumido na ordem.
    antes = {f: f.read_bytes() for f in p.raw.rglob("*.json")}
    assert [r["id"] for r in p.descobrir()] == [1]
    assert {f: f.read_bytes() for f in p.raw.rglob("*.json")} == antes


@pytest.mark.parametrize("mudanca,tipo", [("contexto", ConfigError), ("alvo", aux.EncerrarAuxiliar),
                                         ("parada", aux.EncerrarAuxiliar), ("inativa", aux.PausaAuxiliar),
                                         ("antiga", aux.PausaAuxiliar)])
def test_pausa_ou_encerra_sem_api_se_principal_nao_permite(tmp_path, mudanca, tipo):
    _, p, progresso = configurar(tmp_path)
    if mudanca == "contexto":
        progresso["contexto"]["versao"] = 999
        gravar_json(p.raw / "progresso.json", progresso)
    elif mudanca == "alvo":
        progresso["elegiveis_com_coleta_completa"] = 3
        gravar_json(p.raw / "progresso.json", progresso)
    elif mudanca == "parada":
        (p.raw / "auxiliar-compare").mkdir()
        (p.raw / "auxiliar-compare/parar").touch()
    else:
        gravar_json(p.raw / "processo.json", {"estado": "falhou" if mudanca == "inativa" else "executando",
                   "atualizado_utc": "1970-01-01T00:00:00+00:00"})
    with pytest.raises(tipo):
        p.conferir()


def test_lock_exclusivo_e_liberado_apos_saida(tmp_path):
    with aux.instancia_unica(tmp_path):
        with pytest.raises(OSError):
            with aux.instancia_unica(tmp_path):
                pytest.fail("Segunda instância adquiriu o lock")
    with aux.instancia_unica(tmp_path):
        pass


def test_publicacao_atomica_nao_substitui_arquivo_existente(tmp_path):
    origem, destino = tmp_path / "origem.json", tmp_path / "destino.json"
    origem.write_text('{"id":1}')
    assert aux.publicar(origem, destino)
    origem.write_text('{"id":2}')
    assert not aux.publicar(origem, destino)
    assert json.loads(destino.read_text()) == {"id": 1}
    assert not list(tmp_path.glob("*.tmp"))


def test_integrado_existente_reutiliza_checkpoint_auxiliar_sem_chamar_api(tmp_path, monkeypatch):
    cfg, principal, _ = configurar(tmp_path)
    inicio, fim = janela_utc(cfg)
    registro = {"id": 1, "full_name": "org/repo1", "total_releases": 1, "total_comparacoes": 1,
                "total_releases_ignoradas": 0, "releases_ignoradas_por_motivo": {},
                "total_releases_ignoradas_404": 0, "comparacoes_acima_250": 0,
                "coleta_incompleta": False, "comparacoes": []}
    chamadas = []
    monkeypatch.setattr(aux.compare, "coletar_repositorio", lambda *args: chamadas.append(args) or registro)
    assert aux.antecipar(cfg, principal, object(), repo(), tmp_path / "aux") == "publicado"
    assert len(chamadas) == 1
    destino = aux.caminho_compare(principal.raw, repo(), inicio, fim, cfg["api"]["base_url"])
    antes = destino.read_bytes()
    def proibido(*args):
        pytest.fail("Compare já antecipado foi consultado novamente")
    monkeypatch.setattr(aux.compare, "coletar_repositorio", proibido)
    resumo = integrado._coletar_compares(cfg, object(), [repo()], inicio, fim)
    assert resumo == [{k: v for k, v in registro.items() if k != "comparacoes"}]
    consolidado = json.loads((principal.raw / "compare.json").read_text(encoding="utf-8"))
    assert consolidado["repositorios"] == [registro]
    assert destino.read_bytes() == antes
    assert aux.antecipar(cfg, principal, object(), repo(), tmp_path / "aux") == "reutilizado"


def test_se_principal_termina_durante_compare_nao_publica_mas_guarda_local(tmp_path, monkeypatch):
    cfg, p, progresso = configurar(tmp_path)
    def terminar(*args):
        progresso["elegiveis_com_coleta_completa"] = 3
        gravar_json(p.raw / "progresso.json", progresso)
        return {"id": 1, "full_name": "org/repo1"}
    monkeypatch.setattr(aux.compare, "coletar_repositorio", terminar)
    with pytest.raises(aux.EncerrarAuxiliar):
        aux.antecipar(cfg, p, object(), repo(), tmp_path / "aux")
    assert len(list((tmp_path / "aux/prontos").rglob("*.json"))) == 1
    assert not list((p.raw / "checkpoints/compare").rglob("*.json"))


class Relogio:
    agora = 1000
    def time(self):
        return self.agora
    def sleep(self, n):
        self.agora += n


class Sessao:
    def __init__(self, remaining=4900, reset=1100, replies=()):
        self.headers, self.chamadas = {}, []
        self.cota = {"limit": 5000, "remaining": remaining, "reset": reset}
        self.replies = iter(replies)
    def get(self, url, params=None, timeout=None):
        self.chamadas.append(url)
        r = requests.Response()
        r.status_code = 200
        r._content = json.dumps({"resources": {"core": copy.copy(self.cota)}} if url.endswith("/rate_limit") else {"ok": True}).encode()
        if not url.endswith("/rate_limit"):
            status, headers = next(self.replies, (200, {}))
            r.status_code = status
            r.headers.update(headers)
        return r
    def close(self):
        pass


def cliente(tmp_path, sessao):
    cfg, principal, _ = configurar(tmp_path)
    relogio = Relogio()
    c = aux.ClienteAuxiliar("token-falso", cfg, principal, session=sessao,
                            relogio=relogio.time, sleep=relogio.sleep)
    return c, relogio, principal


def test_cota_baixa_nao_faz_chamada_de_coleta(tmp_path):
    sessao = Sessao(remaining=1999)
    c, _, _ = cliente(tmp_path, sessao)
    with pytest.raises(aux.PausaAuxiliar):
        c.get("/repos/org/repo/compare/a...b")
    assert all(url.endswith("/rate_limit") for url in sessao.chamadas)
    assert c.estatisticas()["requisicoes"] == 0


def test_reserva_proporcional_protege_orcamento_no_inicio_da_janela(tmp_path):
    sessao = Sessao(remaining=4700, reset=4600)
    c, _, _ = cliente(tmp_path, sessao)
    with pytest.raises(aux.PausaAuxiliar):
        c.get("/repos/org/repo/compare/a...b")
    assert len(sessao.chamadas) == 1


def test_intervalo_cache_e_headers_da_cota(tmp_path):
    sessao = Sessao(replies=[(200, {"X-RateLimit-Remaining": "2100"}), (200, {})])
    c, clock, _ = cliente(tmp_path, sessao)
    c.get("/repos/org/repo/compare/a...b")
    c.get("/repos/org/repo/compare/a...b")  # Cache não consome API nem espera.
    assert clock.agora == 1000
    c.get("/repos/org/repo/compare/b...c")
    assert clock.agora == 1006
    assert c.cota["remaining"] == 2100
    assert c.estatisticas()["requisicoes"] == 2
    assert c.estatisticas()["cache_hits"] == 1


def test_retry_5xx_tambem_obedece_intervalo(tmp_path):
    sessao = Sessao(replies=[(500, {}), (200, {})])
    c, clock, _ = cliente(tmp_path, sessao)
    assert c.get("/repos/org/repo/compare/a...b") == {"ok": True}
    assert clock.agora == 1006  # Backoff 1s + restante do intervalo 5s.
    assert c.estatisticas()["repeticoes_5xx"] == 1


def test_limite_secundario_respeita_retry_after_sem_novas_chamadas(tmp_path):
    sessao = Sessao(replies=[(429, {"Retry-After": "120"})])
    c, clock, _ = cliente(tmp_path, sessao)
    with pytest.raises(aux.PausaAuxiliar):
        c.get("/repos/org/repo/compare/a...b")
    n = len(sessao.chamadas)
    clock.agora += 60
    with pytest.raises(aux.PausaAuxiliar):
        c.get("/repos/org/repo/compare/a...b")
    assert len(sessao.chamadas) == n


def test_nao_consulta_api_quando_principal_atingiu_alvo(tmp_path):
    sessao = Sessao()
    c, _, p = cliente(tmp_path, sessao)
    progresso = aux.ler(p.raw / "progresso.json")
    progresso["elegiveis_com_coleta_completa"] = 3
    gravar_json(p.raw / "progresso.json", progresso)
    with pytest.raises(aux.EncerrarAuxiliar):
        c.get("/repos/org/repo/compare/a...b")
    assert sessao.chamadas == []


@pytest.mark.parametrize("falha_rede", [False, True])
def test_execucao_publica_retoma_rede_e_encerra_so_auxiliar(tmp_path, monkeypatch, falha_rede):
    cfg, p, _ = configurar(tmp_path)
    checkpoint(p, 1)
    checkpoint(p, 2, False)
    gravar_json(p.raw / "processo.json", {"estado": "executando", "atualizado_utc":
               dt.datetime.now(dt.timezone.utc).isoformat()})
    antes = {f: f.read_bytes() for f in (p.raw / "processo.json", p.raw / "progresso.json")}
    chamadas = []
    def comparar(*args):
        chamadas.append(args)
        if falha_rede and len(chamadas) == 1:
            raise requests.ConnectionError("rede simulada")
        return {"id": 1, "full_name": "org/repo1"}
    class ClienteSemRede:
        def __init__(self, *args, **kwargs):
            pass
        def estatisticas(self):
            return {"requisicoes": 0}
        def close(self):
            pass
    def dormir(n):
        # Após a publicação não há pendências; pedir parada só da auxiliar.
        if list((p.raw / "checkpoints/compare").rglob("*.json")):
            (p.raw / "auxiliar-compare/parar").touch()
    monkeypatch.setattr(aux, "ClienteAuxiliar", ClienteSemRede)
    monkeypatch.setattr(aux.compare, "coletar_repositorio", comparar)
    monkeypatch.setattr(aux.time, "sleep", dormir)
    result = aux.executar(cfg, tmp_path / "fonte.json", "token-falso")
    assert result["estado"] == "encerrada"
    assert result["checkpoints_publicados"] == 1
    assert len(chamadas) == (2 if falha_rede else 1)
    assert {f: f.read_bytes() for f in antes} == antes


def configurar_futuros(tmp_path):
    cfg, p, progresso = configurar(tmp_path)
    fonte = tmp_path / "fonte.json"
    gravar_json(fonte, {"candidatos": [{"id": i, "full_name": f"org/repo{i}"} for i in range(1, 61)]})
    p = aux.Principal(cfg, fonte, relogio=lambda: 1000)
    progresso["contexto"] = copy.deepcopy(p.contexto)
    gravar_json(p.raw / "progresso.json", progresso)
    return cfg, p, progresso


def test_fila_futura_respeita_margem_janela_e_checkpoints_existentes(tmp_path):
    cfg, p, _ = configurar_futuros(tmp_path)
    candidatos = p.proximos()
    assert candidatos[0][0] == 9  # 2 consumidos + 1 worker + 6 de margem.
    assert candidatos[0][1]["id"] == 10
    assert len(candidatos) == 32
    checkpoint(p, 10, False)
    assert p.proximos()[0][1]["id"] == 11
    estado = aux.ler(p.raw / "processo.json")
    estado["max_candidatos"] = 12
    gravar_json(p.raw / "processo.json", estado)
    assert [r["id"] for _, r in p.proximos()] == [11, 12]


@pytest.mark.parametrize("elegivel", [True, False])
def test_checkpoint_candidato_com_runs_inteiros_reutilizado_sem_api(tmp_path, elegivel):
    from test_integrado import Api
    cfg, p, _ = configurar_futuros(tmp_path)
    indice, candidato = p.proximos()[0]
    api = Api(excluidos=0 if elegivel else 10)
    antes = {f: f.read_bytes() for f in (p.raw / "processo.json", p.raw / "progresso.json")}
    resultado, incluido = aux.antecipar_candidato(cfg, p, api, indice, candidato, tmp_path / "aux")
    assert (resultado, incluido) == ("publicado", elegivel)
    registro = aux.ler(p.pasta / "10.json")
    assert registro["elegivel"] == elegivel
    if elegivel:
        assert len(registro["aprovados"]["workflow_runs"]["workflow_runs"]) == 50
    inicio, fim = janela_utc(cfg)
    retomado = integrado._coletar_candidato(cfg, object(), candidato, p.pasta, {}, inicio, fim)
    assert retomado["elegivel"] == elegivel
    assert {f: f.read_bytes() for f in antes} == antes
    assert api.validar_tarefa is None


def test_principal_consumiu_candidato_durante_coleta_guarda_so_privado(tmp_path, monkeypatch):
    cfg, p, progresso = configurar_futuros(tmp_path)
    indice, candidato = p.proximos()[0]
    def coletar(config, client, repo, pasta, anteriores, inicio, fim):
        registro = {"candidato": repo, "elegivel": False, "aprovados": {}, "descartes": {}}
        gravar_json(pasta / f"{repo['id']}.json", registro)
        progresso["candidatos_avaliados"] += 1
        gravar_json(p.raw / "progresso.json", progresso)
        return registro
    class Api:
        pass
    api = Api()
    monkeypatch.setattr(integrado, "_coletar_candidato", coletar)
    with pytest.raises(aux.PausaAuxiliar):
        aux.antecipar_candidato(cfg, p, api, indice, candidato, tmp_path / "aux")
    assert not (p.pasta / "10.json").exists()
    assert list((tmp_path / "aux/candidatos").rglob("10.json"))
    assert api.validar_tarefa is None


def test_fila_da_principal_e_amostra_preservadas_com_antecipacao(tmp_path):
    from test_integrado import Api
    cfg, p, _ = configurar_futuros(tmp_path)
    fonte = tmp_path / "fonte.json"
    antes = fonte.read_bytes()
    indice, candidato = p.proximos()[0]
    aux.antecipar_candidato(cfg, p, Api(excluidos=9), indice, candidato, tmp_path / "aux")
    api = Api(excluidos=9)
    resultado = integrado.executar(cfg, api, alvo=2, max_candidatos=60, fonte=fonte)
    assert resultado["total_amostra_completa"] == 2
    assert resultado["candidatos_avaliados"] == 11
    frequencia = aux.ler(Path(cfg["caminhos"]["processed"]) / "deployment_frequency.json")
    assert [r["id"] for r in frequencia["repositorios"]] == [10, 11]
    assert not [path for path, _ in api.chamadas if path.startswith('/repos/org/repo10/actions/')]
    assert fonte.read_bytes() == antes


def test_guard_do_candidato_interrompe_antes_de_nova_requisicao(tmp_path):
    sessao = Sessao()
    client, clock, p = cliente(tmp_path, sessao)
    client.validar_tarefa = lambda: p.conferir_candidato(9)
    client.get('/repos/org/repo10/actions/workflows')
    chamadas = len(sessao.chamadas)
    progresso = aux.ler(p.raw / 'progresso.json')
    progresso['candidatos_avaliados'] = 3
    gravar_json(p.raw / 'progresso.json', progresso)
    with pytest.raises(aux.PausaAuxiliar):
        client.get('/repos/org/repo10/actions/runs')
    assert len(sessao.chamadas) == chamadas


def test_reutiliza_mes_do_piloto_somente_de_candidatos_futuros(tmp_path):
    cfg, p, _ = configurar_futuros(tmp_path)
    entrada = tmp_path / "piloto.json"
    gravar_json(entrada, {"janela": p.contexto['janela'], "repositorios": [
        {"id": 1, "workflow_runs": []}, {"id": 10, "workflow_runs": []}]})
    assert set(aux.carregar_anteriores(entrada, p)) == {10}
    gravar_json(entrada, {"janela": {}, "repositorios": []})
    with pytest.raises(ConfigError):
        aux.carregar_anteriores(entrada, p)


def test_candidato_grande_cede_rodada_e_preserva_paginas(tmp_path, monkeypatch):
    cfg, p, _ = configurar_futuros(tmp_path)
    clock, sessao = Relogio(), Sessao(reset=4600)
    c = aux.ClienteAuxiliar("token-falso", cfg, p, session=sessao,
                            relogio=clock.time, sleep=clock.sleep)
    def coletar(config, client, repo, *args):
        for i in range(31):
            client.get(f'/repos/org/repo10/pagina/{i}')
        pytest.fail('Deveria ter cedido antes da chamada 31')
    monkeypatch.setattr(integrado, '_coletar_candidato', coletar)
    with pytest.raises(aux.AdiarCandidato):
        aux.antecipar_candidato(cfg, p, c, 9, p.candidatos[9], tmp_path / 'aux')
    assert c.requisicoes_reais == 30
    assert c.cache.ler(f'{c.base_url}/repos/org/repo10/pagina/0') is not None
    assert c.cache.ler(f'{c.base_url}/repos/org/repo10/pagina/29') is not None
    assert not (p.pasta/'10.json').exists()
    assert c.validar_tarefa is None


def test_scheduler_prioriza_candidato_antes_de_compare(tmp_path, monkeypatch):
    from test_integrado import Api
    cfg, p, _ = configurar_futuros(tmp_path)
    gravar_json(p.raw/'processo.json', {'estado':'executando', 'atualizado_utc':
        dt.datetime.now(dt.timezone.utc).isoformat()})
    class ClienteSemRede(Api):
        def __init__(self, *args, **kwargs):
            super().__init__(excluidos=9)
        def estatisticas(self):
            if (p.pasta/'10.json').exists():
                (p.raw/'auxiliar-compare/parar').touch()
            return {'requisicoes':len(self.chamadas)}
        def close(self):
            pass
    def proibido(*args):
        pytest.fail('Compare executado enquanto havia candidato futuro pendente')
    monkeypatch.setattr(aux, 'ClienteAuxiliar', ClienteSemRede)
    monkeypatch.setattr(aux, 'antecipar', proibido)
    s=aux.executar(cfg,tmp_path/'fonte.json','token-falso')
    assert s['estado']=='encerrada'
    assert s['candidatos_antecipados']==s['candidatos_publicados']==s['elegiveis_antecipados']==1
