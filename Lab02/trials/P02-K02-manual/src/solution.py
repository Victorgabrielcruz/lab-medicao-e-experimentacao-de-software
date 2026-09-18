from __future__ import annotations


def processar_movimentos(capacidades: list[dict], movimentos: list[dict]) -> dict:
    """Processa os movimentos e retorna aceitos, recusados e saldos finais."""

    saldos = {item["compartimento"]: 0 for item in capacidades}
    limites = {
        item["compartimento"]: item["capacidade"]
        for item in capacidades
    }

    aceitos = []
    recusados = []

    for movimento in movimentos:
        id_movimento = movimento["id"]
        compartimento = movimento["compartimento"]
        quantidade = movimento["quantidade"]
        tipo = movimento["tipo"]

        saldo_atual = saldos[compartimento]

        if tipo == "ENTRADA":
            novo_saldo = saldo_atual + quantidade
            valido = novo_saldo <= limites[compartimento]
        else:
            novo_saldo = saldo_atual - quantidade
            valido = novo_saldo >= 0

        if valido:
            saldos[compartimento] = novo_saldo
            aceitos.append(id_movimento)
        else:
            recusados.append(id_movimento)

    saldo_final = []

    for item in capacidades:
        compartimento = item["compartimento"]

        saldo_final.append({
            "compartimento": compartimento,
            "saldo": saldos[compartimento]
        })

    return {
        "aceitos": aceitos,
        "recusados": recusados,
        "saldoFinal": saldo_final
    }