"""Ordem de coleta: liberar candidatos adiados após um mínimo de elegíveis (#151)."""

from collections import deque
from pipeline.config import ConfigError


def validar(politica, candidatos):
    if not politica:
        return {}
    limite = politica.get("liberar_adiados_com_elegiveis")
    ids = politica.get("adiados_ids")
    if isinstance(limite, bool) or not isinstance(limite, int) or limite < 1:
        raise ConfigError("O mínimo para liberar adiados deve ser um inteiro positivo")
    if not isinstance(ids, list) or any(isinstance(i, bool) or not isinstance(i, int) for i in ids):
        raise ConfigError("adiados_ids deve ser uma lista de IDs inteiros")
    if len(ids) != len(set(ids)) or not set(ids) <= {c["id"] for c in candidatos}:
        raise ConfigError("IDs adiados repetidos ou ausentes na fonte")
    return {"liberar_adiados_com_elegiveis": limite, "adiados_ids": ids}


def iterar(candidatos, politica, total_elegiveis):
    """Consulta o total a cada nova vaga; tarefas já iniciadas terminam normalmente."""
    if not politica:
        yield from candidatos
        return
    ids = set(politica["adiados_ids"])
    normais, adiados = deque(), deque()
    for candidato in candidatos:
        (adiados if candidato["id"] in ids else normais).append(candidato)
    while normais or adiados:
        if adiados and total_elegiveis() >= politica["liberar_adiados_com_elegiveis"]:
            yield adiados.popleft()
        elif normais:
            yield normais.popleft()
        else:
            # Não violar o mínimo para completar uma amostra insuficiente.
            return
