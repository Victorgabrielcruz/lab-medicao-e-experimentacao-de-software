"""Reconstrói somente checkpoints consumidos de uma amostra encerrada, sem API (#153)."""
import argparse
import hashlib
import json
from pathlib import Path
import yaml
from pipeline import auditoria, cfr, compare, consolidado, funil, integrado, lead_time_commit, lead_time_release, metricas, tempo_recuperacao
from pipeline.cache import gravar_json
from pipeline.classificacao import VERSAO_REFERENCIA, classificar_frequencia
from pipeline.config import janela_utc, load_config
from pipeline.dataset_csv import exigir, indice
from pipeline.workflow_runs import _iso

def ler(caminho):
    return json.loads(Path(caminho).read_text(encoding="utf-8-sig"))

def sha(caminho):
    return consolidado.sha256(Path(caminho))

def finalizar_funil(resultado, amostra):
    """O funil legado inclui runs parciais; o recorte oficial exige completude."""
    candidatos = resultado["amostra"]
    excluidos = [r for r in candidatos if r["coleta_runs_incompleta"]]
    incluidos = [r for r in candidatos if not r["coleta_runs_incompleta"]]
    exigir([r["id"] for r in incluidos] == amostra, "Funil nao reproduz amostra oficial")
    resultado["etapas"].append({"etapa": "completude_runs", "descricao": "Coleta completa de runs (amostra oficial)",
        "entrada": len(candidatos), "descartados": len(excluidos), "restantes": len(incluidos),
        "motivos": {"coleta_runs_incompleta": len(excluidos)} if excluidos else {}})
    resultado["descartes"].extend({"id": r["id"], "full_name": r["full_name"],
        "motivo": "coleta_runs_incompleta", "etapa": "completude_runs"} for r in excluidos)
    resultado.update(amostra=incluidos, total_amostra=len(incluidos))
    return resultado

def executar(encerramento, saida):
    autoridade_path = Path(encerramento)
    autoridade_bytes = autoridade_path.read_bytes()
    autoridade = json.loads(autoridade_bytes)
    exigir(autoridade.get("coleta_externa_encerrada") is True and
           autoridade.get("novas_consultas_api_autorizadas") is False, "Encerramento humano ausente")
    snapshot = Path(autoridade["snapshot"])
    saida = Path(saida).resolve()
    exigir(not saida.is_relative_to(snapshot.resolve()) and
           not saida.is_relative_to(Path(autoridade["origem"]).resolve()), "Saida invade entrada protegida")
    exigir(not saida.exists(), "Saida ja existe: reutilize o resultado ou escolha outra pasta isolada")
    hashes = autoridade["arquivos_sha256"]
    def verificado(relativo):
        caminho = snapshot / relativo
        conteudo = caminho.read_bytes()
        exigir(hashlib.sha256(conteudo).hexdigest() == hashes.get(relativo), f"Hash divergente: {relativo}")
        registro = json.loads(conteudo)
        exigir(sha(caminho) == hashes[relativo], f"Entrada em mutacao: {relativo}")
        return registro
    progresso = verificado("progresso.json")
    exigir(progresso["contexto"] == autoridade["contexto"], "Contexto divergente")
    contexto = autoridade["contexto"]
    digest = hashlib.sha256(json.dumps(contexto, sort_keys=True).encode()).hexdigest()
    exigir(digest == autoridade["contexto_sha256"], "Hash do contexto divergente")
    ids = progresso["ids_avaliados"]
    amostra = autoridade["ids_amostra"]
    exigir(len(ids) == len(set(ids)) == autoridade["candidatos_avaliados"], "IDs consumidos divergentes")
    exigir(len(amostra) == len(set(amostra)) == autoridade["total_amostra"], "Populacao duplicada/divergente")
    exigir(set(amostra) <= set(ids), "Amostra nao consumida")
    exigir(sha(snapshot / "config.yaml") == hashes["config.yaml"], "Config modificada")
    config = load_config(snapshot / "config.yaml")
    inicio, fim = janela_utc(config)
    janela = {"inicio": _iso(inicio), "fim_exclusivo": _iso(fim)}
    exigir(janela == contexto["janela"], "Janela divergente")
    raw, processed = saida / "raw", saida / "processed"
    raw.mkdir(parents=True)
    processed.mkdir()
    config["caminhos"] = {"raw": str(raw), "processed": str(processed), "cache": str(saida / "cache-nao-utilizado")}
    (saida / "config.yaml").write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")
    dados = {nome: {"janela": janela, "repositorios": [], "descartes": []} for nome, *_ in integrado.ETAPAS}
    dados["candidatos"] = {"candidatos": []}
    elegiveis, utilizados = [], []
    def reconstruir():
        for pos, i in enumerate(ids, 1):
            rel = f"checkpoints/{digest}/{i}.json"
            cp = verificado(rel)
            utilizados.append(rel)
            exigir(cp["candidato"]["id"] == i, "ID do checkpoint divergente")
            dados["candidatos"]["candidatos"].append(cp["candidato"])
            for etapa, valor in cp["aprovados"].items():
                exigir(integrado._identidade(cp["candidato"], valor), "Identidade divergente no checkpoint")
                dados[etapa]["repositorios"].append(integrado._sem_runs(valor, inicio, fim)
                                                  if etapa == "workflow_runs" else valor)
            for etapa, valor in cp["descartes"].items():
                dados[etapa]["descartes"].append(valor)
            if cp["elegivel"]:
                exigir(not cp["aprovados"]["metadados"].get("contribuidores_pendentes"), "Metadados intermediarios")
                elegiveis.append(i)
            if "workflow_runs" in cp["aprovados"]:
                yield cp["aprovados"]["workflow_runs"]
            if pos % 50 == 0:
                print(f"Checkpoints offline: {pos}/{len(ids)}", flush=True)
    consolidado.gravar(raw / "workflow_runs.json", {"janela": janela}, reconstruir())
    exigir(elegiveis == amostra, "Elegiveis reconstruidos diferem da autoridade")
    for nome, _, arquivo, _ in integrado.ETAPAS:
        if nome != "workflow_runs":
            gravar_json(raw / arquivo, dados[nome])
    filtro = set(amostra)
    entrada = raw / "amostra_workflow_runs.json"
    consolidado.gravar(entrada, {"janela": janela},
                      (r for r in consolidado.repositorios(raw / "workflow_runs.json") if r["id"] in filtro))
    resultado_funil = finalizar_funil(funil.montar_funil(dados, config, integrado.ETAPAS), amostra)
    gravar_json(processed / "funil.json", resultado_funil)
    (processed / "funil.md").write_text(funil.tabela_markdown(resultado_funil), encoding="utf-8")
    print("Calculando CFR(a) e recuperacao a partir dos runs locais", flush=True)
    cfr.executar(config, entrada)
    tempo_recuperacao.executar(config, entrada)
    validacao = auditoria.validar(config, entrada, processed / "cfr.json", processed / "tempo_recuperacao.json")
    gravar_json(processed / "auditoria.json", validacao)
    rels = indice(dados["releases"]["repositorios"])
    frequencias, comparacoes, faltantes = [], [], []
    for i in amostra:
        r = rels[i]
        n = funil.contar_releases(r, inicio, fim, config["inclusao"].get("incluir_prereleases", True))["releases_publicadas"]
        valor, classe = classificar_frequencia(n, inicio, fim)
        frequencias.append({"id": i, "full_name": r["full_name"], "releases_ano": n, "releases_janela": n,
                            "deployment_frequency": valor, "classe": classe})
        contexto_compare = {"releases": r, "janela": janela, "api": contexto["api"], "versao_compare": 1}
        digest_compare = hashlib.sha256(json.dumps(contexto_compare, sort_keys=True).encode()).hexdigest()
        relativo = f"checkpoints/compare/{digest_compare}/{i}.json"
        if relativo in hashes:
            cp = verificado(relativo)
            exigir(integrado._identidade(r, cp), "Compare com identidade divergente")
            comparacoes.append(cp)
            utilizados.append(relativo)
        else:
            faltantes.append(i)
    compare.gravar_consolidado(config, comparacoes, inicio, fim)
    lead_time_release.executar(config)
    lead_time_commit.executar(config)
    audit_lt = auditoria.validar_lead_time(config, raw / "compare.json", processed / "lead_time_release.json")
    audit_lt.update(validado=True, populacao_csv=len(amostra), repositorios_sem_compare=len(faltantes),
                    ids_sem_compare=faltantes, cobertura_compare_completa=not faltantes)
    gravar_json(processed / "auditoria_lead_time.json", audit_lt)
    gravar_json(processed / "deployment_frequency.json", {"janela": janela, "versao_classificacao": VERSAO_REFERENCIA,
                "unidade": "releases_por_semana", "semanas_janela": (fim-inicio).total_seconds()/604800,
                "incluir_prereleases": False, "repositorios": frequencias})
    caminho_metricas, _, _ = metricas.executar(config)
    documento = ler(caminho_metricas)
    # A ausencia de compare nao e um compare vazio/coletado. Marca a uniao final
    # e mantem os arquivos de lead time somente com compares efetivamente presentes.
    for r in documento["repositorios"]:
        if r["id"] in faltantes:
            exigir(r["lead_time_a"] is None and r["lead_time_b"] is None, "Lead time sem compare")
            r.update(coleta_incompleta=True, calculo_parcial=True, compare_ausente_no_encerramento=True)
    documento["repositorios_com_coleta_incompleta"] = sum(r["coleta_incompleta"] for r in documento["repositorios"])
    documento["repositorios_com_calculo_parcial"] = sum(r["calculo_parcial"] for r in documento["repositorios"])
    documento["politica_incompletude"] = "Compare ausente no encerramento marca coleta_incompleta e calculo_parcial; nao sintetiza compare."
    gravar_json(caminho_metricas, documento)
    # Instantes de processamento nao alteram a identidade de uma reproducao offline.
    for arquivo in [raw / "compare.json", *processed.glob("*.json")]:
        d = ler(arquivo)
        if "gerado_em" in d:
            d["gerado_em"] = autoridade["encerrado_utc"]
            gravar_json(arquivo, d)
    exigir(autoridade_path.read_bytes() == autoridade_bytes, "Autoridade modificada durante leitura")
    for rel in utilizados:
        exigir(sha(snapshot / rel) == hashes[rel], f"Snapshot mudou: {rel}")
    execucao = {"contexto": contexto, "total_amostra_completa": len(amostra), "candidatos_avaliados": len(ids),
                "alvo_original": autoridade["meta_original"], "minimo_original": autoridade["minimo_original"],
                "execucao_completa": False, "consolidacao_offline_completa": True,
                "excecao_humana": autoridade["decisao"], "encerrado_utc": autoridade["encerrado_utc"],
                "novas_consultas_api": 0, "raw": str(raw), "processed": str(processed),
                "repositorios_com_compare_local": len(comparacoes), "repositorios_sem_compare": len(faltantes),
                "dependencias_pendentes": ["CFR(b) #161", "Compare nao coletado para IDs indicados na auditoria"],
                "ids_amostra_sha256": hashlib.sha256(json.dumps(amostra).encode()).hexdigest(),
                "autoridade_sha256": hashlib.sha256(autoridade_bytes).hexdigest(),
                "entradas_sha256": {rel: hashes[rel] for rel in utilizados}}
    gravar_json(processed / "execucao.json", execucao)
    print(json.dumps({k: v for k, v in execucao.items() if k not in ("entradas_sha256", "contexto")}, ensure_ascii=True), flush=True)
    return execucao

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--encerramento", required=True)
    p.add_argument("--saida-dados", required=True)
    args = p.parse_args()
    executar(args.encerramento, args.saida_dados)

if __name__ == "__main__":
    main()
