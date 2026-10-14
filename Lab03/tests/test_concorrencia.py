import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
import requests

from pipeline.cache import CacheDisco
from pipeline.concorrencia import mapear_ordenado
from pipeline.github_api import GitHubClient


def test_fila_limitada_e_sem_prefetch_da_lista_inteira():
    produzidos = []

    def entradas():
        for i in range(1000):
            produzidos.append(i)
            yield i

    with mapear_ordenado(lambda i: i, entradas(), 2) as resultados:
        assert next(resultados) == 0
        assert produzidos == [0, 1]
    assert produzidos == [0, 1]


def test_fila_encolhe_perto_do_alvo_sem_coletar_extras():
    restantes = 3
    chamadas = []

    def buscar(i):
        chamadas.append(i)
        return i

    with mapear_ordenado(buscar, range(100), 4, limite=lambda: restantes) as resultados:
        for _ in resultados:
            restantes -= 1
            if restantes == 0:
                break
    assert sorted(chamadas) == [0, 1, 2]


def test_erro_da_tarefa_e_propagado_sem_submeter_restante():
    chamadas = []

    def buscar(i):
        chamadas.append(i)
        if i == 0:
            raise requests.ConnectionError("interrupção")
        return i

    with pytest.raises(requests.ConnectionError):
        with mapear_ordenado(buscar, range(100), 2) as resultados:
            list(resultados)
    assert all(i < 2 for i in chamadas)


def test_cliente_limita_http_global_e_isola_sessoes_por_thread(tmp_path):
    trava = threading.Lock()
    sessoes = []
    ativas = maximo = 0

    class Sessao:
        def __init__(self):
            self.headers = {}
            self.threads = set()
            self.fechada = False
            sessoes.append(self)

        def get(self, url, params, timeout):
            nonlocal ativas, maximo
            with trava:
                self.threads.add(threading.get_ident())
                ativas += 1
                maximo = max(maximo, ativas)
            try:
                time.sleep(0.02)
                r = requests.Response()
                r.status_code = 200
                r._content = b'{"ok": true}'
                return r
            finally:
                with trava:
                    ativas -= 1

        def close(self):
            self.fechada = True

    client = GitHubClient("fixture", paralelismo=2, session_factory=Sessao, cache=CacheDisco(tmp_path))
    try:
        with ThreadPoolExecutor(max_workers=6) as executor:
            resultados = list(executor.map(lambda i: client.get(f"/repos/org/repo{i}"), range(12)))
        assert resultados == [{"ok": True}] * 12
        assert maximo == 2
        assert all(len(s.threads) == 1 for s in sessoes)
        assert all(s.headers["Authorization"] == "Bearer fixture" for s in sessoes)
        assert client.get("/repos/org/repo0") == {"ok": True}
        assert client.estatisticas()["requisicoes"] == 12
        assert client.estatisticas()["cache_hits"] == 1
    finally:
        client.close()
    assert all(s.fechada for s in sessoes)


def test_pool_de_paginas_e_reutilizado_entre_fatias():
    client = GitHubClient("fixture", paralelismo=2)
    try:
        assert list(client.mapear_paginas(lambda i: i, range(3))) == [0, 1, 2]
        pool = client._pool_paginas
        assert list(client.mapear_paginas(lambda i: i, range(2))) == [0, 1]
        assert client._pool_paginas is pool
    finally:
        client.close()
