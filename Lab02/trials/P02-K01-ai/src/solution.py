"""Esqueleto de K01 — Conflitos no pátio de docas.

Implemente a função abaixo seguindo o contrato descrito em ../README.md.
Não altere a assinatura nem o nome da função — a suíte de testes depende
dela.
"""
from __future__ import annotations


def _para_minutos(horario: str) -> int:
    horas, minutos = horario.split(":")
    return int(horas) * 60 + int(minutos)


def conflitos_no_patio(agendamentos: list[dict], margem: int) -> list[str]:
    """Retorna os ids dos agendamentos que conflitam com pelo menos outro
    agendamento da mesma doca, na ordem em que aparecem em `agendamentos`.
    """
    por_doca: dict[str, list[dict]] = {}
    for agendamento in agendamentos:
        por_doca.setdefault(agendamento["doca"], []).append(agendamento)

    conflitantes: set[str] = set()

    for grupo in por_doca.values():
        ordenado = sorted(grupo, key=lambda a: _para_minutos(a["inicio"]))
        for i, atual in enumerate(ordenado):
            inicio_atual = _para_minutos(atual["inicio"])
            fim_atual = _para_minutos(atual["fim"]) + margem
            for outro in ordenado[i + 1 :]:
                inicio_outro = _para_minutos(outro["inicio"])
                fim_outro = _para_minutos(outro["fim"]) + margem
                if inicio_atual < fim_outro and inicio_outro < fim_atual:
                    conflitantes.add(atual["id"])
                    conflitantes.add(outro["id"])

    return [a["id"] for a in agendamentos if a["id"] in conflitantes]
