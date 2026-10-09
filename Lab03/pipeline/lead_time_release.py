"""Lead time por release (RQ02a): publicação menos data do autor mais antiga (#141)."""

import argparse
import datetime as dt
import json
import logging
import statistics
import sys
from pathlib import Path

from pipeline.cache import gravar_json
from pipeline.classificacao import classificar_metrica
from pipeline.config import ConfigError, janela_utc, load_config

ARQUIVO_ENTRADA = "compare.json"
ARQUIVO_SAIDA = "lead_time_release.json"
log = logging.getLogger(__name__)


def _data(texto):
    try:
        data = dt.datetime.fromisoformat(texto.replace("Z", "+00:00"))
        if data.tzinfo is not None:
            return data.astimezone(dt.timezone.utc)
    except (AttributeError, ValueError):
        pass
    return None


def _iso(data):
    return data.isoformat().replace("+00:00", "Z")


def _ignorar(resultado, motivo):
    return {**resultado, "ignorada": True, "motivo": motivo}


def calcular_release(comparacao):
    """Calcula a variante (a) sem usar a ordem dos commits nem a data do committer.

    Sem uma comparação completa e todas as datas válidas, não há mínimo seguro.
    Ausência de commits produz None; zero representa um intervalo real de zero.
    """
    resultado = {
        "release": dict(comparacao["release"]), "release_anterior": comparacao.get("release_anterior"),
        "lead_time_horas": None, "commit_mais_antigo_sha": None, "commit_mais_antigo_author_date": None,
        "commits_considerados": 0, "ignorada": False, "motivo": None,
        "coleta_incompleta": bool(comparacao.get("coleta_incompleta")),
    }
    if comparacao.get("detalhe"):
        resultado["detalhe"] = comparacao["detalhe"]
    if comparacao.get("ignorada"):
        return _ignorar(resultado, comparacao.get("motivo") or "compare_ignorado")
    if resultado["coleta_incompleta"]:
        return _ignorar(resultado, "compare_incompleto")
    if resultado["release_anterior"] is None:
        return _ignorar(resultado, "sem_release_anterior")
    publicada = _data(resultado["release"].get("published_at"))
    if publicada is None:
        return _ignorar(resultado, "data_release_invalida")

    commits = {}
    for commit in comparacao.get("commits", []):
        sha = commit.get("sha")
        if not isinstance(sha, str) or not sha:
            return _ignorar(resultado, "commit_sem_sha")
        commits.setdefault(sha, commit)
    resultado["commits_considerados"] = len(commits)
    totais = (comparacao.get("total_commits_api"), comparacao.get("total_commits_coletados"))
    if any(total is not None and total != len(commits) for total in totais):
        resultado["coleta_incompleta"] = True
        return _ignorar(resultado, "compare_incompleto")
    if not commits:
        return _ignorar(resultado, "sem_commits_novos")

    datas = []
    for sha, commit in commits.items():
        autor = (commit.get("commit") or {}).get("author") or {}
        data = _data(autor.get("date"))
        if data is None:
            return _ignorar(resultado, "data_commit_invalida")
        datas.append((data, sha))
    antiga, sha = min(datas)
    resultado["commit_mais_antigo_sha"] = sha
    resultado["commit_mais_antigo_author_date"] = _iso(antiga)
    horas = (publicada - antiga).total_seconds() / 3600
    if horas < 0:
        return _ignorar(resultado, "lead_time_negativo")
    resultado["lead_time_horas"] = horas
    return resultado


def calcular_repositorio(repo, inicio, fim):
    """Calcula a mediana por release, conferindo janela e duplicatas por ID."""
    lista, ids = [], set()
    fora, duplicadas = 0, 0
    for comparacao in repo["comparacoes"]:
        release = comparacao["release"]
        publicada = _data(release.get("published_at"))
        if publicada is None:
            raise ConfigError(f"published_at inválido nas releases de {repo['full_name']}.")
        if not inicio <= publicada < fim:
            fora += 1
            continue
        if release.get("id") is None:
            raise ConfigError(f"Release sem ID em {repo['full_name']}.")
        if release["id"] in ids:
            duplicadas += 1
            continue
        ids.add(release["id"])
        lista.append(calcular_release(comparacao))
    lista.sort(key=lambda r: (_data(r["release"]["published_at"]), r["release"]["id"]))
    valores = [r["lead_time_horas"] for r in lista if r["lead_time_horas"] is not None]
    mediana = statistics.median(valores) if valores else None
    ignoradas = [r for r in lista if r["ignorada"]]
    incompleta = bool(repo.get("coleta_incompleta") or any(r["coleta_incompleta"] for r in lista))
    if ignoradas or incompleta:
        log.warning("%s: lead time RQ02a baseado em %d/%d releases; %d ignoradas, coleta incompleta=%s.",
                    repo["full_name"], len(valores), len(lista), len(ignoradas), incompleta)
    return {
        "id": repo["id"], "full_name": repo["full_name"], "default_branch": repo.get("default_branch"),
        "lead_time_horas": mediana, "classe_lead_time": classificar_metrica("lead_time", mediana),
        "total_releases": len(lista), "releases_com_lead_time": len(valores), "releases_ignoradas": len(ignoradas),
        "releases_ignoradas_por_motivo": {motivo: sum(r["motivo"] == motivo for r in ignoradas)
                                         for motivo in sorted({r["motivo"] for r in ignoradas})},
        "releases_fora_janela": fora, "releases_duplicadas": duplicadas,
        "coleta_incompleta": incompleta, "releases": lista,
    }


def executar(config, entrada=None, saida=None):
    """Lê compare da S01-12 e grava a métrica em horas, sem acessar a API."""
    entrada = Path(entrada) if entrada is not None else Path(config["caminhos"]["raw"]) / ARQUIVO_ENTRADA
    saida = Path(saida) if saida is not None else Path(config["caminhos"]["processed"]) / ARQUIVO_SAIDA
    if entrada.resolve() == saida.resolve():
        raise ConfigError("A saída de lead time deve ser diferente do arquivo de compare.")
    if not entrada.is_file():
        raise FileNotFoundError(f"{entrada} não encontrado; execute antes a etapa compare (S01-12).")
    dados = json.loads(entrada.read_text(encoding="utf-8"))
    inicio, fim = janela_utc(config)
    janela = {"inicio": _iso(inicio), "fim_exclusivo": _iso(fim)}
    if dados.get("janela") != janela:
        raise ConfigError("A janela do compare não corresponde à janela configurada para o lead time.")
    if dados.get("definicao_deploy") != "release_estavel":
        raise ConfigError("RQ02a exige compare com definicao_deploy=release_estavel.")
    lista = [calcular_repositorio(repo, inicio, fim) for repo in dados["repositorios"]]
    gravar_json(saida, {
        "gerado_em": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "origem": str(entrada), "janela": janela, "variante": "a", "unidade": "horas",
        "definicao_deploy": "release_estavel", "formula": "published_at - min(commit.author.date)",
        "total_repositorios": len(lista), "repositorios_com_lead_time": sum(r["lead_time_horas"] is not None for r in lista),
        "total_releases": sum(r["total_releases"] for r in lista),
        "releases_com_lead_time": sum(r["releases_com_lead_time"] for r in lista),
        "releases_ignoradas": sum(r["releases_ignoradas"] for r in lista),
        "repositorios_com_coleta_incompleta": sum(r["coleta_incompleta"] for r in lista), "repositorios": lista,
    })
    return saida, lista


def main(argv=None):
    parser = argparse.ArgumentParser(description="Lead time por release (RQ02a) a partir de compare local.")
    parser.add_argument("--config", default="config.yaml", help="caminho da configuração")
    parser.add_argument("--entrada", help="JSON do compare (padrão: caminhos.raw/compare.json)")
    parser.add_argument("--saida", help="JSON de lead time (padrão: caminhos.processed/lead_time_release.json)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        saida, lista = executar(load_config(args.config), args.entrada, args.saida)
    except (ConfigError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    calculadas = sum(r["lead_time_horas"] is not None for r in lista)
    ignoradas = sum(r["releases_ignoradas"] for r in lista)
    print(f"Lead time (RQ02a): {calculadas}/{len(lista)} repositórios com métrica, "
          f"{ignoradas} releases ignoradas -> {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
