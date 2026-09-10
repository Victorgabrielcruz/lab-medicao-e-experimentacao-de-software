"""Suíte de aceitação de K04 — Credenciais de visita."""
from solution import avaliar_credenciais


def test_exemplo_do_enunciado():
    credenciais = [
        {"credencial": "V1", "expiraEm": "10:30"},
        {"credencial": "V2", "expiraEm": "09:00"},
    ]
    eventos = [
        {"id": "E1", "credencial": "V1", "momento": "10:00", "acao": "LIBERAR"},
        {"id": "E2", "credencial": "V2", "momento": "09:00", "acao": "LIBERAR"},
        {"id": "E3", "credencial": "V2", "momento": "09:01", "acao": "USAR"},
        {"id": "E4", "credencial": "V1", "momento": "10:20", "acao": "USAR"},
        {"id": "E5", "credencial": "V1", "momento": "10:25", "acao": "REVOGAR"},
    ]

    resultado = avaliar_credenciais(credenciais, eventos)

    assert resultado["aceitos"] == ["E1", "E2", "E4"]
    assert resultado["recusados"] == ["E3", "E5"]
    assert resultado["statusFinal"] == [
        {"credencial": "V1", "status": "UTILIZADA"},
        {"credencial": "V2", "status": "LIBERADA"},
    ]


def test_acao_no_horario_exato_de_expiracao_e_aceita():
    credenciais = [{"credencial": "V1", "expiraEm": "10:00"}]
    eventos = [
        {"id": "E1", "credencial": "V1", "momento": "10:00", "acao": "LIBERAR"},
    ]

    resultado = avaliar_credenciais(credenciais, eventos)

    assert resultado["aceitos"] == ["E1"]
    assert resultado["statusFinal"] == [{"credencial": "V1", "status": "LIBERADA"}]


def test_acao_um_minuto_apos_expiracao_e_recusada():
    credenciais = [{"credencial": "V1", "expiraEm": "10:00"}]
    eventos = [
        {"id": "E1", "credencial": "V1", "momento": "10:01", "acao": "LIBERAR"},
    ]

    resultado = avaliar_credenciais(credenciais, eventos)

    assert resultado["recusados"] == ["E1"]
    assert resultado["statusFinal"] == [{"credencial": "V1", "status": "NOVA"}]


def test_revogar_e_valido_direto_a_partir_de_nova():
    credenciais = [{"credencial": "V1", "expiraEm": "10:00"}]
    eventos = [
        {"id": "E1", "credencial": "V1", "momento": "09:00", "acao": "REVOGAR"},
    ]

    resultado = avaliar_credenciais(credenciais, eventos)

    assert resultado["aceitos"] == ["E1"]
    assert resultado["statusFinal"] == [{"credencial": "V1", "status": "REVOGADA"}]


def test_usar_sem_liberar_antes_e_recusado():
    credenciais = [{"credencial": "V1", "expiraEm": "10:00"}]
    eventos = [
        {"id": "E1", "credencial": "V1", "momento": "09:00", "acao": "USAR"},
    ]

    resultado = avaliar_credenciais(credenciais, eventos)

    assert resultado["recusados"] == ["E1"]
    assert resultado["statusFinal"] == [{"credencial": "V1", "status": "NOVA"}]


def test_estados_finais_nao_aceitam_novos_eventos():
    credenciais = [{"credencial": "V1", "expiraEm": "10:00"}]
    eventos = [
        {"id": "E1", "credencial": "V1", "momento": "09:00", "acao": "REVOGAR"},
        {"id": "E2", "credencial": "V1", "momento": "09:05", "acao": "LIBERAR"},
    ]

    resultado = avaliar_credenciais(credenciais, eventos)

    assert resultado["recusados"] == ["E2"]
    assert resultado["statusFinal"] == [{"credencial": "V1", "status": "REVOGADA"}]
