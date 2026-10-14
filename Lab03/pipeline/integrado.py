"""Um comando seleciona, coleta e calcula até N repositórios elegíveis (#149)."""
import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path
import requests
from pipeline import actions, auditoria, candidatos, cfr, compare, funil, lead_time_commit, lead_time_release, metadados, metricas, releases, tempo_recuperacao
from pipeline import workflow_runs_completos as completos
from pipeline.cache import CacheDisco, gravar_json
from pipeline.classificacao import VERSAO_REFERENCIA, classificar_frequencia
from pipeline.config import ConfigError, janela_utc, load_config, read_token
from pipeline.github_api import GitHubClient
from pipeline.workflow_runs import _iso

log = logging.getLogger(__name__)
ETAPAS = (funil.ETAPAS[0], funil.ETAPAS[1], funil.ETAPAS[2], funil.ETAPAS[4], funil.ETAPAS[3])


def _ler(caminho):
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def _identidade(a, b):
    return a["id"] == b["id"] and a["full_name"].lower() == b["full_name"].lower()


def _coletar_compares(config, client, rels, inicio, fim):
    """Coleta somente a amostra elegível e retoma cada repositório separadamente."""
    raw = Path(config["caminhos"]["raw"])
    lista = []
    for repo in rels:
        contexto = {"releases": repo, "janela": {"inicio": _iso(inicio), "fim_exclusivo": _iso(fim)},
                    "api": config["api"]["base_url"], "versao_compare": 1}
        digest = hashlib.sha256(json.dumps(contexto, sort_keys=True).encode()).hexdigest()
        caminho = raw / "checkpoints" / "compare" / digest / f"{repo['id']}.json"
        if caminho.is_file():
            registro = _ler(caminho)
        else:
            registro = compare.coletar_repositorio(client, repo, inicio, fim)
            gravar_json(caminho, registro)
        if not _identidade(registro, repo):
            raise ConfigError("Identidade divergente no checkpoint de compare")
        lista.append(registro)
        log.info("Compare integrado: %d/%d repositórios; %d releases ignoradas",
                 len(lista), len(rels), registro["total_releases_ignoradas"])
    compare.gravar_consolidado(config, lista, inicio, fim)
    return lista


def executar(config, client, alvo=100, max_candidatos=1000, fonte=None, reutilizar_runs=None):
    if alvo < 1 or max_candidatos < alvo:
        raise ConfigError("alvo positivo e max_candidatos >= alvo são obrigatórios")
    if config["runs"].get("evento") != "push" or config["runs"].get("somente_default_branch") is not True:
        raise ConfigError("A integração exige evento push e somente default branch")
    raw, processed = (Path(config["caminhos"][k]) for k in ("raw", "processed"))
    if raw.resolve() == processed.resolve():
        raise ConfigError("raw e processed devem ser diferentes")
    destino_candidatos = raw / candidatos.ARQUIVO_SAIDA
    if fonte is not None:
        fonte = Path(fonte)
        if not fonte.is_file():
            raise FileNotFoundError(f"Fonte de candidatos não encontrada: {fonte}")
        if fonte.resolve() == destino_candidatos.resolve():
            raise ConfigError("Fonte explícita não pode ser candidatos.json de saída; use candidatos_busca.json")
    else:
        fonte = raw / "candidatos_busca.json"
        if not fonte.is_file():
            if not destino_candidatos.is_file():
                candidatos.executar(config, client)
            gravar_json(fonte, _ler(destino_candidatos))
    todos = _ler(fonte)["candidatos"]
    if len({r["id"] for r in todos}) != len(todos):
        raise ConfigError("IDs duplicados na fonte de candidatos")
    inicio, fim = janela_utc(config)
    janela = {"inicio": _iso(inicio), "fim_exclusivo": _iso(fim)}
    contexto = {"janela": janela, "inclusao": config["inclusao"], "runs": config["runs"],
                "api": config["api"]["base_url"],
                "fonte_sha256": hashlib.sha256(fonte.read_bytes()).hexdigest(), "versao": 2}
    digest = hashlib.sha256(json.dumps(contexto, sort_keys=True).encode()).hexdigest()
    pasta = raw / "checkpoints" / digest
    anteriores = {}
    if reutilizar_runs:
        seed = _ler(reutilizar_runs)
        if seed["janela"] != janela:
            raise ConfigError("Janela dos runs reutilizados divergente")
        anteriores = {r["id"]: r for r in seed["repositorios"]}
    dados = {nome: {"janela": janela, "repositorios": [], "descartes": []} for nome, *_ in ETAPAS}
    dados["candidatos"] = {"candidatos": []}
    amostra = []
    for repo in todos[:max_candidatos]:
        caminho = pasta / f"{repo['id']}.json"
        if caminho.is_file():
            registro = _ler(caminho)
            if not _identidade(registro["candidato"], repo):
                raise ConfigError("Identidade divergente no checkpoint")
        else:
            registro = {"candidato": repo, "aprovados": {}, "descartes": {}, "elegivel": False}
            etapa = "actions"
            try:
                total, proprios = actions.contar_workflows(client, repo["full_name"])
                if not proprios:
                    registro["descartes"][etapa] = actions._descarte(repo, actions.MOTIVO_SEM_ACTIONS,
                                                                       "nenhum workflow próprio")
                else:
                    registro["aprovados"][etapa] = {**repo, "total_workflows": total,
                                                     "workflows_proprios": proprios}
                    etapa = "metadados"
                    lista, descartes = metadados.coletar([repo],
                        lambda nome: metadados.coletar_repositorio(client, nome, fim),
                        config["caminhos"]["cache"])
                    if descartes:
                        registro["descartes"][etapa] = descartes[0]
                    else:
                        meta = lista[0]
                        if not _identidade(repo, meta):
                            raise ConfigError("Identidade divergente nos metadados")
                        registro["aprovados"][etapa] = meta
                        etapa = "releases"
                        rel = releases.coletar_repositorio(client, meta, inicio, fim)
                        registro["aprovados"][etapa] = rel
                        etapa = "workflow_runs"
                        n_releases = funil.contar_releases(rel, inicio, fim,
                            config["inclusao"].get("incluir_prereleases", True))["releases_publicadas"]
                        if n_releases < config["inclusao"]["min_releases"]:
                            registro["descartes"][etapa] = actions._descarte(repo,
                                "prefiltro_releases_insuficientes", f"{n_releases} releases que atendem à definição configurada")
                        else:
                            antigo = anteriores.get(repo["id"])
                            if antigo and (not _identidade(meta, antigo)
                                           or antigo["default_branch"] != meta["default_branch"]):
                                raise ConfigError("Identidade/branch divergente nos runs reutilizados")
                            runs = completos.coletar_repositorio(client, meta, inicio, fim, antigo)
                            registro["aprovados"][etapa] = runs
                            contagem = cfr.calcular_repositorio(runs, inicio, fim)
                            registro["elegivel"] = (contagem["runs_validos"] >= config["inclusao"]["min_runs_validos"]
                                                     and not runs["coleta_incompleta"])
            except requests.HTTPError as exc:
                status = getattr(exc.response, "status_code", None)
                if status not in actions.STATUS_INACESSIVEL:
                    raise
                registro["descartes"][etapa] = actions._descarte(repo, actions.MOTIVO_INACESSIVEL,
                                                                f"HTTP {status}")
            gravar_json(caminho, registro)
        dados["candidatos"]["candidatos"].append(repo)
        for etapa, valor in registro["aprovados"].items():
            dados[etapa]["repositorios"].append(valor)
        for etapa, valor in registro["descartes"].items():
            dados[etapa]["descartes"].append(valor)
        if registro["elegivel"]:
            amostra.append(repo["id"])
        gravar_json(raw / "progresso.json", {"contexto": contexto, "alvo": alvo,
                    "candidatos_avaliados": len(dados["candidatos"]["candidatos"]),
                    "elegiveis_com_coleta_completa": len(amostra), "etapa": "selecao_coleta"})
        log.info("Pipeline: %d candidatos avaliados; %d/%d elegíveis completos",
                 len(dados["candidatos"]["candidatos"]), len(amostra), alvo)
        if len(amostra) >= alvo:
            break
    for nome, _, arquivo, _ in ETAPAS:
        gravar_json(raw / arquivo, dados[nome])
    funil_resultado = funil.montar_funil(dados, config, ETAPAS)
    gravar_json(processed / "funil.json", funil_resultado)
    processed.mkdir(parents=True, exist_ok=True)
    (processed / "funil.md").write_text(funil.tabela_markdown(funil_resultado), encoding="utf-8")
    # O funil mantém inclusões com dados parciais; a execução completa exige completude.
    selecionados = [r for r in dados["workflow_runs"]["repositorios"] if r["id"] in amostra]
    entrada = raw / "amostra_workflow_runs.json"
    gravar_json(entrada, {"janela": janela, "repositorios": selecionados})
    audit_path = processed / "auditoria.json"
    audit_anterior = _ler(audit_path) if audit_path.is_file() else {}
    mesma_entrada = (audit_anterior.get("origem") == str(entrada.resolve())
                     and audit_anterior.get("entrada_sha256") == hashlib.sha256(entrada.read_bytes()).hexdigest())
    if not mesma_entrada or not (processed / "cfr.json").is_file():
        cfr.executar(config, entrada)
    saida_recuperacao = processed / tempo_recuperacao.ARQUIVO_SAIDA
    if (not mesma_entrada or not saida_recuperacao.is_file()
            or _ler(saida_recuperacao).get("versao_metrica") != tempo_recuperacao.VERSAO_METRICA):
        # A versão da métrica muda sem invalidar os checkpoints de coleta.
        if saida_recuperacao.is_file() and mesma_entrada:
            legado = processed / "tempo_recuperacao-legado-created-at.json"
            if legado.exists():
                raise ConfigError("Backup legado já existe; audite antes de sobrescrever recuperação.")
            legado.write_bytes(saida_recuperacao.read_bytes())
        tempo_recuperacao.executar(config, entrada)
    validacao = auditoria.validar(config, entrada, processed / "cfr.json", processed / "tempo_recuperacao.json")
    gravar_json(processed / "auditoria.json", validacao)
    rels = {r["id"]: r for r in dados["releases"]["repositorios"]}
    comparacoes = _coletar_compares(config, client, [rels[r["id"]] for r in selecionados], inicio, fim)
    entrada_compare = raw / compare.ARQUIVO_SAIDA
    saida_lead_time = processed / lead_time_release.ARQUIVO_SAIDA
    audit_lead_time = processed / "auditoria_lead_time.json"
    audit_lt_anterior = _ler(audit_lead_time) if audit_lead_time.is_file() else {}
    mesma_entrada_lt = (audit_lt_anterior.get("origem") == str(entrada_compare.resolve())
                       and audit_lt_anterior.get("entrada_semantica_sha256") == auditoria.hash_compare(_ler(entrada_compare))
                       and saida_lead_time.is_file())
    if not mesma_entrada_lt:
        lead_time_release.executar(config, entrada_compare, saida_lead_time)
    elif _ler(saida_lead_time).get("versao_classificacao") != VERSAO_REFERENCIA:
        # Confere valores/diagnósticos antes de migrar somente a categoria.
        auditoria.validar_lead_time(config, entrada_compare, saida_lead_time, conferir_classificacao=False)
        lead_time_release.reclassificar(saida_lead_time)
    validacao_lt = auditoria.validar_lead_time(config, entrada_compare, saida_lead_time)
    gravar_json(audit_lead_time, validacao_lt)
    # A variante por commit (#142) é recalculada do compare local a cada execução.
    lead_time_commit.executar(config, entrada_compare)
    frequencias = []
    for r in selecionados:
        quantidade = funil.contar_releases(rels[r["id"]], inicio, fim,
            config["inclusao"].get("incluir_prereleases", True))["releases_publicadas"]
        frequencia, classe = classificar_frequencia(quantidade, inicio, fim)
        frequencias.append({"id": r["id"], "full_name": r["full_name"], "releases_ano": quantidade,
                            "releases_janela": quantidade, "deployment_frequency": frequencia,
                            "classe": classe})
    gravar_json(processed / "deployment_frequency.json", {"janela": janela,
               "unidade": "releases_por_semana", "semanas_janela": (fim-inicio).total_seconds()/(7*24*3600),
               "versao_classificacao": VERSAO_REFERENCIA,
               "incluir_prereleases": config["inclusao"].get("incluir_prereleases", True),
               "repositorios": frequencias})
    _, _, pendentes = metricas.executar(config)
    resultado = {"contexto": contexto, "alvo": alvo, "total_amostra_completa": len(amostra),
                 "candidatos_avaliados": len(dados["candidatos"]["candidatos"]),
                 "execucao_completa": len(amostra) == alvo,
                 "coletas_incompletas": sum(r["coleta_incompleta"] for r in dados["workflow_runs"]["repositorios"]),
                 "metricas": [m for m in metricas.METRICAS if m not in pendentes],
                 "dependencias_pendentes": ["CFR (b) #161"] if "cfr_b" in pendentes else [],
                 "repositorios_com_lead_time_release": validacao_lt["repositorios_com_lead_time"],
                 "total_comparacoes": sum(r["total_comparacoes"] for r in comparacoes),
                 "releases_compare_ignoradas": sum(r["total_releases_ignoradas"] for r in comparacoes),
                 "coletas_compare_incompletas": sum(r["coleta_incompleta"] for r in comparacoes),
                 "raw": str(raw.resolve()), "processed": str(processed.resolve())}
    gravar_json(processed / "execucao.json", resultado)
    return resultado


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--alvo", type=int, default=100)
    parser.add_argument("--max-candidatos", type=int, default=1000)
    parser.add_argument("--candidatos", help="fonte existente; não executa nova busca")
    parser.add_argument("--reutilizar-runs", help="consolidado mensal; reutiliza meses completos")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        config = load_config(args.config)
        api = config["api"]
        client = GitHubClient(read_token(), api["base_url"], api.get("timeout_s", 30),
                              cache=CacheDisco(config["caminhos"]["cache"]))
        resultado = executar(config, client, args.alvo, args.max_candidatos, args.candidatos, args.reutilizar_runs)
    except (ConfigError, FileNotFoundError, ValueError, requests.RequestException) as exc:
        # Não imprimir objetos de requisição ou headers autenticados.
        print(f"erro: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(f"Pipeline: {resultado['total_amostra_completa']}/{args.alvo} elegíveis completos; "
          f"{resultado['candidatos_avaliados']} candidatos avaliados")
    return 0 if resultado["execucao_completa"] else 3


if __name__ == "__main__":
    sys.exit(main())
