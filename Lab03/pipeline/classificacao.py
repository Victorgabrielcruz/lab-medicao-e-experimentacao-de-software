"""Classificação C1 pelos cortes fixos do enunciado oficial do Lab03.

Entradas: DF em releases/semana; lead time e recuperação em horas; CFR em
fração. A classificação geral é a mediana das notas, arredondada para baixo.
Para DF na janela real, classificar_frequencia mantém o corte mensal civil:
12 releases em 12 meses, independentemente da duração em dias da janela.
"""

import math
import statistics
from dataclasses import dataclass, replace

VERSAO_REFERENCIA = "lab03-enunciado-cortes-v2"

ELITE, HIGH, MEDIUM, LOW = "Elite", "High", "Medium", "Low"
CLASSES = (ELITE, HIGH, MEDIUM, LOW)
NOTA = {LOW: 1, MEDIUM: 2, HIGH: 3, ELITE: 4}
CLASSE_DA_NOTA = {nota: classe for classe, nota in NOTA.items()}

HORA = 1
DIA = 24 * HORA
SEMANA = 7 * DIA
MES = 30 * DIA


@dataclass(frozen=True)
class Faixas:
    """Limites de Elite, High e Medium; o que não atende nenhum é Low.

    maior_melhor=True: a classe é atingida com valor >= limite.
    maior_melhor=False: com valor < limite (ou <= limite, se inclusivo=True).
    """

    elite: float
    high: float
    medium: float
    maior_melhor: bool = False
    inclusivo: bool = False

    def classificar(self, valor):
        for classe, limite in ((ELITE, self.elite), (HIGH, self.high), (MEDIUM, self.medium)):
            if self.maior_melhor:
                atende = valor >= limite
            else:
                atende = valor <= limite if self.inclusivo else valor < limite
            if atende:
                return classe
        return LOW


REFERENCIA = {
    # Conversão de 1/mês em uma referência de 12 meses / 365 dias.
    # O integrado ajusta esse limite à duração real da janela com a função abaixo.
    "deployment_frequency": Faixas(elite=7, high=1, medium=12*7/365, maior_melhor=True),
    "lead_time": Faixas(elite=DIA, high=SEMANA, medium=MES),
    # Elite: até 15%; High: até 30%; Medium: até 45%; Low: acima de 45%.
    "change_failure_rate": Faixas(elite=0.15, high=0.30, medium=0.45, inclusivo=True),
    # Elite: < 1 hora; High: < 1 dia; Medium: < 1 semana; Low: 1 semana ou mais.
    "tempo_recuperacao": Faixas(elite=1 * HORA, high=DIA, medium=SEMANA),
}
METRICAS = tuple(REFERENCIA)


def classificar_metrica(metrica, valor, referencia=REFERENCIA):
    """Devolve a classe da métrica, ou None quando o valor não existe."""
    if metrica not in referencia:
        raise ValueError(f"Métrica desconhecida: {metrica}")
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return None
    if valor < 0:
        raise ValueError(f"{metrica} não pode ser negativa: {valor}")
    if metrica == "change_failure_rate" and valor > 1:
        raise ValueError(f"change_failure_rate deve ser uma fração entre 0 e 1: {valor}")
    return referencia[metrica].classificar(valor)


def nota_geral(classes):
    """Mediana das classificações, arredondada para baixo. Ignora as ausentes."""
    notas = [NOTA[c] for c in classes if c is not None]
    if not notas:
        return None
    return CLASSE_DA_NOTA[math.floor(statistics.median(notas))]


def classificar(valores, referencia=REFERENCIA):
    """Classifica um repositório.

    `valores` mapeia cada métrica ao seu valor (None quando não pôde ser
    calculada; a métrica então não entra na nota geral). Devolve um dicionário
    com a classe de cada métrica e a chave "geral".
    """
    desconhecidas = set(valores) - set(referencia)
    if desconhecidas:
        raise ValueError(f"Métricas desconhecidas: {', '.join(sorted(desconhecidas))}")
    resultado = {m: classificar_metrica(m, valores.get(m), referencia) for m in referencia}
    resultado["geral"] = nota_geral(resultado.values())
    return resultado


def classificar_frequencia(quantidade, inicio, fim):
    """Releases/semana real; Medium exige >=1 por mês na janela de 12 meses."""
    semanas = (fim-inicio).total_seconds() / (7*24*3600)
    if semanas <= 0:
        raise ValueError("Janela de frequência deve ter duração positiva.")
    frequencia = quantidade/semanas
    referencia = {"deployment_frequency": replace(REFERENCIA["deployment_frequency"], medium=12/semanas)}
    return frequencia, classificar_metrica("deployment_frequency", frequencia, referencia)
