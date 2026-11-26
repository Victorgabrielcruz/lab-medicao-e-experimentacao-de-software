"""Unidades, sinais e premissas dos cenários de impacto (#311)."""

import math

import pandas as pd
import pytest

from experimento import impacto


def efeitos(delta=-2, inferior=-3, superior=-1):
    return pd.DataFrame([{"carga": "escrita", "hipotese": "H1", "efeito": "Diferença M1",
                          "estimativa": delta, "ic_inf": inferior, "ic_sup": superior}])


def test_conversao_segundos_horas_e_ic_com_sinal_invertido():
    resultado = impacto.estimar(efeitos(), dispositivos=10_000, lotes_por_dia=1)
    assert resultado.reducao_por_lote_s == 2
    assert resultado.reducao_dispositivo_dia_s == 2
    assert resultado.horas_equivalentes_dia == pytest.approx(20_000 / 3600)
    assert resultado.horas_ic_inf == pytest.approx(10_000 / 3600)
    assert resultado.horas_ic_sup == pytest.approx(30_000 / 3600)
    assert resultado.operacoes_por_lote == 1000
    assert resultado.operacoes_total_dia == 10_000_000
    assert resultado.razao_referencia_publica_pct == pytest.approx(100 * 10_000 / 3_000_000_000)
    assert resultado.tratamento == "WAL-FULL"
    assert resultado.referencia == "DELETE-FULL"


def test_cenario_escala_so_premissas_e_preserva_valor_local():
    pequeno = impacto.estimar(efeitos(), dispositivos=1000, lotes_por_dia=1)
    grande = impacto.estimar(efeitos(), dispositivos=2000, lotes_por_dia=3)
    assert grande.reducao_por_lote_s == pequeno.reducao_por_lote_s
    assert grande.reducao_dispositivo_dia_s == 3 * pequeno.reducao_dispositivo_dia_s
    assert grande.horas_equivalentes_dia == 6 * pequeno.horas_equivalentes_dia
    assert grande.horas_ic_inf == 6 * pequeno.horas_ic_inf


def test_piora_e_faixa_que_cruza_zero_nao_sao_transformadas_em_economia():
    piora = impacto.estimar(efeitos(2, 1, 3))
    assert piora.horas_equivalentes_dia < 0
    assert piora.horas_ic_inf < piora.horas_ic_sup < 0
    incerto = impacto.estimar(efeitos(0.1, -1, 2))
    assert incerto.horas_ic_inf < 0 < incerto.horas_ic_sup


@pytest.mark.parametrize("premissa", [{"dispositivos": 0}, {"lotes_por_dia": 0}])
def test_cenario_zero_nao_divide_por_zero(premissa):
    resultado = impacto.estimar(efeitos(), **premissa)
    assert resultado.horas_equivalentes_dia == resultado.horas_ic_inf == resultado.horas_ic_sup == 0
    assert resultado.operacoes_total_dia == 0


@pytest.mark.parametrize("premissa", [
    {"dispositivos": -1}, {"dispositivos": 2.5}, {"dispositivos": True},
    {"lotes_por_dia": -1}, {"lotes_por_dia": math.inf}, {"lotes_por_dia": False},
    {"carga": "outra"}, {"hipotese": "H4"},
])
def test_recusa_premissas_invalidas(premissa):
    with pytest.raises(ValueError):
        impacto.estimar(efeitos(), **premissa)


@pytest.mark.parametrize("entrada", [
    efeitos(math.nan), efeitos(inferior=math.inf), efeitos(inferior=2, superior=-1),
    efeitos().iloc[:0], pd.concat([efeitos(), efeitos()]), pd.DataFrame(),
])
def test_recusa_efeito_ausente_duplicado_ou_intervalo_invalido(entrada):
    with pytest.raises(ValueError):
        impacto.estimar(entrada)
