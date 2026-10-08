"""Cliente REST do GitHub com cache, controle de rate limit e backoff (S01-17)."""

import time
import requests

from pipeline.rate_limit import ControleRequisicoes

API_VERSION = "2022-11-28"


class GitHubClient:
    def __init__(self, token, base_url="https://api.github.com", timeout_s=30, session=None, cache=None,
                 sleep=time.sleep, relogio=time.time):
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.session = session or requests.Session()
        self.cache = cache
        self.controle = ControleRequisicoes(sleep, relogio)
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
        })

    def get_resposta(self, path, params=None):
        """Faz o GET e devolve a resposta inteira (para quem precisa dos headers)."""
        url = requests.Request("GET", f"{self.base_url}{path}", params=params).prepare().url
        if self.cache is not None:
            salva = self.cache.ler(url)
            if salva is not None:
                return salva
        response = self.controle.executar(
            lambda: self.session.get(f"{self.base_url}{path}", params=params, timeout=self.timeout_s), path,
        )
        if self.cache is not None:
            self.cache.gravar(url, response)
        return response

    def get(self, path, params=None):
        return self.get_resposta(path, params).json()
