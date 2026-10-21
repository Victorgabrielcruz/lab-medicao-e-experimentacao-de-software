"""Avalia releases corretivas da #161 contra o consenso da #160, sem rede (#162)."""

import argparse
import csv
import io
import json
import platform
import sys
import tempfile
from collections import Counter
from pathlib import Path

import sklearn
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support

from pipeline import cfr_b, consolidado
from pipeline.amostra_ouro import PASTA_SAIDA, _data
from pipeline.cache import gravar_json, substituir_atomico
from pipeline.config import ConfigError

SAIDA = "validacao/avaliacao-heuristica/v1"
ARQUIVOS = ("avaliacao.json", "avaliacao.md", "pares.csv", "previsoes_amostra.json", "pendencias.csv")
COLUNAS_PARES = ("repo_id", "full_name", "release_id", "tag_name", "published_at",
                 "consenso", "origem_consenso", "previsao", "motivo_previsao",
                 "resultado", "motivos_exclusao")
COLUNAS_PENDENCIAS = ("repo_id", "full_name", "release_id", "tag_name", "published_at",
                      "compare_url", "tipo_pendencia", "motivos_exclusao", "acao_recomendada")


def exigir(condicao, mensagem):
    if not condicao:
        raise ConfigError(mensagem)


def identificador(valor):
    exigir(type(valor) in (str, int) and str(valor).strip().isdecimal(), f"ID inválido: {valor!r}")
    exigir(int(valor) > 0, f"ID inválido: {valor!r}")
    return str(int(valor))


def janela(dados):
    exigir(isinstance(dados, dict), "Entrada JSON deve ser um objeto com janela.")
    j = dados.get("janela")
    exigir(isinstance(j, dict), "Cabeçalho sem janela de observação.")
    inicio, fim = _data(j.get("inicio")), _data(j.get("fim_exclusivo"))
    exigir(inicio is not None and fim is not None and inicio < fim, "Janela inválida.")
    return inicio, fim


def carregar_amostra(caminho):
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    inicio, fim = janela(dados)
    exigir(dados.get("incluir_prereleases") is False, "A heurística v1 exige releases estáveis.")
    repositorios = dados.get("repositorios")
    exigir(isinstance(repositorios, list) and repositorios, "Manifesto sem repositórios.")
    esperadas, ids = {}, set()
    for repo in repositorios:
        i = identificador(repo.get("repo_id"))
        exigir(i not in ids, f"Repositório repetido no manifesto: {i}")
        ids.add(i)
        exigir(isinstance(repo.get("full_name"), str) and repo["full_name"].strip(), "Nome de repositório ausente.")
        exigir(isinstance(repo.get("releases"), list) and repo["releases"], f"Repositório {i} sem releases.")
        for rel in repo["releases"]:
            chave = i, identificador(rel.get("release_id"))
            data = _data(rel.get("published_at"))
            exigir(chave not in esperadas, f"Release repetida no manifesto: {chave}")
            exigir(isinstance(rel.get("tag_name"), str) and rel["tag_name"].strip(), "Tag ausente no manifesto.")
            exigir(data is not None and inicio <= data < fim, f"Release fora da janela: {chave}")
            esperadas[chave] = {"repo_id": i, "full_name": repo["full_name"], "release_id": chave[1],
                                "tag_name": rel["tag_name"], "published_at": rel["published_at"]}
    exigir(dados.get("total_repositorios") == len(ids) and dados.get("total_releases") == len(esperadas),
           "Contagens do manifesto divergem dos itens.")
    exigir(all(len(r["releases"]) == dados.get("releases_por_repositorio") for r in repositorios),
           "Quantidade de releases por repositório divergente no manifesto.")
    return dados, esperadas


def conferir_identidade(item, esperado, contexto, data=False):
    exigir(isinstance(item.get("full_name"), str) and item["full_name"].casefold() == esperado["full_name"].casefold(),
           f"Nome divergente em {contexto}: {esperado['repo_id']}")
    exigir(item.get("tag_name") == esperado["tag_name"], f"Tag divergente em {contexto}: {esperado['release_id']}")
    if data:
        exigir(_data(item.get("published_at")) == _data(esperado["published_at"]),
               f"Data divergente em {contexto}: {esperado['release_id']}")


def carregar_consenso(caminho, esperadas):
    """Só aceita o contrato de consenso, nunca a planilha de um rotulador como substituta."""
    with Path(caminho).open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        obrigatorias = {"repo_id", "release_id", "full_name", "tag_name", "corretiva", "origem_corretiva"}
        exigir(obrigatorias <= set(leitor.fieldnames or ()), "Consenso: colunas obrigatórias ausentes.")
        exigir(len(leitor.fieldnames) == len(set(leitor.fieldnames)), "Consenso: cabeçalhos repetidos.")
        resultado = {}
        for n, linha in enumerate(leitor, 2):
            exigir(None not in linha and all(v is not None for v in linha.values()), f"Consenso: linha {n} malformada.")
            linha = {k: v.strip() for k, v in linha.items()}
            chave = identificador(linha["repo_id"]), identificador(linha["release_id"])
            exigir(chave in esperadas, f"Consenso contém item fora da amostra: {chave}")
            exigir(chave not in resultado, f"Consenso contém chave repetida: {chave}")
            conferir_identidade(linha, esperadas[chave], "consenso")
            valor, origem = linha["corretiva"], linha["origem_corretiva"]
            exigir(origem in {"unanime", "maioria", "discussao", "pendente"}, "Origem do consenso inválida.")
            exigir((valor in {"sim", "nao"} and origem != "pendente") or (valor == "" and origem == "pendente"),
                   f"Rótulo/origem de consenso inválidos: {chave}")
            resultado[chave] = (valor or None, origem)
    return resultado


def selecionar_previsoes(repositorios, esperadas):
    selecionadas, vistos = {}, set()
    ids = {i for i, _ in esperadas}
    for repo in repositorios:
        i = identificador(repo.get("id"))
        exigir(i not in vistos, f"Repositório repetido nas previsões: {i}")
        vistos.add(i)
        if i not in ids:
            continue
        exigir(isinstance(repo.get("releases"), list), f"Previsões sem detalhes por release: {i}")
        releases_vistas = set()
        for rel in repo["releases"]:
            chave = i, identificador(rel.get("release_id"))
            exigir(chave not in releases_vistas, f"Previsão repetida: {chave}")
            releases_vistas.add(chave)
            if chave not in esperadas:
                continue
            conferir_identidade(rel | {"full_name": repo.get("full_name")}, esperadas[chave], "previsões", True)
            exigir("corretiva" in rel and (type(rel["corretiva"]) is bool or rel["corretiva"] is None),
                   f"Previsão corretiva deve ser bool ou null: {chave}")
            # A decisão já foi calculada com todas as mensagens. O recorte mantém
            # contagem e exemplos dos sinais; a entrada integral fica vinculada por hash.
            detalhe = dict(rel)
            if "commits_corretivos" in detalhe:
                sinais = detalhe.pop("commits_corretivos")
                exigir(isinstance(sinais, list), f"Sinais de commits devem ser uma lista: {chave}")
                detalhe["total_commits_corretivos"] = len(sinais)
                detalhe["exemplos_commits_corretivos"] = sinais[:5]
            selecionadas[chave] = detalhe
    return selecionadas


def prever_entradas(releases, compares, manifesto, esperadas):
    """Reaplica a #161 à sequência completa, antes de selecionar as cinco releases sorteadas."""
    ids = {i for i, _ in esperadas}
    exigir(janela(consolidado.cabecalho(releases)) == janela(manifesto), "Janela divergente nas releases.")
    if compares is not None:
        cabecalho = consolidado.cabecalho(compares)
        exigir(janela(cabecalho) == janela(manifesto), "Janela divergente nos compares.")
        exigir(cabecalho.get("definicao_deploy") == "release_estavel", "Compare deve usar release_estavel.")
    fontes, vistos = {}, set()
    for repo in consolidado.repositorios(releases):
        i = identificador(repo.get("id"))
        exigir(i not in vistos, f"Repositório repetido nas releases: {i}")
        vistos.add(i)
        if i in ids:
            fontes[i] = repo
    exigir(ids <= fontes.keys(), "Repositório da amostra ausente nas releases.")
    calculados, vistos = {}, set()
    if compares is not None:
        for cp in consolidado.repositorios(compares):
            i = identificador(cp.get("id"))
            exigir(i not in vistos, f"Repositório repetido no compare: {i}")
            vistos.add(i)
            if i in fontes:
                calculados[i] = cfr_b.calcular_repositorio(fontes[i], *janela(manifesto), cp)
    for i, repo in fontes.items():
        if i not in calculados:
            calculados[i] = cfr_b.calcular_repositorio(repo, *janela(manifesto))
    return selecionar_previsoes(calculados.values(), esperadas)


def calcular_metricas(verdade, previsao):
    """Classe positiva sim; denominador nulo é None, zero observado continua zero."""
    exigir(len(verdade) == len(previsao), "Vetores de tamanhos diferentes.")
    exigir(all(type(v) is bool for v in [*verdade, *previsao]), "Métricas exigem vetores booleanos completos.")
    if verdade:
        vn, fp, fn, vp = map(int, confusion_matrix(verdade, previsao, labels=[False, True]).ravel())
        p, r, f, _ = precision_recall_fscore_support(
            verdade, previsao, labels=[False, True], average=None, zero_division=0)
        precisao = float(p[1]) if vp + fp else None
        recall = float(r[1]) if vp + fn else None
        f1 = float(f[1]) if 2 * vp + fp + fn else None
    else:
        vn = fp = fn = vp = 0
        precisao = recall = f1 = None
    return {"matriz_confusao": {"linhas_consenso": ["nao", "sim"], "colunas_previsao": ["nao", "sim"],
                                "valores": [[vn, fp], [fn, vp]], "VP": vp, "FP": fp, "FN": fn, "VN": vn},
            "precisao": precisao, "recall": recall, "f1": f1,
            "suporte_positivo": vp + fn, "suporte_negativo": vn + fp,
            "previsoes_positivas": vp + fp, "previsoes_negativas": vn + fn,
            "denominadores": {"precisao": vp + fp, "recall": vp + fn, "f1": 2 * vp + fp + fn}}


def avaliar(esperadas, consenso, previsoes):
    pares, verdade, estimado = [], [], []
    for chave, item in esperadas.items():
        rotulo, origem = consenso.get(chave, (None, None))
        p = previsoes.get(chave)
        v = p["corretiva"] if p else None
        motivos = []
        if rotulo is None:
            motivos.append("consenso_ausente")
        if p is None:
            motivos.append("previsao_ausente")
        elif v is None:
            motivos.append("previsao_indeterminada")
        resultado = None
        if not motivos:
            y = rotulo == "sim"
            verdade.append(y)
            estimado.append(v)
            resultado = ("VP" if y else "FP") if v else ("FN" if y else "VN")
        pares.append(item | {"consenso": rotulo, "origem_consenso": origem, "previsao": v,
                             "motivo_previsao": p.get("motivo_corretiva") if p else None,
                             "resultado": resultado, "motivos_exclusao": motivos})
    metricas = calcular_metricas(verdade, estimado)
    motivos = Counter(m for p in pares for m in p["motivos_exclusao"])
    cobertura = {"total_amostra": len(pares), "avaliadas": len(verdade), "excluidas": len(pares) - len(verdade),
                 "fracao_avaliada": len(verdade) / len(pares), "motivos_exclusao": dict(sorted(motivos.items())),
                 "consenso_positivo_total": sum(p["consenso"] == "sim" for p in pares),
                 "consenso_negativo_total": sum(p["consenso"] == "nao" for p in pares)}
    cobertura["consenso_positivo_excluido"] = cobertura["consenso_positivo_total"] - metricas["suporte_positivo"]
    cobertura["consenso_negativo_excluido"] = cobertura["consenso_negativo_total"] - metricas["suporte_negativo"]
    return {"classe_positiva": "sim", "avaliacao_completa": len(verdade) == len(pares),
            "cobertura": cobertura, **metricas, "limiar_f1": 0.70,
            "atinge_limiar_no_subconjunto": metricas["f1"] >= .70 if metricas["f1"] is not None else None,
            "pares": pares}


def diagnosticar_pendencias(pares, previsoes, manifesto):
    """Explica lacunas sem usar o consenso para alterar as previsões da heurística."""
    urls = {(identificador(r["repo_id"]), identificador(rel["release_id"])): rel.get("compare_url")
            for r in manifesto["repositorios"] for rel in r["releases"]}
    pendencias = []
    for par in pares:
        if not par["motivos_exclusao"]:
            continue
        chave = par["repo_id"], par["release_id"]
        previsao = previsoes.get(chave)
        tipos, acoes = [], []
        if "consenso_ausente" in par["motivos_exclusao"]:
            tipos.append("consenso")
            acoes.append("Concluir o rótulo de consenso da #160.")
        if previsao is None:
            tipos.append("previsao")
            acoes.append("Exportar a previsão por release da #161 para este par de IDs.")
        elif previsao["corretiva"] is None:
            if "patch_semver" in previsao and previsao["patch_semver"] is None:
                tipos.append("predecessora_historica")
                acoes.append("Confirmar a predecessora anterior à janela, quando existir; ausência legítima permanece indeterminada na v1.")
            if "compare_completo" in previsao and previsao["compare_completo"] is not True:
                tipos.append("commits_compare")
                acoes.append("Disponibilizar mensagens e contagens do compare completo ou registrar sua indisponibilidade.")
            if not any(t in tipos for t in ("predecessora_historica", "commits_compare")):
                tipos.append("evidencias_previsao")
                acoes.append("Recalcular ou exportar as evidências de patch e compare da versão da heurística utilizada.")
        pendencias.append({k: par[k] for k in COLUNAS_PENDENCIAS[:5]} |
                          {"compare_url": urls[chave], "tipo_pendencia": "+".join(tipos),
                           "motivos_exclusao": ";".join(par["motivos_exclusao"]),
                           "acao_recomendada": " ".join(acoes)})
    return pendencias


def tabela_markdown(dados):
    def numero(v):
        return "não estimável" if v is None else f"{v:.6f}"
    m, c = dados["matriz_confusao"], dados["cobertura"]
    return ("# Avaliação da heurística corretiva — #162\n\n"
            f"Versão: `{dados['versao_heuristica']}`. Classe positiva: **sim**.\n\n"
            f"**{'Completa' if dados['avaliacao_completa'] else 'Parcial'}:** {c['avaliadas']}/{c['total_amostra']} "
            f"releases avaliadas; {c['excluidas']} excluídas.\n\n"
            "| Consenso / previsão | nao | sim |\n|---|---:|---:|\n"
            f"| nao | {m['VN']} (VN) | {m['FP']} (FP) |\n| sim | {m['FN']} (FN) | {m['VP']} (VP) |\n\n"
            "| Métrica | Valor |\n|---|---:|\n"
            f"| Precisão | {numero(dados['precisao'])} |\n| Recall | {numero(dados['recall'])} |\n"
            f"| F1 | {numero(dados['f1'])} |\n| Suporte positivo avaliado | {dados['suporte_positivo']} |\n"
            f"| Suporte negativo avaliado | {dados['suporte_negativo']} |\n\n"
            f"No consenso total há {c['consenso_positivo_total']} corretivas e {c['consenso_negativo_total']} não corretivas; "
            f"ficaram fora do cálculo {c['consenso_positivo_excluido']} corretivas e "
            f"{c['consenso_negativo_excluido']} não corretivas.\n\n"
            f"Exclusões por motivo (podem se sobrepor): `{json.dumps(c['motivos_exclusao'], ensure_ascii=False)}`.\n\n"
            f"Diagnóstico das pendências: `{json.dumps(c['pendencias_por_tipo'], ensure_ascii=False)}`. "
            "Os IDs, URLs oficiais de compare e ações recomendadas estão em `pendencias.csv`. "
            "Uma URL vazia indica que o sorteio não fornece compare para a primeira release elegível; "
            "ela não comprova ausência de predecessora fora da janela.\n\n"
            "Ausências não viram negativos. Valores com denominador nulo são não estimáveis. "
            "A censura de sete dias pertence à falha da CFR(b); esta avaliação usa `corretiva`, "
            "inclusive nas releases censuradas para CFR. Os pares e as exclusões estão em `pares.csv`.\n\n"
            "O limiar de F1 é 0,70 (#163). Um resultado parcial descreve somente o subconjunto "
            "avaliado, sujeito a viés de cobertura, e não confirma a meta para toda a amostra. "
            "Este comando não refina a heurística nem altera os rótulos de consenso.\n")


def gravar_texto(caminho, texto):
    temporario = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=caminho.parent,
                                         suffix=".tmp", delete=False) as arquivo:
            temporario = Path(arquivo.name)
            arquivo.write(texto)
        substituir_atomico(temporario, caminho)
    finally:
        if temporario is not None:
            temporario.unlink(missing_ok=True)


def executar(previsoes=None, *, releases=None, compares=None, pasta=PASTA_SAIDA, saida=SAIDA):
    exigir((previsoes is None) != (releases is None), "Use exatamente um de --previsoes ou --releases.")
    exigir(compares is None or releases is not None, "--compare exige --releases.")
    pasta, saida = Path(pasta), Path(saida)
    entradas = {"amostra": pasta / "amostra_ouro.json", "consenso": pasta / "consenso_releases.csv"}
    entradas.update({k: Path(v) for k, v in {"previsoes": previsoes, "releases": releases, "compare": compares}.items()
                     if v is not None})
    exigir(not any((saida / n).resolve() in {p.resolve() for p in entradas.values()} for n in ARQUIVOS),
           "Saída não pode sobrescrever entradas.")
    hashes = {k: consolidado.sha256(p) for k, p in entradas.items()}
    manifesto, esperadas = carregar_amostra(entradas["amostra"])
    consenso = carregar_consenso(entradas["consenso"], esperadas)
    if previsoes is not None:
        cabecalho = consolidado.cabecalho(previsoes)
        exigir(janela(cabecalho) == janela(manifesto), "Janela divergente nas previsões.")
        exigir(cabecalho.get("variante") == "b", "Previsões devem usar variante=b da CFR.")
        versao = cabecalho.get("versao_heuristica")
        exigir(isinstance(versao, str) and versao.strip(), "Versão da heurística ausente nas previsões.")
        selecionadas = selecionar_previsoes(consolidado.repositorios(previsoes), esperadas)
    else:
        selecionadas = prever_entradas(releases, compares, manifesto, esperadas)
        versao = cfr_b.VERSAO_HEURISTICA
    dados = avaliar(esperadas, consenso, selecionadas)
    pendencias = diagnosticar_pendencias(dados["pares"], selecionadas, manifesto)
    dados["cobertura"]["pendencias_por_tipo"] = dict(sorted(Counter(p["tipo_pendencia"] for p in pendencias).items()))
    dados.update(versao_avaliador=2, versao_heuristica=versao,
                 bibliotecas={"python": platform.python_version(), "scikit-learn": sklearn.__version__},
                 metodo="precision_recall_fscore_support e confusion_matrix; labels=[nao,sim]; sem média entre repositórios",
                 entradas={k: {"arquivo": str(p), "sha256": hashes[k]} for k, p in entradas.items()})
    exigir(all(consolidado.sha256(p) == hashes[k] for k, p in entradas.items()), "Entrada mudou durante a avaliação.")
    repositorios = {}
    for (i, _), rel in selecionadas.items():
        repositorios.setdefault(i, {"id": int(i), "full_name": esperadas[(i, identificador(rel['release_id']))]["full_name"],
                                   "releases": []})["releases"].append(rel)
    filtradas = {"janela": manifesto["janela"], "variante": "b", "versao_heuristica": versao,
                 "origens_avaliacao": dados["entradas"], "repositorios": list(repositorios.values())}
    texto = io.StringIO(newline="")
    escritor = csv.DictWriter(texto, fieldnames=COLUNAS_PARES, lineterminator="\n")
    escritor.writeheader()
    for par in dados["pares"]:
        escritor.writerow(par | {"previsao": "sim" if par["previsao"] is True else "nao" if par["previsao"] is False else "",
                                  "motivos_exclusao": ";".join(par["motivos_exclusao"])})
    saida.mkdir(parents=True, exist_ok=True)
    gravar_json(saida / ARQUIVOS[0], dados)
    gravar_texto(saida / ARQUIVOS[1], tabela_markdown(dados))
    gravar_texto(saida / ARQUIVOS[2], texto.getvalue())
    gravar_json(saida / ARQUIVOS[3], filtradas)
    texto_pendencias = io.StringIO(newline="")
    escritor = csv.DictWriter(texto_pendencias, fieldnames=COLUNAS_PENDENCIAS, lineterminator="\n")
    escritor.writeheader()
    escritor.writerows(pendencias)
    gravar_texto(saida / ARQUIVOS[4], texto_pendencias.getvalue())
    return dados


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    fonte = parser.add_mutually_exclusive_group(required=True)
    fonte.add_argument("--previsoes", help="cfr_b.json com detalhes por release")
    fonte.add_argument("--releases", help="releases.json completo, antes de selecionar as cinco sorteadas")
    parser.add_argument("--compare", help="compare.json; sem ele só são conhecidas decisões com evidência suficiente")
    parser.add_argument("--pasta", default=PASTA_SAIDA, help="Pasta do manifesto e consenso da #160")
    parser.add_argument("--saida", default=SAIDA, help="Pasta dos cinco artefatos de avaliação")
    parser.add_argument("--exigir-completa", action="store_true", help="Retorna 3, preservando o relatório, se a cobertura for parcial")
    args = parser.parse_args(argv)
    try:
        dados = executar(args.previsoes, releases=args.releases, compares=args.compare, pasta=args.pasta, saida=args.saida)
    except (ConfigError, OSError, ValueError, KeyError, TypeError, csv.Error) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    c = dados["cobertura"]
    print(f"Avaliação {'completa' if dados['avaliacao_completa'] else 'parcial'}: "
          f"{c['avaliadas']}/{c['total_amostra']} releases; precisão={dados['precisao']}, "
          f"recall={dados['recall']}, F1={dados['f1']} -> {args.saida}")
    return 3 if args.exigir_completa and not dados["avaliacao_completa"] else 0


if __name__ == "__main__":
    sys.exit(main())
