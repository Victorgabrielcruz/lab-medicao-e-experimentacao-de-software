import pytest

from solution import expandir_mensagem


def test_expande_blocos_na_ordem():
    assert expandir_mensagem([("ab", 2), ("!", 3)]) == "abab!!!"


def test_aceita_lista_vazia_e_repeticao_zero():
    assert expandir_mensagem([]) == ""
    assert expandir_mensagem([("x", 0), ("fim", 1)]) == "fim"


@pytest.mark.parametrize(
    "blocos",
    [
        [("", 1)],
        [(1, 1)],
        [("x", -1)],
        [("x", 21)],
        [("x", 1.5)],
        [("x", True)],
    ],
)
def test_rejeita_blocos_invalidos(blocos):
    with pytest.raises(ValueError):
        expandir_mensagem(blocos)
