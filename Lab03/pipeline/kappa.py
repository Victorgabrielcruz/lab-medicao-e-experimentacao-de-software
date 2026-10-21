"""Kappa de Fleiss entre os rotuladores A, B e C da amostra-ouro (#159).

Lê as planilhas `rotulador_<X>_*.csv` da #155, confere IDs e categorias contra
o manifesto do sorteio e o livro de códigos e calcula, por dimensão, o kappa
de Fleiss nominal só com os itens que têm os três julgamentos. Células vazias
são ausências, nunca uma categoria. Executar antes de qualquer consenso (#160).
"""

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from statsmodels.stats.inter_rater import aggregate_raters, fleiss_kappa

from pipeline.amostra_ouro import ARQUIVO_SORTEIO, PASTA_SAIDA, ROTULADORES
from pipeline.config import ConfigError

SIM_NAO = ("sim", "nao")
CATEGORIAS_TIPO = ("biblioteca", "framework", "aplicacao", "ferramenta_dev", "infraestrutura", "outro")

# dimensão -> (planilha, colunas da chave, categorias do LIVRO-CODIGOS.md)
DIMENSOES = {
    "tipo_projeto": ("repositorios", ("repo_id",), CATEGORIAS_TIPO),
    "releases_sao_entregas_reais": ("repositorios", ("repo_id",), SIM_NAO),
    "corretiva": ("releases", ("repo_id", "release_id"), SIM_NAO),
}

# Landis e Koch (1977): abaixo de zero é pobre; depois, limites superiores inclusivos.
LANDIS_KOCH = ((0.20, "leve"), (0.40, "razoável"), (0.60, "moderada"),
               (0.80, "substancial"), (1.0, "quase perfeita"))

ARQUIVO_JSON = "kappa.json"
ARQUIVO_MD = "kappa.md"


def interpretar(kappa):
    """Faixa de Landis e Koch; kappa negativo é concordância pobre."""
    if kappa is None:
        return None
    if kappa < 0:
        return "pobre"
    for limite, rotulo in LANDIS_KOCH:
        if kappa <= limite:
            return rotulo
    return LANDIS_KOCH[-1][1]


def _sha256(caminho):
    return hashlib.sha256(Path(caminho).read_bytes()).hexdigest()


def chaves_esperadas(manifesto):
    """IDs sorteados, como strings: repo_id e (repo_id, release_id)."""
    repositorios = {(str(r["repo_id"]),) for r in manifesto["repositorios"]}
    releases = {(str(r["repo_id"]), str(rel["release_id"]))
                for r in manifesto["repositorios"] for rel in r["releases"]}
    return {"repositorios": repositorios, "releases": releases}


def ler_planilha(caminho, colunas_chave, dimensoes, esperadas):
    """Rótulos por chave e dimensão; recusa IDs fora do sorteio, duplicados ou categorias inválidas."""
    with open(caminho, encoding="utf-8-sig", newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo))
    rotulos = {dimensao: {} for dimensao in dimensoes}
    vistas = set()
    for numero, linha in enumerate(linhas, start=2):
        chave = tuple(linha[c].strip() for c in colunas_chave)
        if chave in vistas:
            raise ConfigError(f"{caminho.name}, linha {numero}: chave repetida {chave}")
        vistas.add(chave)
        for dimensao, categorias in dimensoes.items():
            valor = linha[dimensao].strip()
            if valor and valor not in categorias:
                raise ConfigError(f"{caminho.name}, linha {numero}: {dimensao}={valor!r} fora do livro de códigos")
            rotulos[dimensao][chave] = valor or None
    if vistas != esperadas:
        raise ConfigError(f"{caminho.name}: {len(esperadas - vistas)} itens do sorteio ausentes e "
                          f"{len(vistas - esperadas)} fora dele")
    return rotulos


def calcular_dimensao(rotulos, categorias):
    """Kappa de Fleiss de uma dimensão; `rotulos` mapeia rotulador -> {chave: categoria ou None}."""
    rotuladores = sorted(rotulos)
    itens = sorted(set().union(*(rotulos[r] for r in rotuladores)))
    completos = [i for i in itens if all(rotulos[r].get(i) for r in rotuladores)]
    resultado = {
        "categorias": list(categorias),
        "itens": len(itens),
        "itens_completos": len(completos),
        "ausentes_por_rotulador": {r: sum(1 for i in itens if not rotulos[r].get(i)) for r in rotuladores},
        "distribuicao_por_rotulador": {
            r: {c: sum(1 for i in completos if rotulos[r][i] == c) for c in categorias} for r in rotuladores},
    }
    distintos = Counter(len({rotulos[r][i] for r in rotuladores}) for i in completos)
    resultado["concordancia_itens"] = {"unanimes": distintos[1], "maioria": distintos[2],
                                       "todos_diferentes": distintos[3]}
    if not completos:
        return resultado | {"kappa": None, "p_observado": None, "p_esperado": None,
                            "interpretacao": None, "motivo_nao_estimavel": "nenhum item com os três julgamentos"}
    indice = {c: n for n, c in enumerate(categorias)}
    matriz = np.array([[indice[rotulos[r][i]] for r in rotuladores] for i in completos])
    tabela, _ = aggregate_raters(matriz, n_cat=len(categorias))
    n = len(rotuladores)
    proporcoes = tabela.sum(axis=0) / tabela.sum()
    p_esperado = float((proporcoes ** 2).sum())
    p_observado = float((((tabela ** 2).sum(axis=1) - n) / (n * (n - 1))).mean())
    resultado |= {"distribuicao": {c: int(tabela[:, k].sum()) for c, k in indice.items()},
                  "p_observado": p_observado, "p_esperado": p_esperado}
    if np.isclose(p_esperado, 1.0):
        return resultado | {"kappa": None, "interpretacao": None,
                            "motivo_nao_estimavel": "todos os julgamentos na mesma categoria (P_e = 1)"}
    kappa = float(fleiss_kappa(tabela, method="fleiss"))
    return resultado | {"kappa": kappa, "interpretacao": interpretar(kappa), "motivo_nao_estimavel": None}


def carregar_rotulos(pasta):
    """Rótulos validados por dimensão e rotulador, e o SHA-256 do manifesto e das planilhas."""
    pasta = Path(pasta)
    manifesto_caminho = pasta / ARQUIVO_SORTEIO
    manifesto = json.loads(manifesto_caminho.read_text(encoding="utf-8"))
    esperadas = chaves_esperadas(manifesto)
    rotulos = {dimensao: {} for dimensao in DIMENSOES}
    entradas = {ARQUIVO_SORTEIO: _sha256(manifesto_caminho)}
    for planilha in ("repositorios", "releases"):
        dimensoes = {d: cats for d, (p, _, cats) in DIMENSOES.items() if p == planilha}
        colunas_chave = next(chave for p, chave, _ in DIMENSOES.values() if p == planilha)
        for rotulador in ROTULADORES:
            caminho = pasta / f"rotulador_{rotulador}_{planilha}.csv"
            entradas[caminho.name] = _sha256(caminho)
            for dimensao, valores in ler_planilha(caminho, colunas_chave, dimensoes, esperadas[planilha]).items():
                rotulos[dimensao][rotulador] = valores
    return rotulos, entradas


def executar(pasta=PASTA_SAIDA, saida=None):
    pasta = Path(pasta)
    saida = Path(saida) if saida else pasta
    rotulos, entradas = carregar_rotulos(pasta)
    dimensoes = {d: calcular_dimensao(rotulos[d], cats) for d, (_, _, cats) in DIMENSOES.items()}
    resultado = {
        "metodo": "fleiss_kappa(method='fleiss') sobre aggregate_raters; categorias nominais",
        "interpretacao": "Landis e Koch (1977)",
        "rotuladores": list(ROTULADORES),
        "completo": all(d["itens_completos"] == d["itens"] for d in dimensoes.values()),
        "entradas_sha256": entradas,
        "dimensoes": dimensoes,
    }
    saida.mkdir(parents=True, exist_ok=True)
    (saida / ARQUIVO_JSON).write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (saida / ARQUIVO_MD).write_text(tabela_markdown(resultado), encoding="utf-8")
    return resultado


def _numero(valor):
    return "—" if valor is None else f"{valor:.3f}".replace(".", ",")


def tabela_markdown(resultado):
    linhas = ["# Kappa de Fleiss da amostra-ouro (#159)", "",
              f"Rotuladores: {', '.join(resultado['rotuladores'])}. Método: {resultado['metodo']}. "
              f"Interpretação: {resultado['interpretacao']}.", ""]
    if not resultado["completo"]:
        linhas += ["**Atenção:** há julgamentos ausentes; cada kappa usa só os itens com os três julgamentos.", ""]
    linhas += ["| Dimensão | Itens completos | Ausentes (A/B/C) | Unânimes | P_o | P_e | Kappa | Interpretação |",
               "|---|---|---|---|---|---|---|---|"]
    for nome, d in resultado["dimensoes"].items():
        ausentes = "/".join(str(v) for v in d["ausentes_por_rotulador"].values())
        interpretacao = d["interpretacao"] or f"não estimável: {d['motivo_nao_estimavel']}"
        linhas.append(f"| `{nome}` | {d['itens_completos']}/{d['itens']} | {ausentes} | "
                      f"{d['concordancia_itens']['unanimes']} | {_numero(d['p_observado'])} | "
                      f"{_numero(d['p_esperado'])} | {_numero(d['kappa'])} | {interpretacao} |")
    return "\n".join(linhas) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pasta", default=PASTA_SAIDA, help="pasta com o manifesto e as planilhas")
    parser.add_argument("--saida", help="pasta de kappa.json e kappa.md (padrão: --pasta)")
    args = parser.parse_args(argv)
    try:
        resultado = executar(args.pasta, args.saida)
    except (ConfigError, FileNotFoundError, KeyError) as exc:
        print(f"erro: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(tabela_markdown(resultado))
    return 0


if __name__ == "__main__":
    sys.exit(main())
