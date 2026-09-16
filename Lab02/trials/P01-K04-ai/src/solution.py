"""Esqueleto de K04 — Credenciais de visita.

Implemente a função abaixo seguindo o contrato descrito em ../README.md.
Não altere a assinatura nem o nome da função — a suíte de testes depende
dela.
"""
from __future__ import annotations

_TRANSICOES = {
    "LIBERAR": ("NOVA", "LIBERADA"),
    "USAR": ("LIBERADA", "UTILIZADA"),
}


def _minutos(horario: str) -> int:
    horas, minutos = horario.split(":")
    return int(horas) * 60 + int(minutos)


def avaliar_credenciais(credenciais: list[dict], eventos: list[dict]) -> dict:
    """Retorna os eventos aceitos, os recusados e o estado final de cada
    credencial, conforme as regras descritas em ../README.md.
    """
    estados = {c["credencial"]: "NOVA" for c in credenciais}
    expiracoes = {c["credencial"]: _minutos(c["expiraEm"]) for c in credenciais}

    aceitos: list[str] = []
    recusados: list[str] = []

    for evento in eventos:
        credencial = evento["credencial"]
        acao = evento["acao"]
        momento = _minutos(evento["momento"])
        estado_atual = estados[credencial]
        dentro_do_prazo = momento <= expiracoes[credencial]

        if acao == "REVOGAR":
            permitido = estado_atual in ("NOVA", "LIBERADA")
            novo_estado = "REVOGADA"
        else:
            estado_exigido, novo_estado = _TRANSICOES[acao]
            permitido = estado_atual == estado_exigido

        if dentro_do_prazo and permitido:
            estados[credencial] = novo_estado
            aceitos.append(evento["id"])
        else:
            recusados.append(evento["id"])

    status_final = [
        {"credencial": c["credencial"], "status": estados[c["credencial"]]}
        for c in credenciais
    ]

    return {
        "aceitos": aceitos,
        "recusados": recusados,
        "statusFinal": status_final,
    }
