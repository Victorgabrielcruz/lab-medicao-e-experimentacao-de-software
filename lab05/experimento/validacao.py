"""Validação da coleta completa (#307), sem excluir ou modificar medições."""

import csv
import hashlib
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from experimento import config
from experimento.benchmark import plano_execucoes

COLUNAS = (
    "ordem_execucao", "configuracao", "journal_mode", "synchronous", "carga", "repeticao",
    "n_operacoes", "n_leituras", "n_escritas", "tempo_total_s", "vazao_ops_s",
    "semente_carga", "semente", "linhas_iniciais", "tamanho_payload", "data_hora_utc",
    "sqlite_version", "python_version", "python_implementacao", "sistema", "sistema_versao",
    "maquina", "processador", "n_cpus", "disco_total_gb", "disco_livre_gb",
    "diretorio_banco", "executavel_python",
)
INTEIROS = (
    "ordem_execucao", "repeticao", "n_operacoes", "n_leituras", "n_escritas",
    "semente_carga", "semente", "linhas_iniciais", "tamanho_payload", "n_cpus",
)
REAIS = ("tempo_total_s", "vazao_ops_s", "disco_total_gb", "disco_livre_gb")
ARTEFATOS = ("resultados.csv", "ambiente.json", "execucao.json", "lancador.py")
COMPARACOES = (
    ("H1", "WAL-FULL", "DELETE-FULL"),
    ("H2", "WAL-NORMAL", "WAL-FULL"),
    ("H3", "DELETE-NORMAL", "DELETE-FULL"),
)
COLUNAS_OUTLIERS = (
    "coleta", "linha_csv", "ordem_execucao", "configuracao", "carga", "repeticao",
    "metrica", "valor", "q1", "q3", "iqr", "limite_inferior", "limite_superior", "acao",
)
COLUNAS_TEMPORAIS = (
    "serie", "carga", "configuracao_ou_comparacao", "metrica", "n",
    "spearman_ordem", "correlacao_lag1", "mediana_primeira_metade",
    "mediana_segunda_metade", "diferenca_entre_metades",
)


def sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def _data(valor):
    data = datetime.fromisoformat(valor)
    if data.tzinfo is None or data.utcoffset() is None:
        raise ValueError("Data sem fuso horário.")
    return data


def _correlacao(x, y):
    mx, my = statistics.mean(x), statistics.mean(y)
    sx = sum((v - mx) ** 2 for v in x)
    sy = sum((v - my) ** 2 for v in y)
    if sx == 0 or sy == 0:
        return None  # Série constante: correlação não definida.
    return max(-1.0, min(1.0, sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(sx * sy)))


def _postos(valores):
    resultado = [0.0] * len(valores)
    ordenados = sorted(range(len(valores)), key=valores.__getitem__)
    inicio = 0
    while inicio < len(ordenados):
        fim = inicio + 1
        while fim < len(ordenados) and valores[ordenados[fim]] == valores[ordenados[inicio]]:
            fim += 1
        posto = (inicio + 1 + fim) / 2
        for indice in ordenados[inicio:fim]:
            resultado[indice] = posto
        inicio = fim
    return resultado


def diagnostico_temporal(valores, ordens, *, serie, carga, nome, metrica):
    metade = len(valores) // 2
    primeira, segunda = statistics.median(valores[:metade]), statistics.median(valores[metade:])
    return {
        "serie": serie, "carga": carga, "configuracao_ou_comparacao": nome,
        "metrica": metrica, "n": len(valores),
        "spearman_ordem": _correlacao(_postos(ordens), _postos(valores)),
        "correlacao_lag1": _correlacao(valores[:-1], valores[1:]),
        "mediana_primeira_metade": primeira, "mediana_segunda_metade": segunda,
        "diferenca_entre_metades": segunda - primeira,
    }


def diagnosticar(linhas, coleta):
    grupos = defaultdict(list)
    for linha in linhas:
        grupos[(linha["configuracao"], linha["carga"])].append(linha)
    outliers, temporal, contagens = [], [], []
    for (cfg, carga), grupo in sorted(grupos.items()):
        grupo.sort(key=lambda l: l["ordem_execucao"])
        contagens.append({"configuracao": cfg, "carga": carga, "n": len(grupo)})
        for metrica in ("tempo_total_s", "vazao_ops_s"):
            valores = [l[metrica] for l in grupo]
            q1, _, q3 = statistics.quantiles(valores, n=4, method="inclusive")
            iqr = q3 - q1
            inferior, superior = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            for linha in grupo:
                if linha[metrica] < inferior or linha[metrica] > superior:
                    outliers.append({
                        "coleta": coleta, "linha_csv": linha["linha_csv"],
                        "ordem_execucao": linha["ordem_execucao"], "configuracao": cfg,
                        "carga": carga, "repeticao": linha["repeticao"], "metrica": metrica,
                        "valor": linha[metrica], "q1": q1, "q3": q3, "iqr": iqr,
                        "limite_inferior": inferior, "limite_superior": superior,
                        "acao": "preservar",
                    })
            temporal.append(diagnostico_temporal(
                valores, [l["ordem_execucao"] for l in grupo], serie="grupo", carga=carga,
                nome=cfg, metrica=metrica,
            ))
    # Preserva o pareamento por rodada e semente nas diferenças de M2 do plano.
    por_par = {(l["carga"], l["repeticao"], l["configuracao"]): l for l in linhas}
    for carga in config.CARGAS:
        for hipotese, tratamento, referencia in COMPARACOES:
            diferencas = [
                por_par[(carga.nome, r, tratamento)]["vazao_ops_s"]
                - por_par[(carga.nome, r, referencia)]["vazao_ops_s"]
                for r in range(1, config.N_REPETICOES + 1)
            ]
            temporal.append(diagnostico_temporal(
                diferencas, list(range(1, config.N_REPETICOES + 1)), serie="diferenca_pareada",
                carga=carga.nome, nome=hipotese, metrica="diferenca_vazao_ops_s",
            ))
    return contagens, outliers, temporal


def validar(diretorio: Path) -> dict:
    """Retorna erros estruturados; aprovação estrutural não atesta independência."""
    diretorio = Path(diretorio)
    erros = []

    def erro(codigo, mensagem, linha=None, campo=None):
        erros.append({"codigo": codigo, "linha_csv": linha, "campo": campo, "mensagem": mensagem})

    documentos, hashes = {}, {}
    for nome in (*ARTEFATOS, "conferencia.json"):
        try:
            hashes[nome] = sha256(diretorio / nome)
            if nome.endswith(".json"):
                documentos[nome] = json.loads((diretorio / nome).read_text(encoding="utf-8"))
                if not isinstance(documentos[nome], dict):
                    documentos[nome] = {}
                    raise ValueError("JSON deve ser um objeto.")
        except (OSError, ValueError) as exc:
            erro("arquivo", f"{nome}: {exc}")
    ambiente = documentos.get("ambiente.json", {})
    execucao = documentos.get("execucao.json", {})
    conferencia = documentos.get("conferencia.json", {})
    hashes_originais = conferencia.get("sha256_artefatos", {})
    if not isinstance(hashes_originais, dict):
        erro("integridade", "sha256_artefatos deve ser um objeto com os hashes originais.")
        hashes_originais = {}
    for nome in ARTEFATOS:
        esperado = hashes_originais.get(nome)
        if nome in hashes and hashes[nome] != esperado:
            erro("integridade", f"Hash de {nome} difere da conferência original da #306.")
    if hashes.get("lancador.py") != execucao.get("sha256_lancador"):
        erro("integridade", "Hash do lançador difere de execucao.json.")
    if execucao.get("status") != "concluida" or execucao.get("codigo_saida") != 0:
        erro("execucao", "A coleta não foi registrada como concluída com código 0.")
    try:
        inicio, fim = _data(execucao["inicio_utc"]), _data(execucao["fim_utc"])
        momento = _data(ambiente["data_hora_utc"])
        duracao = float(execucao["duracao_parede_s"])
        if not inicio <= momento <= fim or not math.isfinite(duracao) or duracao <= 0:
            raise ValueError("Janela temporal ou duração inválida.")
        if abs((fim - inicio).total_seconds() - duracao) > 2:
            raise ValueError("Duração difere em mais de 2 s da janela registrada.")
    except (KeyError, TypeError, ValueError) as exc:
        erro("execucao", f"Metadados temporais: {exc}")
    esperado_parametros = {
        "repeticoes": config.N_REPETICOES, "aquecimentos": config.N_AQUECIMENTO,
        "semente": config.SEMENTE, "linhas_iniciais": config.LINHAS_INICIAIS,
        "tamanho_payload": config.TAMANHO_PAYLOAD,
        "configuracoes": [c.nome for c in config.CONFIGURACOES],
        "cargas": [vars(c) for c in config.CARGAS],
    }
    if ambiente.get("experimento") != esperado_parametros:
        erro("protocolo", "Parâmetros do ambiente diferem do protocolo completo (30/3/42).")
    for campo in COLUNAS[15:]:
        if campo not in ambiente or ambiente[campo] is None or str(ambiente[campo]).strip() == "":
            erro("ambiente", "Campo obrigatório ausente no ambiente.", campo=campo)
    linhas_brutas = []
    try:
        with (diretorio / "resultados.csv").open(encoding="utf-8", newline="") as arquivo:
            leitor = csv.DictReader(arquivo, strict=True)
            cabecalho = leitor.fieldnames or []
            if len(cabecalho) != len(set(cabecalho)) or set(cabecalho) != set(COLUNAS):
                erro("schema", "Colunas ausentes, extras ou duplicadas no CSV.")
            linhas_brutas = list(leitor)
    except (OSError, csv.Error, UnicodeError) as exc:
        erro("arquivo", f"resultados.csv: {exc}")
    linhas = []
    for numero, bruta in enumerate(linhas_brutas, 2):
        if None in bruta:
            erro("schema", "Linha possui valores além do cabeçalho.", numero)
            continue
        ausentes = [c for c in COLUNAS if bruta.get(c) is None or not bruta[c].strip()
                    or bruta[c].strip().lower() in ("null", "none", "na", "n/a")]
        if ausentes:
            for c in ausentes:
                erro("ausente", "Valor obrigatório ausente.", numero, c)
            continue
        linha = dict(bruta, linha_csv=numero)
        invalida = False
        for campo in INTEIROS:
            if not re.fullmatch(r"[0-9]+", bruta[campo]):
                erro("tipo", "Esperado inteiro decimal não negativo, sem arredondamento.", numero, campo)
                invalida = True
            else:
                linha[campo] = int(bruta[campo])
        for campo in REAIS:
            try:
                linha[campo] = float(bruta[campo])
                if not math.isfinite(linha[campo]):
                    raise ValueError("Não finito.")
            except ValueError:
                erro("tipo", "Esperado número real finito.", numero, campo)
                invalida = True
        if invalida:
            continue
        if linha["tempo_total_s"] <= 0 or linha["vazao_ops_s"] <= 0:
            erro("dominio", "Tempo e vazão devem ser positivos.", numero)
        if linha["n_cpus"] < 1 or not 0 <= linha["disco_livre_gb"] <= linha["disco_total_gb"] or linha["disco_total_gb"] <= 0:
            erro("dominio", "Quantidade de CPUs ou capacidade de disco inválida.", numero)
        for campo in COLUNAS[15:]:
            if bruta[campo] != str(ambiente.get(campo)):
                erro("ambiente", "Valor difere do ambiente registrado para esta coleta.", numero, campo)
        if linha["tempo_total_s"] > 0 and not math.isclose(
            linha["vazao_ops_s"], linha["n_operacoes"] / linha["tempo_total_s"], rel_tol=1e-12, abs_tol=0,
        ):
            erro("vazao", "M2 difere de n_operacoes/M1.", numero, "vazao_ops_s")
        linhas.append(linha)
    plano = {i: e for i, e in enumerate(plano_execucoes(
        config.N_REPETICOES, config.N_AQUECIMENTO, config.SEMENTE,
    ), 1) if not e.aquecimento}
    chaves = Counter((l["configuracao"], l["carga"], l["repeticao"]) for l in linhas)
    esperado_chaves = Counter((e.configuracao.nome, e.carga.nome, e.repeticao) for e in plano.values())
    if len(linhas_brutas) != len(plano) or chaves != esperado_chaves:
        erro("completude", "Esperadas 360 medições: 30 repetições únicas em cada um dos 12 grupos.")
    if [l["ordem_execucao"] for l in linhas] != list(plano):
        erro("ordem", "Ordem medida deve ser 37–396, sem aquecimentos, duplicatas ou reordenação.")
    for linha in linhas:
        e = plano.get(linha["ordem_execucao"])
        if e is None:
            continue
        campos = {
            "configuracao": e.configuracao.nome, "journal_mode": e.configuracao.journal_mode,
            "synchronous": e.configuracao.synchronous, "carga": e.carga.nome,
            "repeticao": e.repeticao, "semente_carga": e.semente_carga, "semente": config.SEMENTE,
            "n_operacoes": e.carga.n_operacoes,
            "n_leituras": round(e.carga.n_operacoes * e.carga.fracao_leitura),
            "n_escritas": e.carga.n_operacoes - round(e.carga.n_operacoes * e.carga.fracao_leitura),
            "linhas_iniciais": config.LINHAS_INICIAIS, "tamanho_payload": config.TAMANHO_PAYLOAD,
        }
        for campo, valor in campos.items():
            if linha[campo] != valor:
                erro("plano", "Valor difere do plano sorteado; pareamento ou protocolo alterado.", linha["linha_csv"], campo)
    contagens, outliers, temporal = ([], [], []) if erros else diagnosticar(linhas, diretorio.name)
    return {
        "versao_validador": 1, "coleta": diretorio.name,
        "status": "reprovada" if erros else "aprovada",
        "escopo_aprovacao": "Integridade, estrutura e protocolo; não comprova independência temporal ou validade causal.",
        "medicoes_lidas": len(linhas_brutas), "medicoes_esperadas": len(plano),
        "colunas": list(COLUNAS), "erros": erros, "entradas_sha256": hashes,
        "grupos": contagens,
        "outliers": outliers,
        "outliers_observacoes_unicas": len({o["ordem_execucao"] for o in outliers}),
        "metodo_outliers": "Por configuração/carga e métrica M1/M2: fora de [Q1−1,5×IQR; Q3+1,5×IQR], quartis inclusivos; preservação integral, inclusive quando IQR=0.",
        "diagnostico_temporal": temporal,
        "inferencia": "Pendente de auditoria temporal em #309: correlações exploratórias não demonstram nem refutam independência; não usar aprovação estrutural como autorização para conclusões confirmatórias.",
        "observacoes_excluidas": 0,
    }
