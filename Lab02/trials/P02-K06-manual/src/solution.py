"""Esqueleto de K06 — Roteiros de inspeção.

Implemente a função abaixo seguindo o contrato descrito em ../README.md.
Não altere a assinatura nem o nome da função — a suíte de testes depende
dela.
"""
from __future__ import annotations


def avaliar_visitas(roteiros: list[dict], visitas: list[dict]) -> dict:
    """Retorna as visitas aceitas, as recusadas, as rotas concluídas e as
    pendentes, conforme as regras descritas em ../README.md.
    """

    aceitos = []
    recusados = []
    progresso = {}

    for roteiro in roteiros:
        progresso[roteiro["rota"]] = 0

    for visita in visitas:
        rota = visita["rota"]
        ponto = visita["ponto"]

        roteiro = next(r for r in roteiros if r["rota"] == rota)
        posicao = progresso[rota]

        if posicao < len(roteiro["pontos"]) and ponto == roteiro["pontos"][posicao]:
            aceitos.append(visita["id"])
            progresso[rota] += 1
        else:
            recusados.append(visita["id"])

    concluidas = []
    pendentes = []

    for roteiro in roteiros:
        rota = roteiro["rota"]

        if progresso[rota] == len(roteiro["pontos"]):
            concluidas.append(rota)
        else:
            pendentes.append(rota)

    return {
        "aceitos": aceitos,
        "recusados": recusados,
        "concluidas": concluidas,
        "pendentes": pendentes
    }