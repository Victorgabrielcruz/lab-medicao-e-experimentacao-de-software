"""Esqueleto de K01 — Conflitos no pátio de docas.

Implemente a função abaixo seguindo o contrato descrito em ../README.md.
Não altere a assinatura nem o nome da função — a suíte de testes depende
dela.
"""
from __future__ import annotations


def _minutos(horario: str) -> int:
    horas, minutos = horario.split(":")
    return int(horas) * 60 + int(minutos)


def conflitos_no_patio(agendamentos: list[dict], margem: int) -> list[str]:
    """Retorna os ids dos agendamentos que conflitam com pelo menos outro
    agendamento da mesma doca, na ordem em que aparecem em `agendamentos`.
    """
    intervalos = [
        (
            agendamento["id"],
            agendamento["doca"],
            _minutos(agendamento["inicio"]),
            _minutos(agendamento["fim"]) + margem,
        )
        for agendamento in agendamentos
    ]

    conflitantes: set[str] = set()
    for i, (id_a, doca_a, inicio_a, fim_a) in enumerate(intervalos):
        for id_b, doca_b, inicio_b, fim_b in intervalos[i + 1 :]:
            if doca_a != doca_b:
                continue
            if max(inicio_a, inicio_b) < min(fim_a, fim_b):
                conflitantes.add(id_a)
                conflitantes.add(id_b)

    return [agendamento["id"] for agendamento in agendamentos if agendamento["id"] in conflitantes]
