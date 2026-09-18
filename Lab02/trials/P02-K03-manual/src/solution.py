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

    progresso = {}
    ordem_remessas = []

    aceitos = []
    recusados = []

    for evento in eventos:
        id_evento = evento["id"]
        remessa = evento["remessa"]
        etapa = evento["etapa"]

        if remessa not in progresso:
            if etapa == "COLETA":
                progresso[remessa] = 0
                ordem_remessas.append(remessa)
                aceitos.append(id_evento)
            else:
                recusados.append(id_evento)

            continue

        etapa_atual = progresso[remessa]

        if etapa_atual == len(etapas) - 1:
            recusados.append(id_evento)
            continue

        proxima_etapa = etapas[etapa_atual + 1]

        if etapa == proxima_etapa:
            progresso[remessa] += 1
            aceitos.append(id_evento)
        else:
            recusados.append(id_evento)

    pendentes = []

    for remessa in ordem_remessas:
        if progresso[remessa] < len(etapas) - 1:
            pendentes.append(remessa)

    return {
        "aceitos": aceitos,
        "recusados": recusados,
        "pendentes": pendentes
    }