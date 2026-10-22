"""Mudanças de categoria e kappa de Cohen ponderado da RQ07 (#174)."""

import argparse
import csv
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

from pipeline import rq07
from pipeline.classificacao import NOTA

ORDEM = ("Low", "Medium", "High", "Elite")
PARES = tuple(itertools.combinations(rq07.COMBINACOES, 2))
DIMENSOES = ("geral", *(f"classe_{m}" for m in rq07.METRICAS))
COORTES = ("completos_por_par", "completos_nas_tres", "notas_disponiveis", "sem_alertas")
COLUNAS = ("par", "dimensao", "coorte", "total", "n", "excluidos", "mudaram",
           "percentual_mudanca", "kappa_quadratico", "kappa_linear", "motivo_nao_estimavel")


def comparar(a, b):
    """Categorias pareadas na ordem fixa Low < Medium < High < Elite.

    Kappa = 1 - discordância observada / esperada; pesos de discordância
    quadráticos (i-j)^2/9 e lineares abs(i-j)/3. Ausências ficam fora do par.
    """
    a, b = list(a), list(b)
    if len(a) != len(b):
        raise ValueError("Vetores pareados devem ter o mesmo tamanho")
    if any(c is not None and c not in NOTA for c in (*a, *b)):
        raise ValueError("Categoria fora da escala DORA")
    pares = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    n = len(pares)
    matriz = [[0 for _ in ORDEM] for _ in ORDEM]
    for x, y in pares:
        matriz[NOTA[x] - 1][NOTA[y] - 1] += 1
    mudaram = sum(x != y for x, y in pares)
    resultado = {"total": len(a), "n": n, "excluidos": len(a) - n, "mudaram": mudaram,
                 "percentual_mudanca": 100 * mudaram / n if n else None,
                 "ordem_matriz": ORDEM, "matriz_transicao": matriz,
                 "kappa_quadratico": None, "kappa_linear": None,
                 "motivo_nao_estimavel": "nenhum par elegível" if not n else None}
    if not n:
        return resultado
    marg_a, marg_b = Counter(x for x, _ in pares), Counter(y for _, y in pares)
    for potencia, nome in ((2, "kappa_quadratico"), (1, "kappa_linear")):
        def peso(x, y):
            return (abs(NOTA[x] - NOTA[y]) / 3) ** potencia
        observado = sum(peso(x, y) for x, y in pares) / n
        esperado = sum(marg_a[x] * marg_b[y] * peso(x, y) for x in ORDEM for y in ORDEM) / n**2
        if esperado == 0:
            resultado["motivo_nao_estimavel"] = "discordância esperada zero: mesma categoria constante"
        else:
            resultado[nome] = 1 - observado / esperado
    return resultado


def analisar(linhas):
    grupos = {c: {} for c in rq07.COMBINACOES}
    for linha in linhas:
        c, i = linha["combinacao"], linha["id"]
        if c not in grupos or i in grupos[c]:
            raise ValueError("Combinação desconhecida ou ID duplicado")
        grupos[c][i] = linha
    ids = set(grupos["C1"])
    if not ids or any(set(g) != ids for g in grupos.values()):
        raise ValueError("Populações divergentes ou vazias entre combinações")
    resultados = []
    for a, b in PARES:
        for dimensao in DIMENSOES:
            for coorte in COORTES:
                xs, ys = [], []
                for i in sorted(ids):
                    x, y = grupos[a][i], grupos[b][i]
                    elegivel = True
                    if coorte == "completos_nas_tres":
                        elegivel = all(g[i]["completa"] for g in grupos.values())
                    elif coorte in ("completos_por_par", "sem_alertas"):
                        elegivel = x["completa"] and y["completa"]
                    if coorte == "sem_alertas":
                        elegivel = elegivel and not any(r[k] for r in (x, y)
                                                       for k in ("coleta_incompleta", "calculo_parcial"))
                    xs.append(x[dimensao] if elegivel else None)
                    ys.append(y[dimensao] if elegivel else None)
                resultados.append({"par": f"{a}x{b}", "dimensao": dimensao, "coorte": coorte,
                                   **comparar(xs, ys)})
    return resultados


def numero(valor):
    return "não estimável" if valor is None else f"{valor:.4f}"


def relatorio(resultados):
    linhas = ["# RQ07 — Mudança de categoria e robustez (#174)", "",
              "Kappa de Cohen com pesos quadráticos; escala ordinal fixa Low, Medium, High, Elite.",
              "O kappa linear é uma verificação adicional. Matrizes: linhas = primeira combinação;",
              "colunas = segunda. Percentuais usam os pares elegíveis, sem imputar ausências.", "",
              "## Classe geral", "",
              "| Par | Coorte | n | Excluídos | Mudaram | Mudança (%) | Kappa quadrático | Kappa linear |",
              "|---|---|---:|---:|---:|---:|---:|---:|"]
    for r in resultados:
        if r["dimensao"] == "geral":
            linhas.append(f"| {r['par']} | {r['coorte']} | {r['n']} | {r['excluidos']} | {r['mudaram']} | "
                          f"{numero(r['percentual_mudanca'])} | {numero(r['kappa_quadratico'])} | "
                          f"{numero(r['kappa_linear'])} |")
    geral = {(r["par"], r["coorte"]): r for r in resultados if r["dimensao"] == "geral"}
    linhas += ["", "## Resultado observado", ""]
    for a, b in PARES:
        par = f"{a}x{b}"
        principal = geral[par, "completos_por_par"]
        restrito = geral[par, "sem_alertas"]
        linhas += [f"{par}: {principal['mudaram']}/{principal['n']} projetos mudaram de categoria "
                   f"({numero(principal['percentual_mudanca'])}%; kappa quadrático "
                   f"{numero(principal['kappa_quadratico'])}). Sem alertas, a mudança foi "
                   f"{numero(restrito['percentual_mudanca'])}% em {restrito['n']} pares, "
                   f"com kappa {numero(restrito['kappa_quadratico'])}.", ""]
    lt = geral["C1xC2", "completos_nas_tres"]["percentual_mudanca"]
    cfr = geral["C1xC3", "completos_nas_tres"]["percentual_mudanca"]
    if lt is not None and cfr is not None:
        linhas += [f"Na população completa comum, a troca de lead time altera {numero(lt)}% "
                   f"das classes gerais e a de CFR altera {numero(cfr)}%. "
                   "A diferença descreve a sensibilidade destas combinações nesta amostra; "
                   "não atribui superioridade de validade a uma definição.", ""]
    linhas += ["", "## Discussão e limites", "",
               "A análise principal usa quatro métricas disponíveis em ambas as combinações",
               "(completos_por_par). completos_nas_tres fixa a população comum aos três pares.",
               "notas_disponiveis inclui medianas parciais, conforme o protocolo de classificação,",
               "e sem_alertas restringe os pares completos a registros sem coleta incompleta nem",
               "cálculo parcial. As comparações por métrica usam as mesmas coortes; a coorte",
               "notas_disponiveis permite examinar cada métrica em todos os pares observados.", "",
               "C1×C2 isola lead time; C1×C3 isola CFR; C2×C3 altera ambos. A tabela permite",
               "avaliar se a sensibilidade persiste ao fixar disponibilidade e qualidade dos dados.",
               "Mesmo quando o kappa indica proximidade ordinal, o percentual de mudanças mede",
               "quantos projetos efetivamente trocaram de classe; as duas medidas são necessárias.", "",
               "A #162 está encerrada com relatório publicado parcial (146/300). A conferência",
               "das previsões finais locais alcançou 296/300, com quatro indeterminadas;",
               "o registro de suporte está em docs/evidencias/rq07-validacao-final-162.json.",
               "CFR(b) mantém essa limitação: a avaliação não é integral e ausências não viram negativos.",
               "A concordância entre definições não comprova validade das proxies de produção.",
               "Pré-releases e tags estão fora destas combinações, e não se pode generalizar",
               "esta análise para mudanças da definição de deploy. Não há conclusão causal.",
               "Kappa fica nulo se não houver pares ou se a discordância esperada for zero;",
               "uma categoria constante idêntica não recebe artificialmente kappa igual a 1.", ""]
    return "\n".join(linhas)


def executar(dataset=rq07.DATASET, saida=rq07.SAIDA):
    # Reproduz e valida a #173 a partir do CSV/manifesto, evitando resultados obsoletos.
    origem = rq07.executar(dataset, saida)
    saida = Path(saida)
    caminho = saida / "classificacoes.csv"
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo))
    for r in linhas:
        for k in ("completa", "coleta_incompleta", "calculo_parcial"):
            r[k] = rq07.booleano(r[k])
        for k in DIMENSOES:
            r[k] = r[k] or None
    resultados = analisar(linhas)
    resumo = {"issue": 174, "dataset_sha256": origem["dataset_sha256"],
              "classificacoes_sha256": hashlib.sha256(caminho.read_bytes()).hexdigest(),
              "metodo": "Cohen ponderado quadrático (principal) e linear (sensibilidade)",
              "ordem": ORDEM, "resultados": resultados}
    (saida / "robustez.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2) + "\n",
                                       encoding="utf-8", newline="\n")
    rq07.gravar_csv(saida / "robustez.csv", [{k: r[k] for k in COLUNAS} for r in resultados], COLUNAS)
    (saida / "robustez.md").write_text(relatorio(resultados), encoding="utf-8", newline="\n")
    return resumo


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", type=Path, default=rq07.DATASET)
    p.add_argument("--saida", type=Path, default=rq07.SAIDA)
    args = p.parse_args()
    resumo = executar(args.dataset, args.saida)
    print(json.dumps([r for r in resumo["resultados"] if r["dimensao"] == "geral"
                      and r["coorte"] == "completos_por_par"], ensure_ascii=True))


if __name__ == "__main__":
    main()
