"""Classificação DORA de referência (C1).

Cada métrica é classificada em Elite, High, Medium ou Low pela tabela de
referência abaixo, e a nota geral do repositório é a mediana das classificações,
arredondada para baixo (para a classe pior).

A tabela segue o Accelerate State of DevOps 2021, o último relatório com as
quatro classes. Os intervalos do relatório deixam lacunas (por exemplo, lead
time entre 1 hora e 1 dia não cai em nenhuma classe) e não diferenciam High,
Medium e Low no change failure rate (todos "16-30%"). Aqui as lacunas são
fechadas: cada valor cai na melhor classe cujo limite ele atende. As decisões
estão em docs/definicoes-operacionais.md, seção 7.

Unidades de entrada:
- deployment_frequency: deploys por ano (= releases na janela de 12 meses)
- lead_time e tempo_recuperacao: horas
- change_failure_rate: fração entre 0 e 1
"""

import math
import statistics
from dataclasses import dataclass

ELITE, HIGH, MEDIUM, LOW = "Elite", "High", "Medium", "Low"
CLASSES = (ELITE, HIGH, MEDIUM, LOW)
NOTA = {LOW: 1, MEDIUM: 2, HIGH: 3, ELITE: 4}
CLASSE_DA_NOTA = {nota: classe for classe, nota in NOTA.items()}

HORA = 1
DIA = 24 * HORA
SEMANA = 7 * DIA
SEIS_MESES = 182.5 * DIA


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
    # Elite: sob demanda (pelo menos 1 por dia); High: pelo menos 1 por mês;
    # Medium: pelo menos 1 a cada 6 meses; Low: menos que isso.
    "deployment_frequency": Faixas(elite=365, high=12, medium=2, maior_melhor=True),
    # Elite: < 1 hora; High: < 1 semana; Medium: < 6 meses; Low: 6 meses ou mais.
    "lead_time": Faixas(elite=1 * HORA, high=SEMANA, medium=SEIS_MESES),
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
