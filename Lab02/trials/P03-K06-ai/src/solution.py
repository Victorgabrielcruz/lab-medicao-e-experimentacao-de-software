from __future__ import annotations


def avaliar_visitas(roteiros: list[dict], visitas: list[dict]) -> dict:
    pontos_por_rota = {
        roteiro["rota"]: roteiro["pontos"]
        for roteiro in roteiros
    }
    proximo_indice = {
        roteiro["rota"]: 0
        for roteiro in roteiros
    }

    aceitos = []
    recusados = []

    for visita in visitas:
        rota = visita["rota"]
        pontos = pontos_por_rota[rota]
        indice = proximo_indice[rota]

        if indice < len(pontos) and visita["ponto"] == pontos[indice]:
            aceitos.append(visita["id"])
            proximo_indice[rota] += 1
        else:
            recusados.append(visita["id"])

    concluidas = [
        roteiro["rota"]
        for roteiro in roteiros
        if proximo_indice[roteiro["rota"]] == len(roteiro["pontos"])
    ]

    pendentes = [
        roteiro["rota"]
        for roteiro in roteiros
        if proximo_indice[roteiro["rota"]] != len(roteiro["pontos"])
    ]

    return {
        "aceitos": aceitos,
        "recusados": recusados,
        "concluidas": concluidas,
        "pendentes": pendentes,
    }