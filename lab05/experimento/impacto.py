"""Cenários de impacto com premissas explícitas e fontes públicas (#311)."""

from dataclasses import asdict, dataclass
import math
from numbers import Integral

import pandas as pd

from experimento import config
from experimento.validacao import COMPARACOES

DATA_ACESSO = "2026-11-25"
FONTES = (
    {
        "id": "android", "publicador": "Google", "titulo": "The Android Show: I/O Edition",
        "url": "https://blog.google/products-and-platforms/platforms/android/the-android-show-io-2025/",
        "publicado_em": "2025-05-13", "acessado_em": DATA_ACESSO,
        "numero": 3_000_000_000, "unidade": "dispositivos Android ativos",
        "qualificador": "mais de", "natureza": "número histórico publicado pelo fornecedor",
    },
    {
        "id": "sqlite", "publicador": "SQLite", "titulo": "Most Widely Deployed and Used Database Engine",
        "url": "https://www.sqlite.org/mostdeployed.html",
        "atualizado_em": "2026-04-21", "acessado_em": DATA_ACESSO,
        "numero": 1_000_000_000_000, "unidade": "bancos SQLite em uso ativo",
        "qualificador": "mais de", "natureza": "estimativa dos autores, não contagem de pessoas",
    },
    {
        "id": "durabilidade", "publicador": "SQLite", "titulo": "PRAGMA synchronous",
        "url": "https://www.sqlite.org/pragma.html#pragma_synchronous", "acessado_em": DATA_ACESSO,
        "natureza": "documentação de garantias; não mede probabilidade de perda",
    },
)
REFERENCIA_DISPOSITIVOS = FONTES[0]["numero"]

LIMITES = (
    "Uma máquina Windows/NTFS e uma sessão; resultados e IC condicionais à independência entre rodadas.",
    "Dados sintéticos, banco inicial de 10.000 linhas e um commit por escrita; outras transações, lotes e volumes exigem nova medição.",
    "Leitura representa SELECTs em autocommit; não estima leitura em transação única ou concorrência.",
    "A janela medida exclui preparação e fechamento; não representa latência percebida, tempo total da aplicação ou SLA.",
    "O modelo proporcional replica um parâmetro local; não prevê desempenho em Android, iOS, outros discos ou versões.",
    "Horas equivalentes somam tempo de execução entre dispositivos; não são horas de trabalho humano, economia financeira, energia ou bateria.",
    "O IC local escalado não é intervalo de predição: não inclui incerteza de adesão, frequência de uso ou heterogeneidade da frota.",
    "Dispositivos, bancos e pessoas são unidades distintas; os números públicos não revelam quantos usuários usam cada PRAGMA ou carga.",
    "Durabilidade não foi medida; desempenho não quantifica frequência de perda, transações perdidas ou custo de incidentes.",
)


@dataclass(frozen=True)
class Cenario:
    carga: str
    hipotese: str
    tratamento: str
    referencia: str
    dispositivos: int
    lotes_por_dispositivo_dia: int
    operacoes_por_lote: int
    lotes_total_dia: int
    operacoes_total_dia: int
    razao_referencia_publica_pct: float
    reducao_por_lote_s: float
    reducao_dispositivo_dia_s: float
    horas_equivalentes_dia: float
    horas_ic_inf: float
    horas_ic_sup: float

    def como_dict(self):
        return asdict(self)


def estimar(efeitos, *, carga="escrita", hipotese="H1", dispositivos=10_000, lotes_por_dia=1):
    """Escala a mediana da diferença pareada de M1, invertendo corretamente o IC.

    É um cenário proporcional, não uma previsão da frota ou a mediana de uma soma.
    Valores negativos de redução representam acréscimo de tempo e são preservados.
    """
    for nome, valor in (("dispositivos", dispositivos), ("lotes_por_dia", lotes_por_dia)):
        if not isinstance(valor, Integral) or isinstance(valor, bool) or valor < 0:
            raise ValueError(f"{nome} deve ser inteiro não negativo.")
    cargas = {c.nome: c for c in config.CARGAS}
    comparacoes = {h: (t, r) for h, t, r in COMPARACOES}
    if carga not in cargas or hipotese not in comparacoes:
        raise ValueError("Carga ou comparação fora do protocolo.")
    campos = {"carga", "hipotese", "efeito", "estimativa", "ic_inf", "ic_sup"}
    if not campos <= set(efeitos.columns):
        raise ValueError("Efeitos e IC da análise #309 estão ausentes.")
    linhas = efeitos[(efeitos.carga == carga) & (efeitos.hipotese == hipotese)
                     & (efeitos.efeito == "Diferença M1")]
    if len(linhas) != 1:
        raise ValueError("Esperado um único efeito pareado de M1 para o cenário.")
    linha = linhas.iloc[0]
    delta, inferior, superior = (float(linha[c]) for c in ("estimativa", "ic_inf", "ic_sup"))
    if not all(math.isfinite(v) for v in (delta, inferior, superior)) or inferior > superior:
        raise ValueError("Efeito ou intervalo inválido.")
    quantidade = int(dispositivos) * int(lotes_por_dia)
    tratamento, referencia = comparacoes[hipotese]
    return Cenario(
        carga, hipotese, tratamento, referencia, int(dispositivos), int(lotes_por_dia),
        cargas[carga].n_operacoes, quantidade, quantidade * cargas[carga].n_operacoes,
        100 * dispositivos / REFERENCIA_DISPOSITIVOS, -delta, -delta * lotes_por_dia,
        -delta * quantidade / 3600, -superior * quantidade / 3600, -inferior * quantidade / 3600,
    )


def cenarios_alternativos(efeitos, dispositivos, lotes_por_dia):
    return pd.DataFrame([
        estimar(efeitos, carga=c.nome, hipotese=h, dispositivos=dispositivos,
                lotes_por_dia=lotes_por_dia).como_dict()
        for c in config.CARGAS for h, _, _ in COMPARACOES
    ])
