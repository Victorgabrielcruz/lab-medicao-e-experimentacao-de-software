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
    estado = {c["credencial"]: "NOVA" for c in credenciais}
    expira_em = {c["credencial"]: c["expiraEm"] for c in credenciais}

    aceitos: list[str] = []
    recusados: list[str] = []

    for evento in eventos:
        credencial = evento["credencial"]
        acao = evento["acao"]
        momento = evento["momento"]
        atual = estado[credencial]

        if momento > expira_em[credencial]:
            recusados.append(evento["id"])
            continue

        if acao == "LIBERAR" and atual == "NOVA":
            estado[credencial] = "LIBERADA"
            aceitos.append(evento["id"])
        elif acao == "USAR" and atual == "LIBERADA":
            estado[credencial] = "UTILIZADA"
            aceitos.append(evento["id"])
        elif acao == "REVOGAR" and atual in ("NOVA", "LIBERADA"):
            estado[credencial] = "REVOGADA"
            aceitos.append(evento["id"])
        else:
            recusados.append(evento["id"])

    return {
        "aceitos": aceitos,
        "recusados": recusados,
        "statusFinal": [
            {"credencial": c["credencial"], "status": estado[c["credencial"]]}
            for c in credenciais
        ],
    }
