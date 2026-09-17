"""Esqueleto de K05 — Alertas de leitura persistente.

Implemente a função abaixo seguindo o contrato descrito em ../README.md.
Não altere a assinatura nem o nome da função — a suíte de testes depende
dela.
"""
from __future__ import annotations

def gerar_alertas(
    sensores: list[dict], consecutivas: int, leituras: list[dict]
) -> list[dict]:
    limites = {s["sensor"]: (s["minimo"], s["maximo"]) for s in sensores}
    contagem = {s["sensor"]: 0 for s in sensores}
    alerta_emitido = {s["sensor"]: False for s in sensores}
    
    alertas = []
    
    for leitura in leituras:
        id_leitura = leitura["id"]
        sensor = leitura["sensor"]
        valor = leitura["valor"]
        
        minimo, maximo = limites[sensor]
        
        if valor < minimo or valor > maximo:
            contagem[sensor] += 1
            if contagem[sensor] == consecutivas and not alerta_emitido[sensor]:
                alertas.append({"sensor": sensor, "leitura": id_leitura})
                alerta_emitido[sensor] = True
        else:
            contagem[sensor] = 0
            alerta_emitido[sensor] = False
            
    return alertas
