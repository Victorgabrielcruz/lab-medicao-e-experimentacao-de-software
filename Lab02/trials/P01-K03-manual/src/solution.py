"""Esqueleto de K03 — Cadeia de custódia de remessas.

Implemente a função abaixo seguindo o contrato descrito em ../README.md.
Não altere a assinatura nem o nome da função — a suíte de testes depende
dela.
"""
from __future__ import annotations


def avaliar_cadeia_de_custodia(eventos: list[dict]) -> dict:
    aceitos = []
    recusados = []
    estado_remessas = {}
    ordem_pendentes = []

    transicoes_validas = {
        None: "COLETA",
        "COLETA": "LACRE",
        "LACRE": "DESPACHO",
        "DESPACHO": "RECEBIMENTO",
        "RECEBIMENTO": None
    }

    for evento in eventos:
        id_evento = evento["id"]
        remessa = evento["remessa"]
        etapa = evento["etapa"]

        estado_atual = estado_remessas.get(remessa, None)
        etapa_esperada = transicoes_validas[estado_atual]

        if etapa == etapa_esperada:
            aceitos.append(id_evento)
            estado_remessas[remessa] = etapa

            if etapa == etapa_esperada:
                aceitos.append(id_evento)
                estado_remessas[remessa] = etapa

                if estado_atual is None:
                    ordem_pendentes.append(remessa)

            else:
                recusados.append(id_evento)

        pendentes = [remessa for remessa in ordem_pendentes if estado_remessas[remessa] != "RECEBIMENTO"]

    return {
        "aceitos": aceitos,
        "recusados": recusados,
        "pendentes": pendentes
    }