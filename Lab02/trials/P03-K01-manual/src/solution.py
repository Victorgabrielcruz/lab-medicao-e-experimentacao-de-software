
from __future__ import annotations


def conflitos_no_patio(agendamentos: list[dict], margem: int) -> list[str]:
    """Retorna os ids dos agendamentos conflitantes, preservando a ordem."""
    def minutos(horario: str) -> int:
        horas, minutos_do_horario = horario.split(":")
        return int(horas) * 60 + int(minutos_do_horario)

    intervalos = [
        (
            agendamento["doca"],
            minutos(agendamento["inicio"]),
            minutos(agendamento["fim"]) + margem,
        )
        for agendamento in agendamentos
    ]

    conflitantes = [False] * len(agendamentos)

    for indice, (doca, inicio, fim_com_margem) in enumerate(intervalos):
        for outro_indice in range(indice + 1, len(intervalos)):
            outra_doca, outro_inicio, outro_fim_com_margem = intervalos[outro_indice]

            if doca != outra_doca:
                continue

            if inicio < outro_fim_com_margem and outro_inicio < fim_com_margem:
                conflitantes[indice] = True
                conflitantes[outro_indice] = True

    return [
        agendamento["id"]
        for indice, agendamento in enumerate(agendamentos)
        if conflitantes[indice]
    ]