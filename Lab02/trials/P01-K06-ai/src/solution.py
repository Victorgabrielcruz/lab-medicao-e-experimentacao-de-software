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
    pontos_por_rota = {r["rota"]: r["pontos"] for r in roteiros}
    proximo_indice = {r["rota"]: 0 for r in roteiros}

    aceitos: list[str] = []
    recusados: list[str] = []

    for visita in visitas:
        rota = visita["rota"]
        pontos = pontos_por_rota[rota]
        indice = proximo_indice[rota]

        concluida = indice == len(pontos)
        se_esperado = not concluida and visita["ponto"] == pontos[indice]

        if se_esperado:
            proximo_indice[rota] = indice + 1
            aceitos.append(visita["id"])
        else:
            recusados.append(visita["id"])

    concluidas = [
        r["rota"] for r in roteiros
        if proximo_indice[r["rota"]] == len(r["pontos"])
    ]
    pendentes = [
        r["rota"] for r in roteiros
        if proximo_indice[r["rota"]] != len(r["pontos"])
    ]

    return {
        "aceitos": aceitos,
        "recusados": recusados,
        "concluidas": concluidas,
        "pendentes": pendentes,
    }
