import pytest

from pipeline.classificacao import (CLASSES, DIA, ELITE, HIGH, HORA, LOW, MEDIUM, METRICAS, SEIS_MESES, SEMANA,
                                    Faixas, classificar, classificar_metrica, nota_geral)


@pytest.mark.parametrize("valor, esperado", [
    (1000, ELITE), (365, ELITE),
    (364.9, HIGH), (12, HIGH),
    (11.9, MEDIUM), (2, MEDIUM),
    (1.9, LOW), (0, LOW),
])
def test_limites_deployment_frequency(valor, esperado):
    assert classificar_metrica("deployment_frequency", valor) == esperado


@pytest.mark.parametrize("valor, esperado", [
    (0, ELITE), (0.99 * HORA, ELITE),
    (1 * HORA, HIGH), (12 * HORA, HIGH), (SEMANA - 0.01, HIGH),
    (SEMANA, MEDIUM), (30 * DIA, MEDIUM), (SEIS_MESES - 0.01, MEDIUM),
    (SEIS_MESES, LOW), (400 * DIA, LOW),
])
def test_limites_lead_time(valor, esperado):
    assert classificar_metrica("lead_time", valor) == esperado


@pytest.mark.parametrize("valor, esperado", [
    (0, ELITE), (0.15, ELITE),
    (0.1501, HIGH), (0.30, HIGH),
    (0.3001, MEDIUM), (0.45, MEDIUM),
    (0.4501, LOW), (1, LOW),
])
def test_limites_change_failure_rate(valor, esperado):
    assert classificar_metrica("change_failure_rate", valor) == esperado


@pytest.mark.parametrize("valor, esperado", [
    (0, ELITE), (0.5 * HORA, ELITE),
    (1 * HORA, HIGH), (DIA - 0.01, HIGH),
    (DIA, MEDIUM), (SEMANA - 0.01, MEDIUM),
    (SEMANA, LOW), (60 * DIA, LOW),
])
def test_limites_tempo_recuperacao(valor, esperado):
    assert classificar_metrica("tempo_recuperacao", valor) == esperado


def test_tabela_cobre_as_quatro_metricas():
    assert set(METRICAS) == {"deployment_frequency", "lead_time", "change_failure_rate", "tempo_recuperacao"}


@pytest.mark.parametrize("valor", [None, float("nan")])
def test_valor_ausente_nao_e_classificado(valor):
    assert classificar_metrica("lead_time", valor) is None


@pytest.mark.parametrize("metrica, valor", [
    ("lead_time", -1),
    ("change_failure_rate", 1.2),
    ("metrica_inexistente", 1),
])
def test_valores_invalidos(metrica, valor):
    with pytest.raises(ValueError):
        classificar_metrica(metrica, valor)


@pytest.mark.parametrize("classes, esperado", [
    ([ELITE, ELITE, ELITE, ELITE], ELITE),
    ([ELITE, HIGH, MEDIUM, LOW], MEDIUM),  # mediana 2,5 -> 2
    ([ELITE, ELITE, HIGH, HIGH], HIGH),    # mediana 3,5 -> 3
    ([ELITE, HIGH, HIGH, LOW], HIGH),      # mediana 3
    ([LOW, LOW, MEDIUM, ELITE], LOW),      # mediana 1,5 -> 1
    ([ELITE, None, LOW, None], MEDIUM),    # só as presentes: mediana 2,5 -> 2
    ([HIGH, None, None, None], HIGH),
    ([None, None, None, None], None),
    ([], None),
])
def test_nota_geral_mediana_arredondada_para_baixo(classes, esperado):
    assert nota_geral(classes) == esperado


def test_classificar_repositorio():
    resultado = classificar({
        "deployment_frequency": 52,     # High
        "lead_time": 3 * DIA,           # High
        "change_failure_rate": 0.10,    # Elite
        "tempo_recuperacao": 2 * DIA,   # Medium
    })
    assert resultado == {
        "deployment_frequency": HIGH, "lead_time": HIGH, "change_failure_rate": ELITE,
        "tempo_recuperacao": MEDIUM, "geral": HIGH,
    }


def test_classificar_com_metrica_ausente():
    resultado = classificar({"deployment_frequency": 400, "lead_time": 0.5, "change_failure_rate": 0.5})
    assert resultado["tempo_recuperacao"] is None
    assert resultado["geral"] == ELITE  # Elite, Elite, Low -> mediana 4


def test_classificar_rejeita_metrica_desconhecida():
    with pytest.raises(ValueError, match="mttr"):
        classificar({"mttr": 1})


def test_faixas_personalizadas():
    referencia = {"x": Faixas(elite=10, high=20, medium=30, inclusivo=True)}
    assert [classificar_metrica("x", v, referencia) for v in (10, 20, 30, 31)] == [ELITE, HIGH, MEDIUM, LOW]
    assert classificar({"x": 25}, referencia) == {"x": MEDIUM, "geral": MEDIUM}


def test_ordem_das_classes():
    assert CLASSES == (ELITE, HIGH, MEDIUM, LOW)
