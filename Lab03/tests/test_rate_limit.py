"""Cenários de rate limit/backoff com HTTP e passagem do tempo simulados."""

import json

import pytest
import requests

from pipeline.cache import CacheDisco
from pipeline.github_api import GitHubClient


def resposta(status=200, headers=None, corpo=None):
    r = requests.Response()
    r.status_code = status
    r.headers.update(headers or {})
    r._content = json.dumps(corpo if corpo is not None else {"ok": True}).encode()
    return r


class Relogio:
    def __init__(self, agora=100):
        self.agora = agora
        self.esperas = []

    def time(self):
        return self.agora

    def sleep(self, segundos):
        self.esperas.append(segundos)
        self.agora += segundos


class Sessao:
    def __init__(self, respostas, relogio):
        self.headers = {}
        self.respostas = iter(respostas)
        self.chamadas = []
        self.relogio = relogio

    def get(self, url, params, timeout):
        self.chamadas.append((url, params, timeout, self.relogio.agora))
        resultado = next(self.respostas)
        if isinstance(resultado, Exception):
            raise resultado
        return resultado


def cliente(respostas, cache=None):
    tempo = Relogio()
    sessao = Sessao(respostas, tempo)
    c = GitHubClient("token-de-teste", timeout_s=12, session=sessao, cache=cache,
                     sleep=tempo.sleep, relogio=tempo.time)
    return c, sessao, tempo


@pytest.mark.parametrize("status", [500, 502, 503, 504, 599])
def test_5xx_repetidos_com_1_2_4_8_segundos(status, caplog):
    c, sessao, tempo = cliente([resposta(status) for _ in range(4)] + [resposta()])
    assert c.get("/repos/org/projeto", {"page": 2}) == {"ok": True}
    assert tempo.esperas == [1, 2, 4, 8]
    assert [chamada[3] for chamada in sessao.chamadas] == [100, 101, 103, 107, 115]
    assert all(chamada[:3] == ("https://api.github.com/repos/org/projeto", {"page": 2}, 12)
               for chamada in sessao.chamadas)
    assert "token-de-teste" not in caplog.text
    assert "repetição 4/4" in caplog.text


def test_5xx_persistente_propaga_ultima_resposta_e_nao_cacheia(tmp_path):
    ultima = resposta(503, corpo={"message": "ainda indisponível"})
    c, sessao, tempo = cliente([resposta(500) for _ in range(4)] + [ultima], CacheDisco(tmp_path))
    with pytest.raises(requests.HTTPError) as erro:
        c.get("/repos/org/projeto")
    assert erro.value.response is ultima
    assert len(sessao.chamadas) == 5
    assert tempo.esperas == [1, 2, 4, 8]
    assert not list(tmp_path.rglob("*.json"))


def test_sucesso_interrompe_repeticoes_e_reinicia_contador_na_proxima_consulta():
    c, sessao, tempo = cliente([resposta(500), resposta(), resposta(502), resposta()])
    c.get("/repos/org/a")
    c.get("/repos/org/b")
    assert tempo.esperas == [1, 1]
    assert len(sessao.chamadas) == 4


@pytest.mark.parametrize("status", [403, 429])
def test_limite_primario_aguarda_reset_e_repete_mesma_consulta(status):
    c, sessao, tempo = cliente([
        resposta(status, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "130"}), resposta(),
    ])
    assert c.get("/repos/org/projeto", {"page": 1}) == {"ok": True}
    assert tempo.esperas == [31]
    assert sessao.chamadas[1][3] == 131
    assert sessao.chamadas[0][:3] == sessao.chamadas[1][:3]


def test_ultima_requisicao_bem_sucedida_nao_espera_mas_proxima_aguarda():
    c, sessao, tempo = cliente([
        resposta(headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "120"}), resposta(),
    ])
    assert c.get("/repos/org/a") == {"ok": True}
    assert tempo.esperas == []
    c.get("/repos/org/b")
    assert tempo.esperas == [21]
    assert sessao.chamadas[1][3] == 121


def test_cota_positiva_permite_proxima_requisicao_sem_espera():
    c, sessao, tempo = cliente([
        resposta(headers={"X-RateLimit-Remaining": "2", "X-RateLimit-Reset": "120"}), resposta(),
    ])
    c.get("/repos/org/a")
    c.get("/repos/org/b")
    assert tempo.esperas == []
    assert [chamada[3] for chamada in sessao.chamadas] == [100, 100]


def test_cache_e_recurso_core_continuam_disponiveis_com_search_esgotado(tmp_path):
    cache = CacheDisco(tmp_path)
    c, sessao, tempo = cliente([
        resposta(headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "120",
                          "X-RateLimit-Resource": "search"}), resposta(), resposta(),
    ], cache)
    params = {"q": "stars:1000..2000"}
    c.get("/search/repositories", params)
    assert c.get("/search/repositories", params) == {"ok": True}
    c.get("/repos/org/projeto")
    assert tempo.esperas == []
    assert len(sessao.chamadas) == 2
    c.get("/search/repositories", {"q": "stars:2001..3000"})
    assert tempo.esperas == [21]


def test_recurso_reportado_e_reconhecido_na_proxima_consulta_ao_endpoint():
    c, _, tempo = cliente([
        resposta(headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "110",
                          "X-RateLimit-Resource": "custom"}), resposta(),
    ])
    c.get("/endpoint")
    c.get("/endpoint")
    assert tempo.esperas == [11]


def test_code_search_tem_cota_separada():
    c, _, tempo = cliente([
        resposta(headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "110"}),
        resposta(), resposta(),
    ])
    c.get("/search/code", {"q": "filename:a.py"})
    c.get("/search/repositories", {"q": "stars:1000"})
    assert tempo.esperas == []
    c.get("/search/code", {"q": "filename:b.py"})
    assert tempo.esperas == [11]


@pytest.mark.parametrize("reset", ["90", "100"])
def test_reset_vencido_nao_gera_espera_negativa(reset):
    c, _, tempo = cliente([
        resposta(403, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": reset}), resposta(),
    ])
    c.get("/repos/org/projeto")
    assert tempo.esperas == ([0] if reset == "90" else [1])


def test_reset_vencido_de_resposta_bem_sucedida_nao_bloqueia():
    c, _, tempo = cliente([
        resposta(headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "90"}), resposta(),
    ])
    c.get("/repos/org/a")
    c.get("/repos/org/b")
    assert tempo.esperas == []


@pytest.mark.parametrize("status", [403, 429])
def test_retry_after_e_respeitado(status):
    c, _, tempo = cliente([resposta(status, {"Retry-After": "7"}), resposta()])
    c.get("/repos/org/projeto")
    assert tempo.esperas == [7]


def test_retry_after_curto_nao_antecipa_reset_primario():
    c, _, tempo = cliente([
        resposta(403, {"Retry-After": "3", "X-RateLimit-Remaining": "0",
                       "X-RateLimit-Reset": "120"}), resposta(),
    ])
    c.get("/repos/org/projeto")
    assert tempo.esperas == [21]


@pytest.mark.parametrize("mensagem", ["API secondary rate limit exceeded", "Abuse detection mechanism"])
def test_limite_secundario_sem_prazo_tem_espera_crescente_e_limite(mensagem):
    c, sessao, tempo = cliente([resposta(403, corpo={"message": mensagem}) for _ in range(5)])
    with pytest.raises(requests.HTTPError):
        c.get("/repos/org/projeto")
    assert len(sessao.chamadas) == 5
    assert tempo.esperas == [60, 120, 240, 480]


def test_429_sem_headers_e_tratado_como_rate_limit():
    c, _, tempo = cliente([resposta(429), resposta()])
    c.get("/repos/org/projeto")
    assert tempo.esperas == [60]


def test_limite_primario_persistente_tem_numero_finito_de_tentativas():
    c, sessao, tempo = cliente([
        resposta(403, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(reset)})
        for reset in (110, 120, 130, 140, 150)
    ])
    with pytest.raises(requests.HTTPError):
        c.get("/repos/org/projeto")
    assert len(sessao.chamadas) == 5
    assert tempo.esperas == [11, 10, 10, 10]


@pytest.mark.parametrize("status", [400, 401, 403, 404, 422])
def test_erros_permanentes_nao_sao_repetidos(status):
    c, sessao, tempo = cliente([resposta(status, corpo={"message": "Forbidden"})])
    with pytest.raises(requests.HTTPError):
        c.get("/repos/org/projeto")
    assert tempo.esperas == []
    assert len(sessao.chamadas) == 1


@pytest.mark.parametrize("corpo", [[], None, "texto"])
def test_403_sem_mensagem_de_rate_limit_nao_e_repetido(corpo):
    r = resposta(403)
    r._content = json.dumps(corpo).encode()
    c, sessao, tempo = cliente([r])
    with pytest.raises(requests.HTTPError):
        c.get("/repos/org/projeto")
    assert tempo.esperas == []
    assert len(sessao.chamadas) == 1


def test_403_nao_json_nao_e_repetido():
    r = resposta(403)
    r._content = b"<html>Forbidden</html>"
    c, _, tempo = cliente([r])
    with pytest.raises(requests.HTTPError):
        c.get("/repos/org/projeto")
    assert tempo.esperas == []


@pytest.mark.parametrize("valor", ["invalido", "-1", None])
def test_headers_invalidos_nao_bloqueiam_resposta_bem_sucedida(valor):
    c, _, tempo = cliente([
        resposta(headers={"X-RateLimit-Remaining": valor, "X-RateLimit-Reset": valor}), resposta(),
    ])
    c.get("/repos/org/a")
    c.get("/repos/org/b")
    assert tempo.esperas == []


def test_reset_e_retry_after_invalidos_usam_espera_secundaria():
    c, _, tempo = cliente([
        resposta(403, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "invalido",
                       "Retry-After": "invalido"}), resposta(),
    ])
    c.get("/repos/org/projeto")
    assert tempo.esperas == [60]


def test_5xx_e_rate_limit_tem_contadores_independentes():
    c, sessao, tempo = cliente([
        resposta(500), resposta(429, {"Retry-After": "7"}), resposta(502), resposta(),
    ])
    c.get("/repos/org/projeto")
    assert tempo.esperas == [1, 7, 2]
    assert len(sessao.chamadas) == 4


def test_5xx_e_reset_esgotado_respeitam_ambos_os_prazos():
    c, _, tempo = cliente([
        resposta(500, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "110"}), resposta(),
    ])
    c.get("/repos/org/projeto")
    assert tempo.esperas == [1, 10]


def test_recuperacao_cacheia_so_sucesso_e_cache_nao_consulta_api(tmp_path):
    cache = CacheDisco(tmp_path)
    c, sessao, tempo = cliente([resposta(503), resposta()], cache)
    c.get("/repos/org/projeto")
    assert len(list(tmp_path.rglob("*.json"))) == 1
    c.get("/repos/org/projeto")
    assert len(sessao.chamadas) == 2
    assert tempo.esperas == [1]


@pytest.mark.parametrize("erro", [requests.Timeout("timeout"), requests.ConnectionError("conexão")])
def test_erros_de_transporte_sao_propagados(erro):
    c, sessao, tempo = cliente([erro])
    with pytest.raises(type(erro)):
        c.get("/repos/org/projeto")
    assert len(sessao.chamadas) == 1
    assert tempo.esperas == []
