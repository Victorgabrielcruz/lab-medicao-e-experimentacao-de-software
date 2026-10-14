"""Sorteio da amostra-ouro e planilhas de rotulagem da validação manual (#155)."""

import argparse
import csv
import datetime as dt
import hashlib
import json
import logging
import sys
from pathlib import Path
from urllib.parse import quote

import pandas as pd

from pipeline.cache import gravar_json
from pipeline.config import ConfigError, janela_utc, load_config

ARQUIVO_AMOSTRA = "deployment_frequency.json"  # elegíveis completos do pipeline integrado
ARQUIVO_RELEASES = "releases.json"
ARQUIVO_SORTEIO = "amostra_ouro.json"
PASTA_SAIDA = "validacao/amostra-ouro"
TOTAL_REPOSITORIOS = 60
RELEASES_POR_REPOSITORIO = 5
RANDOM_STATE = 42
ROTULADORES = ("A", "B", "C")
GITHUB = "https://github.com"
# As colunas de rótulo saem vazias; cada integrante preenche a sua planilha.
COLUNAS_REPOSITORIOS = ("repo_id", "full_name", "repositorio_url", "releases_url",
                        "tipo_projeto", "releases_sao_entregas_reais", "observacoes")
COLUNAS_RELEASES = ("repo_id", "full_name", "release_id", "tag_name", "nome", "published_at",
                    "release_url", "compare_url", "corretiva", "observacoes")
log = logging.getLogger(__name__)


def _iso(data):
    return data.isoformat(timespec="seconds").replace("+00:00", "Z")


def _data(texto):
    try:
        data = dt.datetime.fromisoformat(texto.replace("Z", "+00:00"))
        if data.tzinfo is not None:
            return data.astimezone(dt.timezone.utc)
    except (AttributeError, ValueError):
        pass
    return None


def _sortear(itens, quantidade, random_state):
    """Sorteia sem reposição com pandas; `itens` chega em ordem determinística."""
    posicoes = pd.DataFrame({"posicao": range(len(itens))}).sample(n=quantidade, random_state=random_state)
    return [itens[i] for i in posicoes["posicao"]]


def sortear_repositorios(repositorios, quantidade=TOTAL_REPOSITORIOS, random_state=RANDOM_STATE):
    """Sorteia os repositórios da amostra-ouro; a ordem do arquivo de origem não muda o resultado."""
    por_id = {}
    for repo in repositorios:
        if repo["id"] in por_id:
            raise ConfigError(f"Repositório {repo['full_name']} duplicado na amostra final.")
        por_id[repo["id"]] = repo
    if len(por_id) < quantidade:
        raise ConfigError(f"A amostra final tem {len(por_id)} repositórios; o sorteio exige {quantidade}.")
    ordenados = [por_id[i] for i in sorted(por_id)]
    return sorted(_sortear(ordenados, quantidade, random_state), key=lambda r: r["full_name"].lower())


def releases_elegiveis(repo, inicio, fim, incluir_prereleases=False):
    """Releases publicadas na janela, sem drafts nem repetidas, em ordem cronológica."""
    por_id = {}
    for release in repo["releases"]:
        publicada = _data(release.get("published_at"))
        if release.get("draft") is not False or publicada is None or not inicio <= publicada < fim:
            continue
        if release.get("prerelease") is not False and not incluir_prereleases:
            continue
        if release.get("id") is None:
            raise ConfigError(f"Release sem ID em {repo['full_name']}.")
        por_id.setdefault(release["id"], release)
    return sorted(por_id.values(), key=lambda r: (_data(r["published_at"]), r["id"]))


def _url_release(full_name, release):
    return release.get("html_url") or f"{GITHUB}/{full_name}/releases/tag/{quote(str(release['tag_name']), safe='')}"


def sortear_releases(repo, inicio, fim, incluir_prereleases=False,
                     quantidade=RELEASES_POR_REPOSITORIO, random_state=RANDOM_STATE):
    """Sorteia as releases de um repositório e monta os links diretos de cada uma."""
    elegiveis = releases_elegiveis(repo, inicio, fim, incluir_prereleases)
    if len(elegiveis) < quantidade:
        raise ConfigError(f"{repo['full_name']} tem {len(elegiveis)} releases elegíveis; o sorteio exige {quantidade}.")
    anterior = {r["id"]: elegiveis[i - 1] if i else None for i, r in enumerate(elegiveis)}
    sorteadas = sorted(_sortear(elegiveis, quantidade, random_state),
                       key=lambda r: (_data(r["published_at"]), r["id"]))
    lista = []
    for release in sorteadas:
        base = anterior[release["id"]]
        tags = [quote(str(r["tag_name"]), safe="") for r in (base, release) if r is not None]
        lista.append({
            "release_id": release["id"], "tag_name": release["tag_name"], "nome": release.get("name"),
            "published_at": _iso(_data(release["published_at"])),
            "release_url": _url_release(repo["full_name"], release),
            "tag_anterior": base["tag_name"] if base else None,
            "compare_url": f"{GITHUB}/{repo['full_name']}/compare/{tags[0]}...{tags[1]}" if base else None,
        })
    return lista


def sortear(amostra, releases, inicio, fim, incluir_prereleases=False):
    """Devolve os repositórios sorteados, cada um com as suas releases sorteadas."""
    por_id = {r["id"]: r for r in releases}
    lista = []
    for repo in sortear_repositorios(amostra):
        if repo["id"] not in por_id:
            raise ConfigError(f"{repo['full_name']} está na amostra final e não está em {ARQUIVO_RELEASES}.")
        lista.append({
            "repo_id": repo["id"], "full_name": repo["full_name"],
            "repositorio_url": f"{GITHUB}/{repo['full_name']}",
            "releases_url": f"{GITHUB}/{repo['full_name']}/releases",
            "releases": sortear_releases(por_id[repo["id"]], inicio, fim, incluir_prereleases),
        })
    return lista


def _gravar_csv(caminho, colunas, linhas):
    # utf-8-sig para o Excel reconhecer os acentos dos nomes de release.
    with caminho.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows({coluna: linha.get(coluna, "") for coluna in colunas} for linha in linhas)


def gravar_planilhas(pasta, sorteados, sobrescrever=False):
    """Grava as planilhas em branco de cada rotulador, sem apagar rótulos já preenchidos."""
    pasta = Path(pasta)
    caminhos = [pasta / f"rotulador_{letra}_{tipo}.csv" for letra in ROTULADORES for tipo in ("repositorios", "releases")]
    existentes = [c.name for c in caminhos if c.exists()]
    if existentes and not sobrescrever:
        raise ConfigError(f"Planilhas já existem em {pasta} ({', '.join(existentes)}); "
                          "use --sobrescrever para apagar os rótulos e gerar de novo.")
    pasta.mkdir(parents=True, exist_ok=True)
    linhas_releases = [{**release, "repo_id": repo["repo_id"], "full_name": repo["full_name"]}
                       for repo in sorteados for release in repo["releases"]]
    for caminho in caminhos:
        if caminho.name.endswith("_repositorios.csv"):
            _gravar_csv(caminho, COLUNAS_REPOSITORIOS, sorteados)
        else:
            _gravar_csv(caminho, COLUNAS_RELEASES, linhas_releases)
    return caminhos


def _ler(caminho, janela, etapa):
    if not caminho.is_file():
        raise FileNotFoundError(f"{caminho} não encontrado; execute antes {etapa}.")
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    if dados.get("janela") != janela:
        raise ConfigError(f"A janela de {caminho.name} não corresponde à janela configurada.")
    return dados["repositorios"]


def executar(config, amostra=None, releases=None, saida=None, sobrescrever=False):
    """Lê a amostra final e as releases locais; grava o sorteio e as planilhas, sem acessar a API."""
    amostra = Path(amostra) if amostra is not None else Path(config["caminhos"]["processed"]) / ARQUIVO_AMOSTRA
    releases = Path(releases) if releases is not None else Path(config["caminhos"]["raw"]) / ARQUIVO_RELEASES
    saida = Path(saida) if saida is not None else Path(PASTA_SAIDA)
    inicio, fim = janela_utc(config)
    janela = {"inicio": _iso(inicio), "fim_exclusivo": _iso(fim)}
    populacao = _ler(amostra, janela, "o pipeline integrado")
    incluir_prereleases = config["inclusao"].get("incluir_prereleases", True)
    sorteados = sortear(populacao, _ler(releases, janela, "a coleta de releases"), inicio, fim, incluir_prereleases)
    caminhos = gravar_planilhas(saida, sorteados, sobrescrever)
    ids = sorted(r["id"] for r in populacao)
    # Sem data de geração: o mesmo sorteio regrava o mesmo arquivo.
    gravar_json(saida / ARQUIVO_SORTEIO, {
        "janela": janela, "random_state": RANDOM_STATE, "incluir_prereleases": incluir_prereleases,
        "total_populacao": len(ids),
        "populacao_sha256": hashlib.sha256(json.dumps(ids).encode()).hexdigest(),
        "total_repositorios": len(sorteados),
        "releases_por_repositorio": RELEASES_POR_REPOSITORIO,
        "total_releases": sum(len(r["releases"]) for r in sorteados),
        "planilhas": [c.name for c in caminhos],
        "repositorios": sorteados,
    })
    return saida, sorteados


def main(argv=None):
    parser = argparse.ArgumentParser(description="Sorteio da amostra-ouro e planilhas de rotulagem.")
    parser.add_argument("--config", default="config.yaml", help="caminho da configuração")
    parser.add_argument("--amostra", help="JSON da amostra final (padrão: caminhos.processed/deployment_frequency.json)")
    parser.add_argument("--releases", help="JSON das releases (padrão: caminhos.raw/releases.json)")
    parser.add_argument("--saida", help=f"pasta do sorteio e das planilhas (padrão: {PASTA_SAIDA})")
    parser.add_argument("--sobrescrever", action="store_true",
                        help="regrava planilhas existentes, apagando os rótulos já preenchidos")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        saida, sorteados = executar(load_config(args.config), args.amostra, args.releases, args.saida, args.sobrescrever)
    except (ConfigError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    total = sum(len(r["releases"]) for r in sorteados)
    print(f"Amostra-ouro: {len(sorteados)} repositórios, {total} releases, "
          f"{len(ROTULADORES) * 2} planilhas -> {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
