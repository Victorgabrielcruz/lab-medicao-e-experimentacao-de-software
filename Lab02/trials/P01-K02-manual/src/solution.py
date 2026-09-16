"""Esqueleto de K02 — Compartimentos de coleta.

Implemente a função abaixo seguindo o contrato descrito em ../README.md.
Não altere a assinatura nem o nome da função — a suíte de testes depende
dela.
"""
from __future__ import annotations


def processar_movimentos(capacidades: list[dict], movimentos: list[dict]) -> dict:
    """Retorna os movimentos aceitos, os recusados e o saldo final de cada
    compartimento, conforme as regras descritas em ../README.md.
    """
    saldos = {c["compartimento"]: 0 for c in capacidades}
    caps = {c["compartimento"]: c["capacidade"] for c in capacidades}
    
    aceitos = []
    recusados = []
    
    for mov in movimentos:
        comp = mov["compartimento"]
        qtd = mov["quantidade"]
        
        if mov["tipo"] == "ENTRADA":
            if saldos[comp] + qtd <= caps[comp]:
                saldos[comp] += qtd
                aceitos.append(mov["id"])
            else:
                recusados.append(mov["id"])
        elif mov["tipo"] == "SAIDA":
            if saldos[comp] - qtd >= 0:
                saldos[comp] -= qtd
                aceitos.append(mov["id"])
            else:
                recusados.append(mov["id"])
                
    saldo_final = [
        {"compartimento": c["compartimento"], "saldo": saldos[c["compartimento"]]}
        for c in capacidades
    ]
    
    return {
        "aceitos": aceitos,
        "recusados": recusados,
        "saldoFinal": saldo_final
    }