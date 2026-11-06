"""Calibração do cenário P4 a partir da coleta congelada (#264)."""

import json
from pathlib import Path

from hipotese.config import N_AMOSTRA_PEQUENA
from hipotese.gerador import INDEPENDENTE, RAJADAS

RESUMO = Path(__file__).resolve().parents[1] / "data" / "ci_pytest_resumo.json"


def carregar_resumo() -> dict:
    """Lê a origem e as estatísticas versionadas, sem rede ou simulação."""
    return json.loads(RESUMO.read_text(encoding="utf-8"))


def configuracoes_simulacao(resumo: dict) -> dict[str, dict]:
    """Argumentos do gerador para cada situação do protocolo.

    A situação de rajadas recebe explicitamente a ACF da amostra válida,
    sem depender da correlação padrão do gerador. A taxa sob H0 continua
    sendo a meta de 5%, e não a taxa observada na coleta.
    """
    estatisticas = resumo["estatisticas"]
    n = estatisticas["n_execucoes"]
    return {
        "Independente": {"n": n, "situacao": INDEPENDENTE, "correlacao": 0.0},
        "Rajadas": {
            "n": n,
            "situacao": RAJADAS,
            "correlacao": estatisticas["autocorrelacao_lag1"],
        },
        "Amostra pequena": {
            "n": N_AMOSTRA_PEQUENA, "situacao": INDEPENDENTE, "correlacao": 0.0,
        },
    }
