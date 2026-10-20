"""Consolidados com um repositório por linha, gravados e lidos sem carregar tudo na memória (#151).

O arquivo continua sendo um único JSON válido, com as mesmas chaves:

    {"janela": {...}, "repositorios": [
    {"id": 1, ...},
    {"id": 2, ...}
    ], "descartes": [...]}

Consolidados antigos, em qualquer formatação, são lidos inteiros como antes.
"""

import hashlib
import json
import tempfile
from pathlib import Path
from pipeline.cache import substituir_atomico

ABERTURA = '"repositorios": [\n'
BLOCO = 1024 * 1024


def gravar(caminho, cabecalho, repositorios, rodape=None):
    """Grava um repositório por vez e substitui o arquivo só depois de terminar."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    antes = json.dumps(cabecalho, ensure_ascii=False)[1:-1]
    temporario, total = None, 0
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=caminho.parent,
                                         suffix=".tmp", delete=False) as arquivo:
            temporario = Path(arquivo.name)
            arquivo.write("{" + antes + (", " if antes else "") + ABERTURA)
            for repo in repositorios:
                arquivo.write((",\n" if total else "") + json.dumps(repo, ensure_ascii=False))
                total += 1
            depois = json.dumps((rodape() if callable(rodape) else rodape) or {}, ensure_ascii=False)[1:-1]
            arquivo.write(("\n" if total else "") + "]" + (", " if depois else "") + depois + "}\n")
        substituir_atomico(temporario, caminho)
    finally:
        if temporario is not None:
            temporario.unlink(missing_ok=True)
    return total


def _ultima_linha(arquivo):
    """Lê do fim para o começo até achar a linha que fecha a lista."""
    arquivo.seek(0, 2)
    posicao, dados = arquivo.tell(), b""
    while posicao > 0:
        passo = min(BLOCO, posicao)
        posicao -= passo
        arquivo.seek(posicao)
        dados = arquivo.read(passo) + dados
        corte = dados.rstrip(b"\n").rfind(b"\n")
        if corte >= 0:
            return dados[corte + 1:]
    return dados


def cabecalho(caminho):
    """Devolve as chaves do consolidado, sem a lista de repositórios."""
    with Path(caminho).open("rb") as arquivo:
        primeira = arquivo.readline().decode("utf-8")
        if primeira.endswith(ABERTURA):
            dados = json.loads(primeira + _ultima_linha(arquivo).decode("utf-8"))
        else:
            arquivo.seek(0)
            dados = json.loads(arquivo.read().decode("utf-8"))
    dados.pop("repositorios", None)
    return dados


def repositorios(caminho):
    """Entrega um repositório por vez, na ordem do arquivo."""
    with Path(caminho).open(encoding="utf-8", newline="\n") as arquivo:
        if not arquivo.readline().endswith(ABERTURA):
            arquivo.seek(0)
            yield from json.load(arquivo)["repositorios"]
            return
        for linha in arquivo:
            if linha.startswith("]"):
                return
            yield json.loads(linha.rstrip("\n").removesuffix(","))


def sha256(caminho):
    """Hash do arquivo lido em blocos."""
    resumo = hashlib.sha256()
    with Path(caminho).open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(BLOCO), b""):
            resumo.update(bloco)
    return resumo.hexdigest()
