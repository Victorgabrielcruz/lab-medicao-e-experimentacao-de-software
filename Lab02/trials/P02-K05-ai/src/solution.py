"""Esqueleto de K05 — Alertas de leitura persistente.

Implemente a função abaixo seguindo o contrato descrito em ../README.md.
Não altere a assinatura nem o nome da função — a suíte de testes depende
dela.
"""
from __future__ import annotations


def gerar_alertas(
    sensores: list[dict], consecutivas: int, leituras: list[dict]
) -> list[dict]:
    """Retorna a lista de alertas emitidos, na ordem em que ocorreram,
    conforme as regras descritas em ../README.md.
    """

    limites = {}
    contadores = {}
    alertados = {}

    for sensor in sensores:
        nome = sensor["sensor"]

        limites[nome] = {
            "minimo": sensor["minimo"],
            "maximo": sensor["maximo"]
        }

        contadores[nome] = 0
        alertados[nome] = False

    alertas = []

    for leitura in leituras:
        nome = leitura["sensor"]
        valor = leitura["valor"]

        minimo = limites[nome]["minimo"]
        maximo = limites[nome]["maximo"]

        fora_da_faixa = valor < minimo or valor > maximo

        if fora_da_faixa:
            contadores[nome] += 1

            if contadores[nome] == consecutivas and not alertados[nome]:
                alertas.append({
                    "sensor": nome,
                    "leitura": leitura["id"]
                })

                alertados[nome] = True

        else:
            contadores[nome] = 0
            alertados[nome] = False

    return alertas