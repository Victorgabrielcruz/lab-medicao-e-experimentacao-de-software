"""Calibração do cenário P4 e amostras do G1 a partir da coleta (#264, #267)."""

import csv
import json
from pathlib import Path

import numpy as np

from hipotese.config import META_TAXA_FALHA, N_AMOSTRA_PEQUENA, gerador
from hipotese.gerador import INDEPENDENTE, RAJADAS, gerar_builds

RESUMO = Path(__file__).resolve().parents[1] / "data" / "ci_pytest_resumo.json"


def carregar_resumo() -> dict:
    """Lê a origem e as estatísticas versionadas, sem rede ou simulação."""
    return json.loads(RESUMO.read_text(encoding="utf-8"))


def carregar_builds_reais() -> np.ndarray:
    """Lê as observações binárias do CSV da coleta, em ordem cronológica."""
    with RESUMO.with_name("ci_pytest.csv").open(encoding="utf-8", newline="") as arquivo:
        return np.array([int(linha["falhou"]) for linha in csv.DictReader(arquivo)], dtype=int)


def carregar_amostras_g1() -> tuple[np.ndarray, np.ndarray]:
    """Lê as builds reais e gera uma amostra independente sob H₀ (#267).

    Usa o tamanho efetivo do CSV e um gerador próprio com a semente fixa.
    A taxa permanece a meta do protocolo, sem ajustar o sorteio ao resultado.
    """
    reais = carregar_builds_reais()
    simulados = gerar_builds(
        gerador(), n=reais.size, taxa_falha=META_TAXA_FALHA,
        situacao=INDEPENDENTE, correlacao=0.0,
    )
    return reais, simulados


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
