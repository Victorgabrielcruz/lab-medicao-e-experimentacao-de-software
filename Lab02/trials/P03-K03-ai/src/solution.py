"""Esqueleto de K03 — Cadeia de custódia de remessas.

Implemente a função abaixo seguindo o contrato descrito em ../README.md.
Não altere a assinatura nem o nome da função — a suíte de testes depende
dela.
"""
from __future__ import annotations


def avaliar_cadeia_de_custodia(eventos: list[dict]) -> dict:
    """Retorna os eventos aceitos, os recusados e as remessas pendentes,
    conforme as regras descritas em ../README.md.
    """
    etapas = ("COLETA", "LACRE", "DESPACHO", "RECEBIMENTO")
    progresso: dict[str, int] = {}
    ordem_remessas: list[str] = []
    aceitos: list[str] = []
    recusados: list[str] = []

    for evento in eventos:
        remessa = evento["remessa"]
        indice_esperado = progresso.get(remessa, -1) + 1

        if (
            indice_esperado < len(etapas)
            and evento["etapa"] == etapas[indice_esperado]
        ):
            if remessa not in progresso:
                ordem_remessas.append(remessa)
            progresso[remessa] = indice_esperado
            aceitos.append(evento["id"])
        else:
            recusados.append(evento["id"])

    return {
        "aceitos": aceitos,
        "recusados": recusados,
        "pendentes": [
            remessa
            for remessa in ordem_remessas
            if progresso[remessa] < len(etapas) - 1
        ],
    }
