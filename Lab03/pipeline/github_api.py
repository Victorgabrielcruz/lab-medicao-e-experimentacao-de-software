"""Cliente HTTP mínimo para a API REST do GitHub.

Rate limit e backoff serão tratados na camada própria (S01-17).
"""

import requests

API_VERSION = "2022-11-28"


class GitHubClient:
    def __init__(self, token, base_url="https://api.github.com", timeout_s=30, session=None):
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.session = session or requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
        })

    def get(self, path, params=None):
        response = self.session.get(f"{self.base_url}{path}", params=params, timeout=self.timeout_s)
        response.raise_for_status()
        return response.json()
