from hipotese.config import CORES_TESTES, TESTE_BINOMIAL, TESTE_Z, gerador


def test_gerador_reproduz_a_mesma_sequencia():
    assert (gerador().random(5) == gerador().random(5)).all()


def test_cada_teste_tem_cor_propria():
    assert set(CORES_TESTES) == {TESTE_Z, TESTE_BINOMIAL}
    assert len(set(CORES_TESTES.values())) == 2
