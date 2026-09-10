"""Suíte de aceitação de K05 — Alertas de leitura persistente."""
from solution import gerar_alertas


def test_exemplo_do_enunciado():
    sensores = [
        {"sensor": "S1", "minimo": 0, "maximo": 10},
        {"sensor": "S2", "minimo": 5, "maximo": 8},
    ]
    leituras = [
        {"id": "L1", "sensor": "S1", "valor": 12},
        {"id": "L2", "sensor": "S2", "valor": 4},
        {"id": "L3", "sensor": "S1", "valor": 11},
        {"id": "L4", "sensor": "S1", "valor": 7},
        {"id": "L5", "sensor": "S2", "valor": 9},
        {"id": "L6", "sensor": "S2", "valor": 10},
    ]

    resultado = gerar_alertas(sensores, consecutivas=2, leituras=leituras)

    assert resultado == [
        {"sensor": "S1", "leitura": "L3"},
        {"sensor": "S2", "leitura": "L5"},
    ]


def test_valores_no_limite_da_faixa_estao_dentro_e_reiniciam_a_sequencia():
    sensores = [{"sensor": "S1", "minimo": 0, "maximo": 10}]
    leituras = [
        {"id": "L1", "sensor": "S1", "valor": 12},
        {"id": "L2", "sensor": "S1", "valor": 10},  # no limite: dentro da faixa
        {"id": "L3", "sensor": "S1", "valor": 11},
    ]

    resultado = gerar_alertas(sensores, consecutivas=2, leituras=leituras)

    assert resultado == []


def test_no_maximo_um_alerta_por_sequencia_ininterrupta():
    sensores = [{"sensor": "S1", "minimo": 0, "maximo": 10}]
    leituras = [
        {"id": "L1", "sensor": "S1", "valor": 11},
        {"id": "L2", "sensor": "S1", "valor": 12},  # completa a sequência de 2
        {"id": "L3", "sensor": "S1", "valor": 13},  # continua fora, sem novo alerta
        {"id": "L4", "sensor": "S1", "valor": 14},
    ]

    resultado = gerar_alertas(sensores, consecutivas=2, leituras=leituras)

    assert resultado == [{"sensor": "S1", "leitura": "L2"}]


def test_sensor_pode_alertar_de_novo_apos_uma_leitura_dentro_da_faixa():
    sensores = [{"sensor": "S1", "minimo": 0, "maximo": 10}]
    leituras = [
        {"id": "L1", "sensor": "S1", "valor": 11},
        {"id": "L2", "sensor": "S1", "valor": 12},  # 1º alerta
        {"id": "L3", "sensor": "S1", "valor": 5},  # dentro da faixa: reinicia
        {"id": "L4", "sensor": "S1", "valor": 20},
        {"id": "L5", "sensor": "S1", "valor": 21},  # 2º alerta
    ]

    resultado = gerar_alertas(sensores, consecutivas=2, leituras=leituras)

    assert resultado == [
        {"sensor": "S1", "leitura": "L2"},
        {"sensor": "S1", "leitura": "L5"},
    ]


def test_alerta_so_nasce_exatamente_no_numero_de_consecutivas_configurado():
    sensores = [{"sensor": "S1", "minimo": 0, "maximo": 10}]
    leituras = [
        {"id": "L1", "sensor": "S1", "valor": 11},
        {"id": "L2", "sensor": "S1", "valor": 12},
        {"id": "L3", "sensor": "S1", "valor": 13},
    ]

    resultado = gerar_alertas(sensores, consecutivas=3, leituras=leituras)

    assert resultado == [{"sensor": "S1", "leitura": "L3"}]
