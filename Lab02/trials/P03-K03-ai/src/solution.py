"""Implementação cronometrada de K03 — Cadeia de custódia de remessas."""
from __future__ import annotations


def avaliar_cadeia_de_custodia(eventos: list[dict]) -> dict:
    etapas = ("COLETA", "LACRE", "DESPACHO", "RECEBIMENTO")
    progresso: dict[str, int] = {}
    ordem_remessas: list[str] = []
    aceitos: list[str] = []
    recusados: list[str] = []

    for evento in eventos:
        remessa = evento["remessa"]
        etapa = evento["etapa"]
        indice_atual = progresso.get(remessa, -1)
        indice_esperado = indice_atual + 1

        if indice_esperado < len(etapas) and etapa == etapas[indice_esperado]:
            if remessa not in progresso:
                ordem_remessas.append(remessa)
            progresso[remessa] = indice_esperado
            aceitos.append(evento["id"])
        else:
            recusados.append(evento["id"])

    return {
        "aceitos": aceitos,
        "recusados": recusados,
        "pendentes": [
            remessa
            for remessa in ordem_remessas
            if progresso[remessa] < len(etapas) - 1
        ],
    }
