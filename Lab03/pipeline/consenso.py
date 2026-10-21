"""Rótulos de consenso da amostra-ouro (#160), aplicados depois do kappa (#159).

Itens unânimes recebem o rótulo comum. Cada item divergente precisa de uma
decisão registrada em `decisoes-consenso.csv`: a maioria simples é só a
proposta discutida, e a decisão final pode ser vazia (item pendente). Os
julgamentos independentes de A, B e C não são alterados.
"""

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

from pipeline.amostra_ouro import ARQUIVO_SORTEIO, PASTA_SAIDA, ROTULADORES
from pipeline.config import ConfigError
from pipeline.kappa import DIMENSOES, _sha256, carregar_rotulos

ARQUIVO_DECISOES = "decisoes-consenso.csv"
COLUNAS_DECISOES = ("dimensao", "repo_id", "release_id", "decisao", "justificativa", "participantes", "data")
ARQUIVO_JSON = "consenso.json"
UNANIME, MAIORIA, DISCUSSAO, PENDENTE = "unanime", "maioria", "discussao", "pendente"


def maioria(votos):
    """Categoria com pelo menos dois votos, ou None quando os três divergem."""
    categoria, quantidade = Counter(votos.values()).most_common(1)[0]
    return categoria if quantidade >= 2 else None


def ler_decisoes(caminho):
    """Decisões por (dimensão, chave); recusa dimensões desconhecidas e itens repetidos."""
    with open(caminho, encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        faltando = set(COLUNAS_DECISOES) - set(leitor.fieldnames or ())
        if faltando:
            raise ConfigError(f"{caminho.name}: colunas ausentes {sorted(faltando)}")
        decisoes = {}
        for numero, linha in enumerate(leitor, start=2):
            dimensao = linha["dimensao"].strip()
            if dimensao not in DIMENSOES:
                raise ConfigError(f"{caminho.name}, linha {numero}: dimensão desconhecida {dimensao!r}")
            colunas_chave = DIMENSOES[dimensao][1]
            chave = tuple(linha[c].strip() for c in colunas_chave)
            if (dimensao, chave) in decisoes:
                raise ConfigError(f"{caminho.name}, linha {numero}: decisão repetida para {dimensao} {chave}")
            decisoes[(dimensao, chave)] = {c: linha[c].strip() for c in COLUNAS_DECISOES[3:]}
    return decisoes


def consolidar(rotulos, decisoes):
    """Rótulo final e origem por dimensão e item, e o registro de cada divergência."""
    finais, divergencias = {}, []
    usadas = set()
    for dimensao, (_, colunas_chave, categorias) in DIMENSOES.items():
        finais[dimensao] = {}
        por_rotulador = rotulos[dimensao]
        for chave in sorted(por_rotulador[ROTULADORES[0]]):
            votos = {r: por_rotulador[r][chave] for r in ROTULADORES}
            if None in votos.values():
                raise ConfigError(f"{dimensao} {chave}: julgamento ausente; o consenso exige as três planilhas completas")
            if len(set(votos.values())) == 1:
                if (dimensao, chave) in decisoes:
                    raise ConfigError(f"{dimensao} {chave}: item unânime não deve ter decisão de consenso")
                finais[dimensao][chave] = (votos[ROTULADORES[0]], UNANIME)
                continue
            if (dimensao, chave) not in decisoes:
                raise ConfigError(f"{dimensao} {chave}: item divergente sem decisão registrada")
            usadas.add((dimensao, chave))
            decisao = decisoes[(dimensao, chave)]
            valor, proposta = decisao["decisao"] or None, maioria(votos)
            if valor is not None and valor not in categorias:
                raise ConfigError(f"{dimensao} {chave}: decisão {valor!r} fora do livro de códigos")
            origem = PENDENTE if valor is None else MAIORIA if valor == proposta else DISCUSSAO
            if origem != MAIORIA and not decisao["justificativa"]:
                raise ConfigError(f"{dimensao} {chave}: decisão {origem} exige justificativa")
            if not decisao["participantes"] or not decisao["data"]:
                raise ConfigError(f"{dimensao} {chave}: registre participantes e data da decisão")
            finais[dimensao][chave] = (valor, origem)
            divergencias.append({"dimensao": dimensao, **dict(zip(colunas_chave, chave)), **votos,
                                 "maioria": proposta, "decisao": valor, "origem": origem, **decisao})
    sobras = set(decisoes) - usadas
    if sobras:
        raise ConfigError(f"{len(sobras)} decisões para itens fora do sorteio ou unânimes: {sorted(sobras)[:3]}")
    return finais, divergencias


def _gravar_csv(caminho, colunas, linhas):
    with open(caminho, "w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, colunas, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)


def executar(pasta=PASTA_SAIDA, decisoes=None, saida=None):
    pasta = Path(pasta)
    saida = Path(saida) if saida else pasta
    decisoes_caminho = Path(decisoes) if decisoes else pasta / ARQUIVO_DECISOES
    rotulos, entradas = carregar_rotulos(pasta)
    entradas[decisoes_caminho.name] = _sha256(decisoes_caminho)
    finais, divergencias = consolidar(rotulos, ler_decisoes(decisoes_caminho))
    manifesto = json.loads((pasta / ARQUIVO_SORTEIO).read_text(encoding="utf-8"))

    linhas_repositorios, linhas_releases = [], []
    for repo in manifesto["repositorios"]:
        chave = (str(repo["repo_id"]),)
        linha = {"repo_id": repo["repo_id"], "full_name": repo["full_name"]}
        for dimensao in ("tipo_projeto", "releases_sao_entregas_reais"):
            valor, origem = finais[dimensao][chave]
            linha |= {dimensao: valor or "", f"origem_{dimensao}": origem}
        linhas_repositorios.append(linha)
        for release in repo["releases"]:
            valor, origem = finais["corretiva"][(str(repo["repo_id"]), str(release["release_id"]))]
            linhas_releases.append({"repo_id": repo["repo_id"], "full_name": repo["full_name"],
                                    "release_id": release["release_id"], "tag_name": release["tag_name"],
                                    "corretiva": valor or "", "origem_corretiva": origem})

    saida.mkdir(parents=True, exist_ok=True)
    _gravar_csv(saida / "consenso_repositorios.csv",
                ["repo_id", "full_name", "tipo_projeto", "origem_tipo_projeto",
                 "releases_sao_entregas_reais", "origem_releases_sao_entregas_reais"], linhas_repositorios)
    _gravar_csv(saida / "consenso_releases.csv",
                ["repo_id", "full_name", "release_id", "tag_name", "corretiva", "origem_corretiva"], linhas_releases)
    resumo = {d: dict(Counter(origem for _, origem in finais[d].values())) for d in DIMENSOES}
    resultado = {"rotuladores": list(ROTULADORES), "entradas_sha256": entradas,
                 "origens": resumo, "divergencias": divergencias}
    (saida / ARQUIVO_JSON).write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return resultado


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pasta", default=PASTA_SAIDA, help="pasta com o manifesto e as planilhas")
    parser.add_argument("--decisoes", help=f"CSV de decisões (padrão: <pasta>/{ARQUIVO_DECISOES})")
    parser.add_argument("--saida", help="pasta dos arquivos de consenso (padrão: --pasta)")
    args = parser.parse_args(argv)
    try:
        resultado = executar(args.pasta, args.decisoes, args.saida)
    except (ConfigError, FileNotFoundError, KeyError) as exc:
        print(f"erro: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    for dimensao, origens in resultado["origens"].items():
        print(dimensao, origens)
    return 0


if __name__ == "__main__":
    sys.exit(main())
