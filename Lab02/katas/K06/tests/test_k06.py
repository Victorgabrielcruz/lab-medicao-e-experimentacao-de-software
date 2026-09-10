"""Suíte de aceitação de K06 — Roteiros de inspeção."""
from solution import avaliar_visitas


def test_exemplo_do_enunciado():
    roteiros = [
        {"rota": "A", "pontos": ["P1", "P2", "P3"]},
        {"rota": "B", "pontos": ["X", "Y"]},
    ]
    visitas = [
        {"id": "V1", "rota": "A", "ponto": "P1"},
        {"id": "V2", "rota": "B", "ponto": "Y"},
        {"id": "V3", "rota": "B", "ponto": "X"},
        {"id": "V4", "rota": "A", "ponto": "P3"},
        {"id": "V5", "rota": "A", "ponto": "P2"},
        {"id": "V6", "rota": "A", "ponto": "P3"},
        {"id": "V7", "rota": "B", "ponto": "Y"},
    ]

    resultado = avaliar_visitas(roteiros, visitas)

    assert resultado["aceitos"] == ["V1", "V3", "V5", "V6", "V7"]
    assert resultado["recusados"] == ["V2", "V4"]
    assert resultado["concluidas"] == ["A", "B"]
    assert resultado["pendentes"] == []


def test_rota_sem_nenhuma_visita_fica_pendente():
    roteiros = [{"rota": "A", "pontos": ["P1", "P2"]}]
    visitas = []

    resultado = avaliar_visitas(roteiros, visitas)

    assert resultado["concluidas"] == []
    assert resultado["pendentes"] == ["A"]


def test_ponto_recusado_nao_substitui_a_proxima_parada_esperada():
    roteiros = [{"rota": "A", "pontos": ["P1", "P2", "P3"]}]
    visitas = [
        {"id": "V1", "rota": "A", "ponto": "P1"},
        {"id": "V2", "rota": "A", "ponto": "P3"},  # fora de ordem: recusada
        {"id": "V3", "rota": "A", "ponto": "P2"},  # ainda é a esperada
        {"id": "V4", "rota": "A", "ponto": "P3"},
    ]

    resultado = avaliar_visitas(roteiros, visitas)

    assert resultado["aceitos"] == ["V1", "V3", "V4"]
    assert resultado["recusados"] == ["V2"]
    assert resultado["concluidas"] == ["A"]


def test_rota_concluida_nao_aceita_novas_visitas():
    roteiros = [{"rota": "A", "pontos": ["P1", "P2"]}]
    visitas = [
        {"id": "V1", "rota": "A", "ponto": "P1"},
        {"id": "V2", "rota": "A", "ponto": "P2"},
        {"id": "V3", "rota": "A", "ponto": "P1"},
    ]

    resultado = avaliar_visitas(roteiros, visitas)

    assert resultado["aceitos"] == ["V1", "V2"]
    assert resultado["recusados"] == ["V3"]
    assert resultado["concluidas"] == ["A"]


def test_concluidas_e_pendentes_seguem_a_ordem_dos_roteiros():
    roteiros = [
        {"rota": "A", "pontos": ["P1"]},
        {"rota": "B", "pontos": ["X"]},
        {"rota": "C", "pontos": ["Z"]},
    ]
    visitas = [
        {"id": "V1", "rota": "C", "ponto": "Z"},
        {"id": "V2", "rota": "A", "ponto": "P1"},
    ]

    resultado = avaliar_visitas(roteiros, visitas)

    assert resultado["concluidas"] == ["A", "C"]
    assert resultado["pendentes"] == ["B"]
