from __future__ import annotations


def gerar_alertas(
    sensores: list[dict], consecutivas: int, leituras: list[dict]
) -> list[dict]:
    faixas = {
        sensor["sensor"]: (sensor["minimo"], sensor["maximo"])
        for sensor in sensores
    }
    contagens = {sensor["sensor"]: 0 for sensor in sensores}
    alertados = {sensor["sensor"]: False for sensor in sensores}
    alertas = []

    for leitura in leituras:
        sensor = leitura["sensor"]
        minimo, maximo = faixas[sensor]
        valor = leitura["valor"]
        dentro_da_faixa = minimo <= valor <= maximo

        if dentro_da_faixa:
            contagens[sensor] = 0
            alertados[sensor] = False
            continue

        contagens[sensor] += 1

        if contagens[sensor] >= consecutivas and not alertados[sensor]:
            alertas.append(
                {
                    "sensor": sensor,
                    "leitura": leitura["id"],
                }
            )
            alertados[sensor] = True

    return alertas