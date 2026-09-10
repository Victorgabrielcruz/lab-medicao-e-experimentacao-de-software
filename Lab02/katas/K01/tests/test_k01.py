"""Suíte de aceitação de K01 — Conflitos no pátio de docas."""
from solution import conflitos_no_patio


def test_exemplo_do_enunciado():
    agendamentos = [
        {"id": "A1", "doca": "Norte", "inicio": "08:00", "fim": "08:30"},
        {"id": "B1", "doca": "Norte", "inicio": "08:45", "fim": "09:00"},
        {"id": "C1", "doca": "Norte", "inicio": "08:35", "fim": "08:40"},
        {"id": "D1", "doca": "Sul", "inicio": "08:35", "fim": "08:50"},
    ]

    resultado = conflitos_no_patio(agendamentos, margem=10)

    assert resultado == ["A1", "B1", "C1"]


def test_docas_diferentes_nunca_conflitam():
    agendamentos = [
        {"id": "A1", "doca": "Norte", "inicio": "08:00", "fim": "09:00"},
        {"id": "B1", "doca": "Sul", "inicio": "08:00", "fim": "09:00"},
    ]

    resultado = conflitos_no_patio(agendamentos, margem=30)

    assert resultado == []


def test_toque_exato_no_limite_da_margem_e_compativel():
    # B1 começa exatamente quando termina a margem de A1 (08:30 + 10min = 08:40).
    agendamentos = [
        {"id": "A1", "doca": "Norte", "inicio": "08:00", "fim": "08:30"},
        {"id": "B1", "doca": "Norte", "inicio": "08:40", "fim": "09:00"},
    ]

    resultado = conflitos_no_patio(agendamentos, margem=10)

    assert resultado == []


def test_margem_zero_ainda_detecta_sobreposicao_real():
    agendamentos = [
        {"id": "A1", "doca": "Norte", "inicio": "08:00", "fim": "08:30"},
        {"id": "B1", "doca": "Norte", "inicio": "08:20", "fim": "08:50"},
    ]

    resultado = conflitos_no_patio(agendamentos, margem=0)

    assert resultado == ["A1", "B1"]


def test_margem_maxima_transforma_toque_em_conflito():
    # Sem margem, B1 apenas toca o fim de A1 (compatível). Com margem=60,
    # a indisponibilidade de A1 avança até depois do início de B1.
    agendamentos = [
        {"id": "A1", "doca": "Norte", "inicio": "08:00", "fim": "08:30"},
        {"id": "B1", "doca": "Norte", "inicio": "08:30", "fim": "09:00"},
    ]

    resultado = conflitos_no_patio(agendamentos, margem=60)

    assert resultado == ["A1", "B1"]


def test_agendamento_unico_nao_tem_com_que_conflitar():
    agendamentos = [
        {"id": "A1", "doca": "Norte", "inicio": "08:00", "fim": "08:30"},
    ]

    resultado = conflitos_no_patio(agendamentos, margem=30)

    assert resultado == []
