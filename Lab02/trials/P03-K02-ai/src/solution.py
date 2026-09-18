"""Esqueleto de K02 — Compartimentos de coleta.

Implemente a função abaixo seguindo o contrato descrito em ../README.md.
Não altere a assinatura nem o nome da função — a suíte de testes depende
dela.
"""
from __future__ import annotations


def processar_movimentos(capacidades: list[dict], movimentos: list[dict]) -> dict:
    """Retorna os movimentos aceitos, os recusados e o saldo final de cada
    compartimento, conforme as regras descritas em ../README.md.
    """
    capacidade_por_compartimento = {
        item["compartimento"]: item["capacidade"] for item in capacidades
    }
    saldo_por_compartimento = {
        item["compartimento"]: 0 for item in capacidades
    }
    aceitos = []
    recusados = []

    for movimento in movimentos:
        compartimento = movimento["compartimento"]
        saldo_atual = saldo_por_compartimento[compartimento]
        quantidade = movimento["quantidade"]

        if movimento["tipo"] == "ENTRADA":
            saldo_candidato = saldo_atual + quantidade
            aceito = saldo_candidato <= capacidade_por_compartimento[compartimento]
        else:
            saldo_candidato = saldo_atual - quantidade
            aceito = saldo_candidato >= 0

        if aceito:
            saldo_por_compartimento[compartimento] = saldo_candidato
            aceitos.append(movimento["id"])
        else:
            recusados.append(movimento["id"])

    return {
        "aceitos": aceitos,
        "recusados": recusados,
        "saldoFinal": [
            {
                "compartimento": item["compartimento"],
                "saldo": saldo_por_compartimento[item["compartimento"]],
            }
            for item in capacidades
        ],
    }
