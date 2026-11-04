import numpy as np
import pytest

from hipotese.cenario import carregar_resumo
from hipotese.config import EFEITO_EXEMPLO, gerador
from hipotese.exemplo import gerar_exemplo
from hipotese.gerador import gerar_builds, taxa_com_efeito
from hipotese.testes import aplicar_testes


def test_exemplo_reproduz_a_amostra_unica_definida_no_protocolo():
    exemplo = gerar_exemplo()
    n = carregar_resumo()["estatisticas"]["n_execucoes"]
    referencia = gerar_builds(gerador(), n=n, taxa_falha=taxa_com_efeito(EFEITO_EXEMPLO))
    assert exemplo.taxa_verdadeira == pytest.approx(0.09)
    assert np.array_equal(exemplo.builds, referencia)
    assert exemplo.resultados == aplicar_testes(referencia)
    assert np.array_equal(gerar_exemplo().builds, exemplo.builds)
    assert exemplo.resultados[0].falhas == exemplo.resultados[1].falhas == int(referencia.sum())
