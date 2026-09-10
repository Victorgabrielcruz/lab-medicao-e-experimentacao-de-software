"""Suíte de aceitação de K02 — Compartimentos de coleta."""
from solution import processar_movimentos


def test_exemplo_do_enunciado():
    capacidades = [
        {"compartimento": "A", "capacidade": 10},
        {"compartimento": "B", "capacidade": 5},
    ]
    movimentos = [
        {"id": "M1", "compartimento": "A", "tipo": "ENTRADA", "quantidade": 6},
        {"id": "M2", "compartimento": "A", "tipo": "SAIDA", "quantidade": 7},
        {"id": "M3", "compartimento": "B", "tipo": "ENTRADA", "quantidade": 5},
        {"id": "M4", "compartimento": "B", "tipo": "ENTRADA", "quantidade": 1},
        {"id": "M5", "compartimento": "A", "tipo": "SAIDA", "quantidade": 2},
    ]

    resultado = processar_movimentos(capacidades, movimentos)

    assert resultado["aceitos"] == ["M1", "M3", "M5"]
    assert resultado["recusados"] == ["M2", "M4"]
    assert resultado["saldoFinal"] == [
        {"compartimento": "A", "saldo": 4},
        {"compartimento": "B", "saldo": 5},
    ]


def test_entrada_que_atinge_exatamente_a_capacidade_e_aceita():
    capacidades = [{"compartimento": "A", "capacidade": 10}]
    movimentos = [
        {"id": "M1", "compartimento": "A", "tipo": "ENTRADA", "quantidade": 10},
    ]

    resultado = processar_movimentos(capacidades, movimentos)

    assert resultado["aceitos"] == ["M1"]
    assert resultado["recusados"] == []
    assert resultado["saldoFinal"] == [{"compartimento": "A", "saldo": 10}]


def test_saida_que_zera_o_saldo_e_aceita():
    capacidades = [{"compartimento": "A", "capacidade": 10}]
    movimentos = [
        {"id": "M1", "compartimento": "A", "tipo": "ENTRADA", "quantidade": 5},
        {"id": "M2", "compartimento": "A", "tipo": "SAIDA", "quantidade": 5},
    ]

    resultado = processar_movimentos(capacidades, movimentos)

    assert resultado["aceitos"] == ["M1", "M2"]
    assert resultado["saldoFinal"] == [{"compartimento": "A", "saldo": 0}]


def test_movimento_recusado_nao_altera_o_saldo():
    capacidades = [{"compartimento": "A", "capacidade": 10}]
    movimentos = [
        {"id": "M1", "compartimento": "A", "tipo": "SAIDA", "quantidade": 1},
        {"id": "M2", "compartimento": "A", "tipo": "ENTRADA", "quantidade": 3},
    ]

    resultado = processar_movimentos(capacidades, movimentos)

    # M1 é recusado (saldo negativo); o saldo continua zero para o M2 aceitar.
    assert resultado["recusados"] == ["M1"]
    assert resultado["aceitos"] == ["M2"]
    assert resultado["saldoFinal"] == [{"compartimento": "A", "saldo": 3}]


def test_compartimentos_sao_independentes():
    capacidades = [
        {"compartimento": "A", "capacidade": 2},
        {"compartimento": "B", "capacidade": 100},
    ]
    movimentos = [
        {"id": "M1", "compartimento": "B", "tipo": "ENTRADA", "quantidade": 50},
        {"id": "M2", "compartimento": "A", "tipo": "ENTRADA", "quantidade": 3},
    ]

    resultado = processar_movimentos(capacidades, movimentos)

    assert resultado["aceitos"] == ["M1"]
    assert resultado["recusados"] == ["M2"]
    assert resultado["saldoFinal"] == [
        {"compartimento": "A", "saldo": 0},
        {"compartimento": "B", "saldo": 50},
    ]
