"""Esqueleto de K03 — Cadeia de custódia de remessas.

Implemente a função abaixo seguindo o contrato descrito em ../README.md.
Não altere a assinatura nem o nome da função — a suíte de testes depende
dela.
"""
from __future__ import annotations


def avaliar_cadeia_de_custodia(eventos: list[dict]) -> dict:
    """Retorna os eventos aceitos, os recusados e as remessas pendentes,
    conforme as regras descritas em ../README.md.
    """
    etapas = ["COLETA", "LACRE", "DESPACHO", "RECEBIMENTO"]
    estado_por_remessa: dict[str, int] = {}
    aceitos: list[str] = []
    recusados: list[str] = []

    for evento in eventos:
        remessa = evento["remessa"]
        etapa = evento["etapa"]
        proximo_indice = estado_por_remessa.get(remessa, -1) + 1

        if proximo_indice < len(etapas) and etapa == etapas[proximo_indice]:
            estado_por_remessa[remessa] = proximo_indice
            aceitos.append(evento["id"])
        else:
            recusados.append(evento["id"])

    pendentes = [
        remessa
        for remessa, indice in estado_por_remessa.items()
        if indice != len(etapas) - 1
    ]

    return {
        "aceitos": aceitos,
        "recusados": recusados,
        "pendentes": pendentes,
    }
