"""Esqueleto de K04 — Credenciais de visita.

Implemente a função abaixo seguindo o contrato descrito em ../README.md.
Não altere a assinatura nem o nome da função — a suíte de testes depende
dela.
"""
from __future__ import annotations


def avaliar_credenciais(credenciais: list[dict], eventos: list[dict]) -> dict:
    """Retorna os eventos aceitos, os recusados e o estado final de cada
    credencial, conforme as regras descritas em ../README.md.
    """
    expira_em = {c["credencial"]: c["expiraEm"] for c in credenciais}
    estado = {c["credencial"]: "NOVA" for c in credenciais}

    aceitos: list[str] = []
    recusados: list[str] = []

    transicoes = {
        "LIBERAR": ("NOVA", "LIBERADA"),
        "USAR": ("LIBERADA", "UTILIZADA"),
        "REVOGAR": None,
    }

    for evento in eventos:
        credencial = evento["credencial"]
        acao = evento["acao"]
        momento = evento["momento"]

        if momento > expira_em[credencial]:
            recusados.append(evento["id"])
            continue

        estado_atual = estado[credencial]

        if acao == "REVOGAR":
            if estado_atual in ("NOVA", "LIBERADA"):
                estado[credencial] = "REVOGADA"
                aceitos.append(evento["id"])
            else:
                recusados.append(evento["id"])
            continue

        origem, destino = transicoes[acao]
        if estado_atual == origem:
            estado[credencial] = destino
            aceitos.append(evento["id"])
        else:
            recusados.append(evento["id"])

    status_final = [
        {"credencial": c["credencial"], "status": estado[c["credencial"]]}
        for c in credenciais
    ]

    return {
        "aceitos": aceitos,
        "recusados": recusados,
        "statusFinal": status_final,
    }
