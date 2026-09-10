"""Suíte de aceitação de K03 — Cadeia de custódia de remessas."""
from solution import avaliar_cadeia_de_custodia


def test_exemplo_do_enunciado():
    eventos = [
        {"id": "E1", "remessa": "R1", "etapa": "COLETA"},
        {"id": "E2", "remessa": "R1", "etapa": "DESPACHO"},
        {"id": "E3", "remessa": "R2", "etapa": "LACRE"},
        {"id": "E4", "remessa": "R1", "etapa": "LACRE"},
        {"id": "E5", "remessa": "R1", "etapa": "DESPACHO"},
        {"id": "E6", "remessa": "R1", "etapa": "RECEBIMENTO"},
        {"id": "E7", "remessa": "R3", "etapa": "COLETA"},
    ]

    resultado = avaliar_cadeia_de_custodia(eventos)

    assert resultado["aceitos"] == ["E1", "E4", "E5", "E6", "E7"]
    assert resultado["recusados"] == ["E2", "E3"]
    assert resultado["pendentes"] == ["R3"]


def test_remessa_sem_coleta_nunca_e_pendente():
    # Nenhum evento de R1 é aceito porque o primeiro não é COLETA.
    eventos = [
        {"id": "E1", "remessa": "R1", "etapa": "LACRE"},
        {"id": "E2", "remessa": "R1", "etapa": "DESPACHO"},
    ]

    resultado = avaliar_cadeia_de_custodia(eventos)

    assert resultado["aceitos"] == []
    assert resultado["recusados"] == ["E1", "E2"]
    assert resultado["pendentes"] == []


def test_remessa_concluida_nao_aparece_como_pendente():
    eventos = [
        {"id": "E1", "remessa": "R1", "etapa": "COLETA"},
        {"id": "E2", "remessa": "R1", "etapa": "LACRE"},
        {"id": "E3", "remessa": "R1", "etapa": "DESPACHO"},
        {"id": "E4", "remessa": "R1", "etapa": "RECEBIMENTO"},
    ]

    resultado = avaliar_cadeia_de_custodia(eventos)

    assert resultado["aceitos"] == ["E1", "E2", "E3", "E4"]
    assert resultado["pendentes"] == []


def test_etapa_recusada_nao_muda_a_etapa_confirmada():
    eventos = [
        {"id": "E1", "remessa": "R1", "etapa": "COLETA"},
        {"id": "E2", "remessa": "R1", "etapa": "COLETA"},  # repetida, fora de ordem
        {"id": "E3", "remessa": "R1", "etapa": "LACRE"},  # continua a partir de COLETA
    ]

    resultado = avaliar_cadeia_de_custodia(eventos)

    assert resultado["aceitos"] == ["E1", "E3"]
    assert resultado["recusados"] == ["E2"]


def test_nenhum_evento_e_aceito_apos_recebimento():
    eventos = [
        {"id": "E1", "remessa": "R1", "etapa": "COLETA"},
        {"id": "E2", "remessa": "R1", "etapa": "LACRE"},
        {"id": "E3", "remessa": "R1", "etapa": "DESPACHO"},
        {"id": "E4", "remessa": "R1", "etapa": "RECEBIMENTO"},
        {"id": "E5", "remessa": "R1", "etapa": "COLETA"},
    ]

    resultado = avaliar_cadeia_de_custodia(eventos)

    assert resultado["recusados"] == ["E5"]


def test_pendentes_seguem_a_ordem_de_primeira_ocorrencia():
    eventos = [
        {"id": "E1", "remessa": "R2", "etapa": "COLETA"},
        {"id": "E2", "remessa": "R1", "etapa": "COLETA"},
    ]

    resultado = avaliar_cadeia_de_custodia(eventos)

    assert resultado["pendentes"] == ["R2", "R1"]
