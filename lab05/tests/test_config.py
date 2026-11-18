import sqlite3

from experimento import config
from experimento.config import CARGAS, CONFIGURACOES, CONFIGURACAO_PADRAO, combinacoes, total_execucoes


def test_desenho_fatorial_2x2():
    assert len(CONFIGURACOES) == 4
    assert len({c.nome for c in CONFIGURACOES}) == 4
    assert CONFIGURACAO_PADRAO in CONFIGURACOES


def test_cargas_validas():
    nomes = [c.nome for c in CARGAS]
    assert nomes == ["escrita", "leitura", "mista"]
    for carga in CARGAS:
        assert carga.n_operacoes > 0
        assert 0.0 <= carga.fracao_leitura <= 1.0


def test_parametros_de_repeticao():
    assert config.N_REPETICOES >= 30
    assert 0 < config.N_AQUECIMENTO < config.N_REPETICOES
    assert 0 < config.ALFA < 1
    assert total_execucoes() == len(combinacoes()) * (config.N_REPETICOES + config.N_AQUECIMENTO)


def test_pragmas_aceitos_pelo_sqlite(tmp_path):
    for configuracao in CONFIGURACOES:
        con = sqlite3.connect(tmp_path / f"{configuracao.nome}.db")
        try:
            for pragma in configuracao.pragmas:
                con.execute(pragma)
            modo = con.execute("PRAGMA journal_mode").fetchone()[0]
            sincronismo = con.execute("PRAGMA synchronous").fetchone()[0]
        finally:
            con.close()
        assert modo.upper() == configuracao.journal_mode
        assert sincronismo == {"FULL": 2, "NORMAL": 1}[configuracao.synchronous]
