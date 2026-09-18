from __future__ import annotations


def avaliar_credenciais(credenciais: list[dict], eventos: list[dict]) -> dict:
    """Retorna os eventos aceitos, os recusados e o estado final de cada
    credencial, conforme as regras descritas em ../README.md.
    """
    estados = {credencial["credencial"]: "NOVA" for credencial in credenciais}
    expiracoes = {credencial["credencial"]: credencial["expiraEm"] for credencial in credenciais}
    aceitos = []
    recusados = []

    for evento in eventos:
        identificador = evento["credencial"]
        estado = estados[identificador]
        dentro_do_prazo = evento["momento"] <= expiracoes[identificador]
        acao = evento["acao"]

        pode_aceitar = dentro_do_prazo and (
            (acao == "LIBERAR" and estado == "NOVA")
            or (acao == "USAR" and estado == "LIBERADA")
            or (acao == "REVOGAR" and estado in {"NOVA", "LIBERADA"})
        )

        if not pode_aceitar:
            recusados.append(evento["id"])
            continue

        aceitos.append(evento["id"])
        estados[identificador] = {
            "LIBERAR": "LIBERADA",
            "USAR": "UTILIZADA",
            "REVOGAR": "REVOGADA",
        }[acao]

    return {
        "aceitos": aceitos,
        "recusados": recusados,
        "statusFinal": [
            {"credencial": credencial["credencial"], "status": estados[credencial["credencial"]]}
            for credencial in credenciais
        ],
    }
