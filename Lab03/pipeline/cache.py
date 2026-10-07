"""Cache de respostas GET em JSON, com gravação atômica e retomada por página."""

import hashlib
import json
import logging
import re
import tempfile
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests

log = logging.getLogger(__name__)
VERSAO = 1
HEADERS_PERSISTIDOS = ("Content-Type", "Link")


def gravar_json(caminho, dados):
    """Substitui o arquivo só depois de terminar a escrita no mesmo diretório."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=caminho.parent,
                                         suffix=".tmp", delete=False) as arquivo:
            temporario = Path(arquivo.name)
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
        temporario.replace(caminho)
    finally:
        if temporario is not None:
            temporario.unlink(missing_ok=True)


class CacheDisco:
    def __init__(self, diretorio):
        self.diretorio = Path(diretorio)

    def caminho(self, url):
        """Separa API/repositório e distingue endpoint, filtros e página.

        A ordem das chaves da query não muda a identidade da requisição. Valores
        repetidos da mesma chave mantêm sua ordem. Tokens e headers de
        autenticação não participam da chave nem são persistidos.
        """
        partes = urlsplit(url)
        query = urlencode(sorted(parse_qsl(partes.query, keep_blank_values=True), key=lambda p: p[0]))
        canonica = urlunsplit((partes.scheme, partes.netloc, partes.path, query, ""))
        api = hashlib.sha256(f"{partes.scheme}://{partes.netloc}".encode()).hexdigest()[:16]
        chave = hashlib.sha256(canonica.encode()).hexdigest()
        repo = re.search(r"/repos/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)(?:/|$)", partes.path)
        grupo = f"repo-{repo[1]}--{repo[2]}" if repo else "consultas"
        return self.diretorio / "respostas" / api / grupo / f"{chave}.json"

    def ler(self, url):
        caminho = self.caminho(url)
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
            if (not isinstance(dados, dict) or dados.get("versao") != VERSAO
                    or dados.get("status") not in (200, 204) or "corpo" not in dados
                    or not isinstance(dados.get("headers"), dict)
                    or not all(isinstance(k, str) and isinstance(v, str)
                               for k, v in dados["headers"].items())):
                raise ValueError("formato de cache inválido")
        except FileNotFoundError:
            return None
        except (ValueError, UnicodeError):
            log.warning("Cache inválido em %s; a resposta será consultada novamente.", caminho)
            return None

        resposta = requests.Response()
        resposta.status_code = dados["status"]
        resposta.headers.update(dados["headers"])
        resposta.encoding = "utf-8"
        resposta.url = url
        resposta._content = (b"" if resposta.status_code == 204 else
                             json.dumps(dados["corpo"], ensure_ascii=False).encode("utf-8"))
        return resposta

    def gravar(self, url, resposta):
        """Guarda apenas JSON bem-sucedido; erros e buscas incompletas são repetidos."""
        if resposta.status_code not in (200, 204):
            return
        try:
            corpo = None if resposta.status_code == 204 else resposta.json()
        except ValueError:
            return
        if isinstance(corpo, dict) and corpo.get("incomplete_results"):
            return
        gravar_json(self.caminho(url), {
            "versao": VERSAO,
            "status": resposta.status_code,
            "headers": {h: resposta.headers[h] for h in HEADERS_PERSISTIDOS if h in resposta.headers},
            "corpo": corpo,
        })

    def limpar(self):
        """Remove só os JSON das áreas de cache conhecidas, incluindo metadados."""
        raiz = self.diretorio.resolve()
        arquivos = []
        for nome in ("respostas", "metadados"):
            pasta = self.diretorio / nome
            if not pasta.resolve().is_relative_to(raiz):
                raise ValueError(f"Área de cache fora do diretório configurado: {pasta}")
            for arquivo in pasta.rglob("*.json"):
                if not arquivo.resolve().is_relative_to(raiz):
                    raise ValueError(f"Arquivo de cache fora do diretório configurado: {arquivo}")
                if arquivo.is_file():
                    arquivos.append(arquivo)
        for arquivo in arquivos:
            arquivo.unlink()
        return len(arquivos)
