"""Seleção de repositórios candidatos pela Search API.

A Search API devolve no máximo 1000 resultados por consulta. A busca começa com a
faixa de estrelas inteira e divide a faixa ao meio enquanto o total passar desse
limite. Uma faixa de um único valor de estrelas que ainda passe do limite não pode
ser dividida: ela é coletada até 1000 resultados e marcada como truncada.
"""

import datetime as dt
import json
import logging
import math
import time
from pathlib import Path

from pipeline.config import ConfigError

SEARCH_LIMIT = 1000
PER_PAGE = 100
ARQUIVO_SAIDA = "candidatos.json"

log = logging.getLogger(__name__)


def validar_busca(busca):
    lo, hi = busca.get("estrelas_min"), busca.get("estrelas_max")
    if not all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in (lo, hi)) or lo > hi:
        raise ConfigError("busca.estrelas_min e busca.estrelas_max devem ser inteiros com mínimo <= máximo.")
    if not isinstance(busca.get("qualificadores", []), list) or not isinstance(busca.get("linguagens", []), list):
        raise ConfigError("busca.qualificadores e busca.linguagens devem ser listas.")


def montar_query(lo, hi, qualificadores, linguagem=None):
    partes = [f"stars:{lo}..{hi}", *qualificadores]
    if linguagem:
        partes.append(f'language:"{linguagem}"')
    return " ".join(partes)


def _resumo(item):
    return {
        "id": item["id"],
        "full_name": item["full_name"],
        "html_url": item["html_url"],
        "estrelas": item["stargazers_count"],
        "linguagem": item.get("language"),
    }


def coletar(buscar_pagina, estrelas_min, estrelas_max, qualificadores, linguagens=()):
    """Percorre as fatias e devolve (fatias, candidatos sem duplicatas).

    `buscar_pagina(query, pagina)` deve devolver a resposta da Search API.
    """
    pendentes = [(lang, estrelas_min, estrelas_max) for lang in (linguagens or [None])]
    fatias, candidatos = [], {}

    while pendentes:
        linguagem, lo, hi = pendentes.pop(0)
        query = montar_query(lo, hi, qualificadores, linguagem)
        primeira = buscar_pagina(query, 1)
        total = primeira["total_count"]

        if total > SEARCH_LIMIT and lo < hi:
            meio = (lo + hi) // 2
            pendentes[:0] = [(linguagem, lo, meio), (linguagem, meio + 1, hi)]
            continue

        truncada = total > SEARCH_LIMIT
        if truncada:
            log.warning("Fatia com %d resultados (limite %d); coletando só os primeiros: %s", total, SEARCH_LIMIT, query)

        itens = list(primeira["items"])
        paginas = math.ceil(min(total, SEARCH_LIMIT) / PER_PAGE)
        for pagina in range(2, paginas + 1):
            itens.extend(buscar_pagina(query, pagina)["items"])

        incompleta = bool(primeira.get("incomplete_results"))
        if incompleta:
            log.warning("A Search API indicou resultados incompletos para: %s", query)

        for item in itens:
            candidatos.setdefault(item["id"], _resumo(item))
        fatias.append({"query": query, "total_count": total, "coletados": len(itens),
                       "truncada": truncada, "incompleta": incompleta})

    ordenados = sorted(candidatos.values(), key=lambda r: (-r["estrelas"], r["full_name"]))
    return fatias, ordenados


def com_intervalo(funcao, intervalo_s, sleep=time.sleep, relogio=time.monotonic):
    """Garante um intervalo mínimo entre chamadas (Search API: 30 req/min)."""
    ultima = [None]

    def chamar(*args, **kwargs):
        if ultima[0] is not None:
            espera = intervalo_s - (relogio() - ultima[0])
            if espera > 0:
                sleep(espera)
        ultima[0] = relogio()
        return funcao(*args, **kwargs)

    return chamar


def executar(config, client):
    """Executa a etapa e grava a lista de candidatos em <caminhos.raw>/candidatos.json."""
    busca = config["busca"]
    validar_busca(busca)
    qualificadores = [*busca.get("qualificadores", []), f"pushed:>={config['janela']['inicio']}"]

    def buscar_pagina(query, pagina):
        return client.get("/search/repositories", {
            "q": query, "sort": "stars", "order": "desc", "per_page": PER_PAGE, "page": pagina,
        })

    fatias, candidatos = coletar(
        com_intervalo(buscar_pagina, busca.get("intervalo_s", 0)),
        busca["estrelas_min"], busca["estrelas_max"], qualificadores, busca.get("linguagens", []),
    )

    saida = Path(config["caminhos"]["raw"]) / ARQUIVO_SAIDA
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps({
        "gerado_em": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "total_candidatos": len(candidatos),
        "fatias_truncadas": sum(f["truncada"] for f in fatias),
        "fatias": fatias,
        "candidatos": candidatos,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return saida, fatias, candidatos
