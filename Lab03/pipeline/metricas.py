"""Métricas das RQ01 a RQ04 em todas as variantes, uma linha por repositório (#152)."""

import argparse
import datetime as dt
import json
import logging
import sys
from pathlib import Path

from pipeline import cfr, lead_time_commit, lead_time_release, tempo_recuperacao
from pipeline.cache import gravar_json
from pipeline.config import ConfigError, janela_utc, load_config

ARQUIVO_SAIDA = "metricas.json"
ARQUIVO_FREQUENCIA = "deployment_frequency.json"
# Saída esperada da heurística de release corretiva (#161), no formato de cfr.json.
ARQUIVO_CFR_B = "cfr_b.json"
# (métrica, arquivo em processed, campo do valor, campo da classe)
FONTES = (
    ("deployment_frequency", ARQUIVO_FREQUENCIA, "deployment_frequency", "classe"),
    ("lead_time_a", lead_time_release.ARQUIVO_SAIDA, "lead_time_horas", "classe_lead_time"),
    ("lead_time_b", lead_time_commit.ARQUIVO_SAIDA, "lead_time_horas", "classe_lead_time"),
    ("cfr_a", cfr.ARQUIVO_SAIDA, "change_failure_rate", "classe_cfr"),
    ("cfr_b", ARQUIVO_CFR_B, "change_failure_rate", "classe_cfr"),
    ("tempo_recuperacao", tempo_recuperacao.ARQUIVO_SAIDA, "tempo_recuperacao", "classe_tempo_recuperacao"),
)
METRICAS = tuple(metrica for metrica, *_ in FONTES)
OPCIONAIS = frozenset({"cfr_b"})
UNIDADES = {"deployment_frequency": "releases_por_semana", "lead_time_a": "horas", "lead_time_b": "horas",
            "cfr_a": "fracao", "cfr_b": "fracao", "tempo_recuperacao": "horas"}
log = logging.getLogger(__name__)


def _iso(data):
    return data.isoformat(timespec="seconds").replace("+00:00", "Z")


def _ler(caminho, janela):
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    if dados.get("janela") != janela:
        raise ConfigError(f"A janela de {caminho.name} não corresponde à janela configurada.")
    return dados


def consolidar(fontes):
    """Junta por ID as métricas já calculadas; o que falta fica None, nunca zero.

    `fontes` mapeia cada métrica à lista de repositórios da sua saída. Uma
    métrica sem fonte fica ausente para todos os repositórios.
    """
    linhas = {}
    for metrica, _, campo, campo_classe in FONTES:
        vistos = set()
        for repo in fontes.get(metrica, []):
            if repo["id"] in vistos:
                raise ConfigError(f"Repositório {repo['full_name']} duplicado na saída de {metrica}.")
            vistos.add(repo["id"])
            linha = linhas.setdefault(repo["id"], {
                "id": repo["id"], "full_name": repo["full_name"],
                **{chave: None for m in METRICAS for chave in (m, f"classe_{m}")},
                "coleta_incompleta": False, "calculo_parcial": False})
            if linha["full_name"].lower() != repo["full_name"].lower():
                raise ConfigError(f"Identidade divergente para o repositório {repo['id']} em {metrica}.")
            linha[metrica] = repo[campo]
            linha[f"classe_{metrica}"] = repo[campo_classe]
            linha["coleta_incompleta"] = linha["coleta_incompleta"] or bool(repo.get("coleta_incompleta"))
            linha["calculo_parcial"] = linha["calculo_parcial"] or bool(repo.get("calculo_parcial"))
    for linha in linhas.values():
        linha["metricas_ausentes"] = [m for m in METRICAS if linha[m] is None]
    return list(linhas.values())


def executar(config, saida=None):
    """Lê as saídas locais de cada métrica e grava o resultado por repositório, sem acessar a API."""
    raw, processed = (Path(config["caminhos"][k]) for k in ("raw", "processed"))
    saida = Path(saida) if saida is not None else processed / ARQUIVO_SAIDA
    inicio, fim = janela_utc(config)
    janela = {"inicio": _iso(inicio), "fim_exclusivo": _iso(fim)}
    lead_b = processed / lead_time_commit.ARQUIVO_SAIDA
    if not lead_b.is_file() and (raw / lead_time_commit.ARQUIVO_ENTRADA).is_file():
        lead_time_commit.executar(config)
    fontes, origens, pendentes = {}, {}, []
    for metrica, arquivo, *_ in FONTES:
        caminho = processed / arquivo
        if caminho.resolve() == saida.resolve():
            raise ConfigError("A saída das métricas deve ser diferente dos arquivos de entrada.")
        if not caminho.is_file():
            if metrica not in OPCIONAIS:
                raise FileNotFoundError(f"{caminho} não encontrado; calcule antes a métrica {metrica}.")
            pendentes.append(metrica)
            continue
        fontes[metrica] = _ler(caminho, janela)["repositorios"]
        origens[metrica] = str(caminho)
    lista = consolidar(fontes)
    if pendentes:
        log.warning("Variantes ainda não calculadas: %s.", ", ".join(pendentes))
    gravar_json(saida, {
        "gerado_em": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "janela": janela, "origens": origens, "unidades": UNIDADES, "variantes_pendentes": pendentes,
        "total_repositorios": len(lista),
        "repositorios_por_metrica": {m: sum(r[m] is not None for r in lista) for m in METRICAS},
        "repositorios_com_todas_as_metricas": sum(not r["metricas_ausentes"] for r in lista),
        "repositorios_com_coleta_incompleta": sum(r["coleta_incompleta"] for r in lista),
        "repositorios_com_calculo_parcial": sum(r["calculo_parcial"] for r in lista),
        "repositorios": lista,
    })
    return saida, lista, pendentes


def main(argv=None):
    parser = argparse.ArgumentParser(description="Métricas das RQ01 a RQ04 por repositório a partir das saídas locais.")
    parser.add_argument("--config", default="config.yaml", help="caminho da configuração")
    parser.add_argument("--saida", help="JSON consolidado (padrão: caminhos.processed/metricas.json)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        saida, lista, pendentes = executar(load_config(args.config), args.saida)
    except (ConfigError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    completos = sum(not r["metricas_ausentes"] for r in lista)
    print(f"Métricas: {len(lista)} repositórios, {completos} com todas as variantes, "
          f"{len(pendentes)} variantes pendentes -> {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
