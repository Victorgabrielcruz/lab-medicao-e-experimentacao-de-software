"""Benchmark local do SQLite: preparação fora da janela cronometrada (#303)."""

import csv
import random
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from experimento import config
from experimento.ambiente import registrar_ambiente, salvar_ambiente
from experimento.config import Carga, Configuracao


@dataclass(frozen=True)
class Execucao:
    configuracao: Configuracao
    carga: Carga
    repeticao: int
    aquecimento: bool
    semente_carga: int


def plano_execucoes(repeticoes: int, aquecimentos: int, semente: int) -> list[Execucao]:
    """Em cada rodada, embaralha todas as combinações; aquece antes de medir.

    A mesma carga/repetição usa a mesma sequência de operações nas quatro
    configurações. A geração das cargas independe do sorteio da ordem.
    """
    if repeticoes < 1 or aquecimentos < 0:
        raise ValueError("Repetições devem ser positivas e aquecimentos não negativos.")
    ordem = random.Random(semente)
    sementes = random.Random(semente)
    plano = []
    for aquecimento, quantidade in ((True, aquecimentos), (False, repeticoes)):
        for repeticao in range(1, quantidade + 1):
            sementes_cargas = {c: sementes.getrandbits(64) for c in config.CARGAS}
            rodada = [
                Execucao(cfg, carga, repeticao, aquecimento, sementes_cargas[carga])
                for cfg, carga in config.combinacoes()
            ]
            ordem.shuffle(rodada)
            plano.extend(rodada)
    return plano


def gerar_operacoes(carga: Carga, linhas_iniciais: int, semente: int) -> list[tuple[str, int]]:
    """Proporção exata (arredondada) de leituras, sempre em chaves existentes."""
    if carga.n_operacoes < 1 or not 0 <= carga.fracao_leitura <= 1 or linhas_iniciais < 1:
        raise ValueError("Carga inválida ou banco inicial vazio.")
    rng = random.Random(semente)
    leituras = round(carga.n_operacoes * carga.fracao_leitura)
    tipos = ["leitura"] * leituras + ["escrita"] * (carga.n_operacoes - leituras)
    rng.shuffle(tipos)
    return [(tipo, rng.randint(1, linhas_iniciais) if tipo == "leitura" else 0) for tipo in tipos]


def aplicar_configuracao(con: sqlite3.Connection, configuracao: Configuracao) -> None:
    """Aplica e consulta os valores efetivos: PRAGMAs podem ser ignorados."""
    if configuracao not in config.CONFIGURACOES:
        raise ValueError(f"Configuração fora do desenho experimental: {configuracao}")
    for pragma in configuracao.pragmas:
        con.execute(pragma).fetchall()
    journal = con.execute("PRAGMA journal_mode").fetchone()[0].upper()
    synchronous = con.execute("PRAGMA synchronous").fetchone()[0]
    if journal != configuracao.journal_mode or synchronous != {"FULL": 2, "NORMAL": 1}[configuracao.synchronous]:
        raise RuntimeError("O SQLite não aplicou os PRAGMAs solicitados.")


def executar_carga(
    con: sqlite3.Connection, operacoes: list[tuple[str, int]], payload: str,
) -> float:
    """Cronometra SQL, consumo das leituras e um commit por INSERT.

    Não inclui geração de operações, criação/população do banco, configuração,
    abertura/fechamento da conexão, CSV ou remoção dos arquivos. Checkpoints
    automáticos acionados durante as operações fazem parte da medição.
    """
    cursor = con.cursor()
    inicio = perf_counter()
    for tipo, chave in operacoes:
        if tipo == "leitura":
            cursor.execute("SELECT payload FROM registros WHERE id = ?", (chave,)).fetchone()
        else:
            cursor.execute("INSERT INTO registros (payload) VALUES (?)", (payload,))
            con.commit()
    tempo = perf_counter() - inicio
    cursor.close()
    if tempo <= 0:
        raise RuntimeError("O relógio não registrou uma duração positiva.")
    return tempo


def medir_execucao(execucao: Execucao, diretorio_bancos: Path) -> dict:
    """Usa banco exclusivo e remove banco/journal/WAL após fechar a conexão."""
    operacoes = gerar_operacoes(execucao.carga, config.LINHAS_INICIAIS, execucao.semente_carga)
    payload = "x" * config.TAMANHO_PAYLOAD  # ASCII: um byte por caractere.
    with tempfile.TemporaryDirectory(prefix="execucao-", dir=diretorio_bancos) as pasta:
        con = sqlite3.connect(Path(pasta) / "banco.sqlite3", isolation_level="DEFERRED")
        try:
            con.execute("CREATE TABLE registros (id INTEGER PRIMARY KEY, payload TEXT NOT NULL)")
            con.executemany(
                "INSERT INTO registros (payload) VALUES (?)",
                ((payload,) for _ in range(config.LINHAS_INICIAIS)),
            )
            con.commit()
            aplicar_configuracao(con, execucao.configuracao)
            tempo = executar_carga(con, operacoes, payload)
        finally:
            con.close()
    n_leituras = sum(tipo == "leitura" for tipo, _ in operacoes)
    return {
        "configuracao": execucao.configuracao.nome,
        "journal_mode": execucao.configuracao.journal_mode,
        "synchronous": execucao.configuracao.synchronous,
        "carga": execucao.carga.nome,
        "repeticao": execucao.repeticao,
        "n_operacoes": len(operacoes),
        "n_leituras": n_leituras,
        "n_escritas": len(operacoes) - n_leituras,
        "tempo_total_s": tempo,
        "vazao_ops_s": len(operacoes) / tempo,
        "semente_carga": execucao.semente_carga,
    }


def coletar(
    diretorio: Path = config.DIR_DADOS,
    *,
    repeticoes: int = config.N_REPETICOES,
    aquecimentos: int = config.N_AQUECIMENTO,
    semente: int = config.SEMENTE,
) -> Path:
    """Salva somente medições; recusa substituir uma coleta já existente.

    CSV incremental: uma falha preserva as linhas concluídas para diagnóstico.
    A completude deve ser validada antes da análise (S02-02).
    """
    plano = plano_execucoes(repeticoes, aquecimentos, semente)
    diretorio = Path(diretorio)
    diretorio.mkdir(parents=True, exist_ok=True)
    bancos = diretorio / "bancos"
    bancos.mkdir(exist_ok=True)
    caminho = diretorio / "resultados.csv"
    # A reserva exclusiva vem antes do ambiente para não sobrescrever outra coleta.
    with caminho.open("x", newline="", encoding="utf-8") as arquivo:
        ambiente = registrar_ambiente(bancos)
        ambiente["experimento"] = {
            "repeticoes": repeticoes, "aquecimentos": aquecimentos, "semente": semente,
            "linhas_iniciais": config.LINHAS_INICIAIS, "tamanho_payload": config.TAMANHO_PAYLOAD,
            "configuracoes": [c.nome for c in config.CONFIGURACOES],
            "cargas": [vars(c) for c in config.CARGAS],
        }
        salvar_ambiente(diretorio / "ambiente.json", ambiente)
        campos_ambiente = {k: v for k, v in ambiente.items() if k != "experimento"}
        escritor = None
        for ordem, execucao in enumerate(plano, start=1):
            resultado = medir_execucao(execucao, bancos)
            if execucao.aquecimento:
                continue
            linha = {
                "ordem_execucao": ordem, **resultado,
                "semente": semente, "linhas_iniciais": config.LINHAS_INICIAIS,
                "tamanho_payload": config.TAMANHO_PAYLOAD, **campos_ambiente,
            }
            if escritor is None:
                escritor = csv.DictWriter(arquivo, fieldnames=list(linha))
                escritor.writeheader()
            escritor.writerow(linha)
            arquivo.flush()
    return caminho
