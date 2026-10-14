"""Cliente REST do GitHub com cache, controle de rate limit e backoff (S01-17)."""

import time
import threading
from concurrent.futures import ThreadPoolExecutor
import requests

from pipeline.rate_limit import ControleRequisicoes

API_VERSION = "2022-11-28"
PARALELISMO_MAXIMO = 8


class GitHubClient:
    def __init__(self, token, base_url="https://api.github.com", timeout_s=30, session=None, cache=None,
                 sleep=time.sleep, relogio=time.time, paralelismo=1, session_factory=None):
        if isinstance(paralelismo, bool) or not isinstance(paralelismo, int) or not 1 <= paralelismo <= PARALELISMO_MAXIMO:
            raise ValueError(f"api.paralelismo deve ser um inteiro de 1 a {PARALELISMO_MAXIMO}.")
        # Teto global: inclui repositórios, páginas e novas tentativas.
        self.paralelismo = paralelismo
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self._session_injetada = session
        self._session_factory = session_factory or requests.Session
        self._local = threading.local()
        self._sessoes = []
        self._trava = threading.Lock()
        self._trava_injetada = threading.Lock()
        self._pool_paginas = None
        self._cache_hits = 0
        self.cache = cache
        self.controle = ControleRequisicoes(sleep, relogio, paralelismo)
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
        }
        if session is not None:
            session.headers.update(self._headers)

    @property
    def session(self):
        if self._session_injetada is not None:
            return self._session_injetada
        if not hasattr(self._local, "session"):
            sessao = self._session_factory()
            sessao.headers.update(self._headers)
            self._local.session = sessao
            with self._trava:
                self._sessoes.append(sessao)
        return self._local.session

    def _requisitar(self, path, params):
        if self._session_injetada is not None:
            # Sessões fornecidas pelo chamador também não são usadas simultaneamente.
            with self._trava_injetada:
                return self.session.get(f"{self.base_url}{path}", params=params, timeout=self.timeout_s)
        return self.session.get(f"{self.base_url}{path}", params=params, timeout=self.timeout_s)

    def mapear_paginas(self, buscar, paginas):
        # Reutiliza as threads e suas conexões entre meses e repositórios.
        with self._trava:
            if self._pool_paginas is None:
                self._pool_paginas = ThreadPoolExecutor(max_workers=self.paralelismo)
            pool = self._pool_paginas
        return pool.map(buscar, paginas)

    def estatisticas(self):
        dados = self.controle.estatisticas()
        with self._trava:
            dados["cache_hits"] = self._cache_hits
        return dados

    def close(self):
        if self._pool_paginas is not None:
            self._pool_paginas.shutdown(wait=True, cancel_futures=True)
        for sessao in self._sessoes:
            sessao.close()
        self._sessoes.clear()

    def get_resposta(self, path, params=None):
        """Faz o GET e devolve a resposta inteira (para quem precisa dos headers)."""
        url = requests.Request("GET", f"{self.base_url}{path}", params=params).prepare().url
        if self.cache is not None:
            salva = self.cache.ler(url)
            if salva is not None:
                with self._trava:
                    self._cache_hits += 1
                return salva
        response = self.controle.executar(
            lambda: self._requisitar(path, params), path,
        )
        if self.cache is not None:
            self.cache.gravar(url, response)
        return response

    def get(self, path, params=None):
        return self.get_resposta(path, params).json()
