"""Parâmetros do experimento com o SQLite, compartilhados por coleta, análise e dashboard.

Fatores: ``journal_mode`` × ``synchronous`` (desenho fatorial 2 × 2).
Cargas: escrita, leitura e mista, cada uma executada em todas as configurações.
"""

from dataclasses import dataclass
from itertools import product
from pathlib import Path

SEMENTE = 42
ALFA = 0.05

# Fatores e níveis (valores aceitos pelos PRAGMAs do SQLite).
JOURNAL_MODES = ("DELETE", "WAL")
SYNCHRONOUS = ("FULL", "NORMAL")

# Repetições medidas por configuração e carga; as de aquecimento são descartadas.
N_REPETICOES = 30
N_AQUECIMENTO = 3

# Banco inicial de cada execução: linhas pré-carregadas e tamanho do campo de texto.
LINHAS_INICIAIS = 10_000
TAMANHO_PAYLOAD = 256


@dataclass(frozen=True)
class Carga:
    """Carga de trabalho executada sobre o banco.

    ``fracao_leitura`` é a proporção de operações de leitura (0 a 1);
    as demais são escritas, cada uma em sua própria transação.
    """

    nome: str
    n_operacoes: int
    fracao_leitura: float


CARGAS = (
    Carga("escrita", n_operacoes=1_000, fracao_leitura=0.0),
    Carga("leitura", n_operacoes=10_000, fracao_leitura=1.0),
    Carga("mista", n_operacoes=2_000, fracao_leitura=0.7),
)


@dataclass(frozen=True)
class Configuracao:
    """Combinação de níveis dos fatores aplicada ao banco antes da carga."""

    journal_mode: str
    synchronous: str

    @property
    def nome(self) -> str:
        return f"{self.journal_mode}-{self.synchronous}"

    @property
    def pragmas(self) -> tuple[str, ...]:
        return (
            f"PRAGMA journal_mode={self.journal_mode}",
            f"PRAGMA synchronous={self.synchronous}",
        )


CONFIGURACOES = tuple(Configuracao(j, s) for j, s in product(JOURNAL_MODES, SYNCHRONOUS))

# Configuração padrão do SQLite, usada como referência nas comparações.
CONFIGURACAO_PADRAO = Configuracao("DELETE", "FULL")

RAIZ = Path(__file__).resolve().parent.parent
DIR_DADOS = RAIZ / "data"
DIR_BANCOS = DIR_DADOS / "bancos"

URL_REPOSITORIO = "https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/tree/main/lab05"
URL_PROJECT = "https://github.com/users/Victorgabrielcruz/projects/7"


def combinacoes() -> list[tuple[Configuracao, Carga]]:
    """Todas as combinações de configuração e carga do experimento."""
    return list(product(CONFIGURACOES, CARGAS))


def total_execucoes() -> int:
    """Execuções medidas e de aquecimento na coleta completa."""
    return len(combinacoes()) * (N_REPETICOES + N_AQUECIMENTO)
