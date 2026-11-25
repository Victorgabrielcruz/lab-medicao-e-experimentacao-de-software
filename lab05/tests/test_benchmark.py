import csv
import json
import sqlite3
from collections import Counter

import pytest

import executar
from experimento import benchmark, config
from experimento.benchmark import Execucao
from experimento.config import Carga, Configuracao


@pytest.fixture
def desenho_curto(monkeypatch):
    monkeypatch.setattr(config, "LINHAS_INICIAIS", 10)
    monkeypatch.setattr(config, "TAMANHO_PAYLOAD", 16)
    monkeypatch.setattr(config, "CARGAS", (
        Carga("escrita", 10, 0.0), Carga("leitura", 10, 1.0), Carga("mista", 10, 0.7),
    ))


def test_plano_completo_reprodutivel_e_aleatorizado():
    plano = benchmark.plano_execucoes(30, 3, 42)
    assert len(plano) == 396
    assert sum(not e.aquecimento for e in plano) == 360
    assert all(e.aquecimento for e in plano[:36])
    assert all(not e.aquecimento for e in plano[36:])
    assert plano == benchmark.plano_execucoes(30, 3, 42)
    assert plano != benchmark.plano_execucoes(30, 3, 43)
    esperado = Counter(config.combinacoes())
    ordens = []
    for inicio in range(0, len(plano), 12):
        rodada = plano[inicio:inicio + 12]
        pares = [(e.configuracao, e.carga) for e in rodada]
        assert Counter(pares) == esperado
        ordens.append(tuple(pares))
        for carga in config.CARGAS:
            assert len({e.semente_carga for e in rodada if e.carga == carga}) == 1
    assert len(set(ordens)) > 1


@pytest.mark.parametrize("carga", config.CARGAS, ids=lambda c: c.nome)
def test_cargas_tem_proporcao_exata_e_chaves_existentes(carga):
    operacoes = benchmark.gerar_operacoes(carga, 10_000, 42)
    assert operacoes == benchmark.gerar_operacoes(carga, 10_000, 42)
    assert len(operacoes) == carga.n_operacoes
    assert sum(t == "leitura" for t, _ in operacoes) == round(carga.n_operacoes * carga.fracao_leitura)
    assert all(1 <= chave <= 10_000 for tipo, chave in operacoes if tipo == "leitura")


@pytest.mark.parametrize("cfg", config.CONFIGURACOES, ids=lambda c: c.nome)
def test_medicao_aplica_pragmas_banco_novo_e_commit_por_escrita(tmp_path, monkeypatch, desenho_curto, cfg):
    executar_real = benchmark.executar_carga
    observacoes = []

    def observar(con, operacoes, payload):
        assert con.execute("SELECT count(*) FROM registros").fetchone()[0] == 10
        assert con.execute("SELECT min(length(payload)), max(length(payload)) FROM registros").fetchone() == (16, 16)
        assert con.execute("PRAGMA journal_mode").fetchone()[0].upper() == cfg.journal_mode
        assert con.execute("PRAGMA synchronous").fetchone()[0] == {"FULL": 2, "NORMAL": 1}[cfg.synchronous]
        assert not con.in_transaction
        sql = []
        con.set_trace_callback(sql.append)
        tempo = executar_real(con, operacoes, payload)
        con.set_trace_callback(None)
        assert sum(s.startswith("SELECT") for s in sql) == 7
        assert sum(s.startswith("INSERT") for s in sql) == 3
        assert sum(s.startswith("BEGIN") for s in sql) == 3
        assert sql.count("COMMIT") == 3
        assert not con.in_transaction
        assert con.execute("SELECT count(*) FROM registros").fetchone()[0] == 13
        observacoes.append(sql)
        return tempo

    monkeypatch.setattr(benchmark, "executar_carga", observar)
    execucao = Execucao(cfg, config.CARGAS[2], 1, False, 42)
    for _ in range(2):
        resultado = benchmark.medir_execucao(execucao, tmp_path)
        assert resultado["n_leituras"] == 7
        assert resultado["n_escritas"] == 3
        assert resultado["tempo_total_s"] > 0
        assert resultado["vazao_ops_s"] == pytest.approx(10 / resultado["tempo_total_s"])
        assert list(tmp_path.iterdir()) == []
    assert observacoes[0] == observacoes[1]


def test_csv_so_tem_medicoes_e_registra_ordem_ambiente_e_parametros(tmp_path, desenho_curto):
    caminho = benchmark.coletar(tmp_path, repeticoes=2, aquecimentos=1, semente=42)
    with caminho.open(newline="", encoding="utf-8") as arquivo:
        linhas = list(csv.DictReader(arquivo))
    assert len(linhas) == 24
    assert {int(l["ordem_execucao"]) for l in linhas} == set(range(13, 37))
    assert Counter((l["configuracao"], l["carga"], int(l["repeticao"])) for l in linhas) == Counter(
        (cfg.nome, carga.nome, repeticao)
        for cfg, carga in config.combinacoes() for repeticao in (1, 2)
    )
    ambiente = json.loads((tmp_path / "ambiente.json").read_text(encoding="utf-8"))
    assert ambiente["experimento"]["repeticoes"] == 2
    assert ambiente["experimento"]["aquecimentos"] == 1
    assert ambiente["experimento"]["cargas"][2]["fracao_leitura"] == 0.7
    for linha in linhas:
        assert float(linha["tempo_total_s"]) > 0
        assert float(linha["vazao_ops_s"]) == pytest.approx(10 / float(linha["tempo_total_s"]))
        assert int(linha["n_leituras"]) + int(linha["n_escritas"]) == 10
        assert linha["sqlite_version"] == sqlite3.sqlite_version
        for campo, valor in ambiente.items():
            if campo != "experimento":
                assert linha[campo] == str(valor)
    assert list((tmp_path / "bancos").iterdir()) == []


def test_coleta_nao_sobrescreve_resultados_ou_ambiente(tmp_path, desenho_curto):
    caminho = benchmark.coletar(tmp_path, repeticoes=1, aquecimentos=0)
    csv_original = caminho.read_bytes()
    ambiente_original = (tmp_path / "ambiente.json").read_bytes()
    with pytest.raises(FileExistsError):
        benchmark.coletar(tmp_path, repeticoes=1, aquecimentos=0)
    assert caminho.read_bytes() == csv_original
    assert (tmp_path / "ambiente.json").read_bytes() == ambiente_original


def test_falha_preserva_medicoes_concluidas(tmp_path, monkeypatch, desenho_curto):
    medir_real = benchmark.medir_execucao
    chamadas = 0

    def falhar_na_terceira(execucao, bancos):
        nonlocal chamadas
        chamadas += 1
        if chamadas == 3:
            raise RuntimeError("coleta interrompida")
        return medir_real(execucao, bancos)

    monkeypatch.setattr(benchmark, "medir_execucao", falhar_na_terceira)
    with pytest.raises(RuntimeError, match="interrompida"):
        benchmark.coletar(tmp_path, repeticoes=1, aquecimentos=0)
    with (tmp_path / "resultados.csv").open(encoding="utf-8", newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo))
    assert len(linhas) == 2
    assert [int(l["ordem_execucao"]) for l in linhas] == [1, 2]
    assert list((tmp_path / "bancos").iterdir()) == []


def test_falha_fecha_conexao_e_remove_banco_e_auxiliares(tmp_path, monkeypatch, desenho_curto):
    conexoes = []

    def falhar(con, operacoes, payload):
        conexoes.append(con)
        con.execute("INSERT INTO registros (payload) VALUES (?)", (payload,))
        raise RuntimeError("falha simulada")

    monkeypatch.setattr(benchmark, "executar_carga", falhar)
    execucao = Execucao(Configuracao("WAL", "NORMAL"), config.CARGAS[0], 1, False, 42)
    with pytest.raises(RuntimeError, match="falha simulada"):
        benchmark.medir_execucao(execucao, tmp_path)
    assert list(tmp_path.iterdir()) == []
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        conexoes[0].execute("SELECT 1")


def test_pragmas_nao_aplicados_interrompem_medicao():
    class ConexaoIgnoraPragmas:
        def execute(self, sql):
            self.sql = sql
            return self

        def fetchall(self):
            return []

        def fetchone(self):
            return ("delete",) if self.sql.endswith("journal_mode") else (2,)

    with pytest.raises(RuntimeError, match="PRAGMAs"):
        benchmark.aplicar_configuracao(ConexaoIgnoraPragmas(), Configuracao("WAL", "NORMAL"))


@pytest.mark.parametrize("repeticoes,aquecimentos", [(0, 0), (-1, 0), (1, -1)])
def test_parametros_invalidos_nao_criam_saida(tmp_path, repeticoes, aquecimentos):
    with pytest.raises(ValueError):
        benchmark.coletar(tmp_path / "saida", repeticoes=repeticoes, aquecimentos=aquecimentos)
    assert not (tmp_path / "saida").exists()


def test_cli_executa_coleta_curta(tmp_path, desenho_curto, capsys):
    executar.main(["--diretorio", str(tmp_path), "--repeticoes", "1", "--aquecimentos", "0"])
    assert "Medições salvas" in capsys.readouterr().out
    with (tmp_path / "resultados.csv").open(encoding="utf-8") as arquivo:
        assert len(list(csv.DictReader(arquivo))) == 12


def test_cli_recusa_parametros_invalidos(tmp_path):
    with pytest.raises(SystemExit) as erro:
        executar.main(["--diretorio", str(tmp_path / "saida"), "--repeticoes", "0"])
    assert erro.value.code == 2
    assert not (tmp_path / "saida").exists()


def test_progresso_inclui_aquecimentos_e_medicoes(tmp_path, desenho_curto, monkeypatch):
    eventos = []
    medir_real = benchmark.medir_execucao
    medindo = False

    def medir(execucao, bancos):
        nonlocal medindo
        medindo = True
        try:
            return medir_real(execucao, bancos)
        finally:
            medindo = False

    def progresso(ordem, total, execucao):
        assert not medindo
        eventos.append((ordem, total, execucao.aquecimento))

    monkeypatch.setattr(benchmark, "medir_execucao", medir)
    benchmark.coletar(tmp_path, repeticoes=1, aquecimentos=1, progresso=progresso)
    assert eventos == [(i, 24, i <= 12) for i in range(1, 25)]
    with (tmp_path / "resultados.csv").open(encoding="utf-8") as arquivo:
        assert len(list(csv.DictReader(arquivo))) == 12


def test_cli_mostra_progresso(tmp_path, desenho_curto, capsys):
    executar.main(["--diretorio", str(tmp_path), "--repeticoes", "1", "--aquecimentos", "0", "--progresso"])
    saida = capsys.readouterr().out
    assert "100.0%" in saida
    assert "[ 12/12]" in saida
