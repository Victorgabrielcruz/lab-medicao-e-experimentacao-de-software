"""Heurística corretiva v1 e CFR(b) sobre releases/compares locais (#161)."""

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

from pipeline.cache import gravar_json
from pipeline.classificacao import VERSAO_REFERENCIA, classificar_metrica
from pipeline.config import ConfigError, janela_utc, load_config
from pipeline.releases import _data_publicacao, _iso

ARQUIVO_SAIDA = "cfr_b.json"
VERSAO_HEURISTICA = "corretiva-v1-patch-ou-mensagem"
INTERVALO = dt.timedelta(days=7)
# SemVer estável: prefixo v opcional; build metadata não altera precedência.
SEMVER = re.compile(r"v?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
                    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?")
MENSAGEM = re.compile(r"\b(?:fix|revert|hotfix)\b", re.IGNORECASE)


def patch_semver(anterior, atual):
    """True só para aumento do patch com major/minor iguais; None sem base."""
    if anterior is None:
        return None
    versoes = [SEMVER.fullmatch(tag) if isinstance(tag, str) else None
               for tag in (anterior, atual)]
    if not all(versoes):
        return False
    base, head = [tuple(map(int, v.groups())) for v in versoes]
    return base[:2] == head[:2] and head[2] > base[2]


def identificar_corretiva(release, anterior=None, comparacao=None):
    """OR com três estados: evidência positiva basta; negativo exige compare completo."""
    patch = patch_semver(anterior.get("tag_name") if anterior else None, release.get("tag_name"))
    commits = comparacao.get("commits", []) if comparacao else []
    if not isinstance(commits, list):
        raise ConfigError("Lista de commits inválida no compare da CFR(b).")
    mensagens = [(c.get("sha"), (c.get("commit") or {}).get("message")) for c in commits]
    sinais = [{"sha": sha, "termo": match.group().lower()}
              for sha, mensagem in mensagens if isinstance(mensagem, str)
              for match in [MENSAGEM.search(mensagem)] if match]
    completo = bool(comparacao is not None and not comparacao.get("ignorada")
                    and not comparacao.get("coleta_incompleta")
                    and comparacao.get("total_commits_api") == len(commits)
                    and comparacao.get("total_commits_coletados") == len(commits)
                    and len({sha for sha, _ in mensagens}) == len(commits)
                    and all(sha and isinstance(m, str) and m.strip() for sha, m in mensagens))
    corretiva = True if patch or sinais else False if completo and patch is not None else None
    return {"corretiva": corretiva, "patch_semver": patch,
            "commits_corretivos": sinais, "compare_completo": completo,
            "motivo_corretiva": ("patch_e_mensagem" if patch and sinais else "patch_semver" if patch
                                 else "mensagem_commit" if sinais else "sem_sinais" if corretiva is False
                                 else "evidencia_insuficiente")}


def _indice(lista, chave, contexto):
    indice = {}
    for item in lista:
        if item.get(chave) is None or item[chave] in indice:
            raise ConfigError(f"ID ausente ou duplicado em {contexto}.")
        indice[item[chave]] = item
    return indice


def calcular_repositorio(repo, inicio, fim, compare=None):
    """Avalia qualquer corretiva posterior até 7 dias; censura antes da avaliação."""
    retidas, fora_recorte, duplicadas = {}, 0, 0
    for release in repo["releases"]:
        if release.get("draft") is not False or release.get("prerelease") is not False:
            fora_recorte += 1
            continue
        data = _data_publicacao(release)
        if data is None:
            raise ConfigError(f"published_at inválido nas releases de {repo['full_name']}.")
        if not inicio <= data < fim:
            fora_recorte += 1
            continue
        if release.get("id") is None:
            raise ConfigError(f"Release sem ID em {repo['full_name']}.")
        if release["id"] in retidas:
            if retidas[release["id"]] != release:
                raise ConfigError(f"Release duplicada divergente em {repo['full_name']}.")
            duplicadas += 1
        retidas[release["id"]] = release
    ordenadas = sorted(retidas.values(), key=lambda r: (_data_publicacao(r), r["id"]))
    if compare is not None and (compare["id"] != repo["id"]
                                or compare["full_name"].lower() != repo["full_name"].lower()):
        raise ConfigError("Identidade divergente entre releases e compare da CFR(b).")
    comparacoes = {}
    for c in compare.get("comparacoes", []) if compare else []:
        identificador = c["release"]["id"]
        if identificador in comparacoes or identificador not in retidas:
            raise ConfigError("Compare duplicado ou release desconhecida na CFR(b).")
        comparacoes[identificador] = c
    detalhes = []
    for i, release in enumerate(ordenadas):
        c = comparacoes.get(release["id"])
        anterior = ordenadas[i-1] if i else None
        if c is not None:
            if (c["release"].get("tag_name") != release.get("tag_name")
                    or _data_publicacao(c["release"]) != _data_publicacao(release)):
                raise ConfigError("Release divergente entre releases e compare da CFR(b).")
            base = c.get("release_anterior")
            if base is None and c.get("ignorada"):
                # Histórico inacessível não apaga a base que existe nas releases locais.
                base = anterior
            if anterior is not None:
                if (base is None or base.get("id") != anterior["id"]
                        or base.get("tag_name") != anterior.get("tag_name")
                        or _data_publicacao(base) != _data_publicacao(anterior)):
                    raise ConfigError("Base divergente entre releases e compare da CFR(b).")
            elif base is not None:
                data_base = _data_publicacao(base)
                if data_base is None or data_base >= inicio:
                    raise ConfigError("Base histórica inválida no compare da CFR(b).")
            anterior = base
        detalhes.append({"release_id": release["id"], "tag_name": release.get("tag_name"),
                         "published_at": _iso(_data_publicacao(release).astimezone(dt.timezone.utc)),
                         **identificar_corretiva(release, anterior, c)})
    fonte_incompleta = bool(repo.get("coleta_incompleta"))
    for i, detalhe in enumerate(detalhes):
        data = _data_publicacao(detalhe)
        censurada = data >= fim - INTERVALO
        posteriores = []
        if not censurada:
            for j in range(i+1, len(detalhes)):
                seguinte = detalhes[j]
                delta = _data_publicacao(seguinte) - data
                if delta > INTERVALO:
                    break
                if delta > dt.timedelta(0):
                    posteriores.append(seguinte)
        corretivas = [r["release_id"] for r in posteriores if r["corretiva"] is True]
        desconhecida = fonte_incompleta or any(r["corretiva"] is None for r in posteriores)
        falhou = None if censurada else True if corretivas else None if desconhecida else False
        detalhe.update(censurada=censurada, falhou=falhou, releases_corretivas_posteriores=corretivas,
                       motivo_avaliacao=("ultimos_7_dias" if censurada else "corretiva_ate_7_dias" if falhou
                                         else "evidencia_insuficiente" if falhou is None
                                         else "sem_corretiva_ate_7_dias"))
    avaliadas = sum(r["falhou"] is not None for r in detalhes)
    falhas = sum(r["falhou"] is True for r in detalhes)
    censuradas = sum(r["censurada"] for r in detalhes)
    ignoradas = len(detalhes) - avaliadas - censuradas
    valor = falhas / avaliadas if avaliadas else None
    return {"id": repo["id"], "full_name": repo["full_name"],
            "total_releases": len(detalhes), "releases_avaliadas": avaliadas,
            "releases_falhas": falhas, "releases_censuradas": censuradas,
            "releases_indeterminadas": ignoradas, "releases_fora_recorte": fora_recorte,
            "releases_duplicadas": duplicadas, "change_failure_rate": valor,
            "classe_cfr": classificar_metrica("change_failure_rate", valor),
            "coleta_incompleta": fonte_incompleta or any(
                not r["compare_completo"] and comparacoes.get(r["release_id"], {}).get("motivo")
                != "sem_release_anterior" for r in detalhes),
            "calculo_parcial": fonte_incompleta or ignoradas > 0, "releases": detalhes}


def executar(config, entrada=None, compares=None, saida=None, ids=None, amostra=None):
    """Lê somente arquivos locais; compare ausente não equivale a lista vazia coletada."""
    raw = Path(config["caminhos"]["raw"])
    entrada = Path(entrada) if entrada is not None else raw / "releases.json"
    caminho_compare = Path(compares) if compares is not None else raw / "compare.json"
    saida = Path(saida) if saida is not None else Path(config["caminhos"]["processed"]) / ARQUIVO_SAIDA
    entradas = {entrada.resolve(), caminho_compare.resolve()}
    if amostra is not None:
        entradas.add(Path(amostra).resolve())
    if saida.resolve() in entradas:
        raise ConfigError("A saída da CFR(b) deve ser diferente das entradas.")
    inicio, fim = janela_utc(config)
    janela = {"inicio": _iso(inicio), "fim_exclusivo": _iso(fim)}

    def ler(caminho):
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        if dados.get("janela") != janela:
            raise ConfigError(f"Janela divergente em {caminho.name} para a CFR(b).")
        return dados

    releases = _indice(ler(entrada)["repositorios"], "id", "releases")
    if amostra is not None:
        if ids is not None:
            raise ConfigError("Use somente ids ou arquivo de amostra na CFR(b).")
        selecionados = _indice(ler(Path(amostra))["repositorios"], "id", "amostra")
        for i, r in selecionados.items():
            if i in releases and r["full_name"].lower() != releases[i]["full_name"].lower():
                raise ConfigError("Identidade divergente na amostra da CFR(b).")
        ids = set(selecionados)
    if ids is not None:
        if not set(ids) <= releases.keys():
            raise ConfigError("Repositório selecionado ausente nas releases da CFR(b).")
        releases = {i: r for i, r in releases.items() if i in ids}
    from pipeline import consolidado
    dados_compare = None
    if caminho_compare.is_file() or compares is not None:
        dados_compare = consolidado.cabecalho(caminho_compare)
        if dados_compare.get("janela") != janela:
            raise ConfigError(f"Janela divergente em {caminho_compare.name} para a CFR(b).")
        if dados_compare.get("definicao_deploy") != "release_estavel":
            raise ConfigError("A CFR(b) exige compare com definicao_deploy=release_estavel.")
    calculados, vistos = {}, set()
    if dados_compare:
        for cp in consolidado.repositorios(caminho_compare):
            i = cp.get("id")
            if i is None or i in vistos:
                raise ConfigError("ID ausente ou duplicado em compare.")
            vistos.add(i)
            if i in releases:
                calculados[i] = calcular_repositorio(releases[i], inicio, fim, cp)
    lista = [calculados[i] if i in calculados else calcular_repositorio(repo, inicio, fim)
             for i, repo in releases.items()]
    gravar_json(saida, {
        "gerado_em": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "origens": {"releases": str(entrada), "compare": str(caminho_compare) if dados_compare else None,
                    "amostra": str(amostra) if amostra is not None else None},
        "janela": janela, "variante": "b", "versao_heuristica": VERSAO_HEURISTICA,
        "versao_classificacao": VERSAO_REFERENCIA, "validacao_manual_pendente": True,
        "regra_temporal": "qualquer release corretiva posterior; 0 < intervalo <= 7 dias",
        "censura": "published_at >= fim_exclusivo - 7 dias",
        "total_repositorios": len(lista),
        "repositorios_com_cfr": sum(r["change_failure_rate"] is not None for r in lista),
        "repositorios_com_coleta_incompleta": sum(r["coleta_incompleta"] for r in lista),
        "repositorios_com_calculo_parcial": sum(r["calculo_parcial"] for r in lista),
        "repositorios": lista,
    })
    return saida, lista


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--entrada", help="Releases locais; padrão: raw/releases.json")
    parser.add_argument("--compare", help="Compare local; padrão: raw/compare.json, quando disponível")
    parser.add_argument("--saida", help="Padrão: processed/cfr_b.json")
    parser.add_argument("--amostra", help="JSON de deployment_frequency para restringir aos IDs elegíveis")
    args = parser.parse_args(argv)
    try:
        saida, lista = executar(load_config(args.config), args.entrada, args.compare, args.saida,
                               amostra=args.amostra)
    except (ConfigError, OSError, json.JSONDecodeError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    calculadas = sum(r["change_failure_rate"] is not None for r in lista)
    print(f"CFR (b) v1: {calculadas}/{len(lista)} repositórios com valor -> {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
