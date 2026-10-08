"""Funil de seleção e critério mínimo de inclusão (S01-06).

Lê as saídas das etapas de coleta e conta, para cada etapa, quantos
repositórios entraram, quantos foram descartados e por quê. A última etapa
aplica o critério mínimo: pelo menos `inclusao.min_releases` releases
publicadas e `inclusao.min_runs_validos` runs válidos dentro da janela.

Releases publicadas são as que têm draft = false e published_at em
[início, fim). Runs válidos seguem as mesmas regras da CFR (S01-19): default
branch, event=push, created_at na janela, IDs deduplicados e conclusion de
sucesso ou falha. É um cálculo local, sem token e sem acesso à API.
"""

import argparse
import datetime as dt
import json
import logging
import sys
from pathlib import Path

from pipeline import actions, candidatos, metadados, workflow_runs
from pipeline.cache import gravar_json
from pipeline.cfr import calcular_repositorio
from pipeline.config import ConfigError, janela_utc, load_config

ARQUIVO_RELEASES = "releases.json"
ARQUIVO_SAIDA = "funil.json"
ARQUIVO_TABELA = "funil.md"
MOTIVO_RELEASES = "releases_insuficientes"
MOTIVO_RUNS = "runs_validos_insuficientes"
MOTIVO_AMBOS = "releases_e_runs_insuficientes"
ETAPAS = (
    ("candidatos", "Busca na Search API", candidatos.ARQUIVO_SAIDA, "candidatos"),
    ("actions", "Usa GitHub Actions", actions.ARQUIVO_SAIDA, "repositorios"),
    ("metadados", "Metadados coletados", metadados.ARQUIVO_SAIDA, "repositorios"),
    ("workflow_runs", "Workflow runs coletados", workflow_runs.ARQUIVO_SAIDA, "repositorios"),
    ("releases", "Releases coletadas", ARQUIVO_RELEASES, "repositorios"),
)
log = logging.getLogger(__name__)


def _iso(data):
    return data.isoformat(timespec="seconds").replace("+00:00", "Z")


def _data(texto, full_name):
    try:
        data = dt.datetime.fromisoformat(texto.replace("Z", "+00:00"))
        if data.tzinfo is None:
            raise ValueError("data sem fuso horário")
    except (ValueError, AttributeError) as exc:
        raise ConfigError(f"published_at inválido nas releases de {full_name}.") from exc
    return data


def contar_releases(repo, inicio, fim):
    """Conta as releases publicadas na janela, sem drafts e sem duplicatas."""
    publicadas, chaves = 0, set()
    drafts = fora_janela = duplicadas = 0
    for release in repo.get("releases", []):
        if release.get("draft") is not False:
            drafts += 1
            continue
        if not inicio <= _data(release.get("published_at"), repo["full_name"]) < fim:
            fora_janela += 1
            continue
        chave = release.get("id", release.get("tag_name"))
        if chave is None:
            raise ConfigError(f"Release sem id e sem tag_name em {repo['full_name']}.")
        if chave in chaves:
            duplicadas += 1
            continue
        chaves.add(chave)
        publicadas += 1
    return {"releases_publicadas": publicadas, "releases_draft": drafts,
            "releases_fora_janela": fora_janela, "releases_duplicadas": duplicadas}


def motivo_exclusao(releases, runs_validos, inclusao):
    """Devolve o motivo do descarte pelo critério mínimo, ou None se incluído."""
    poucas_releases = releases < inclusao["min_releases"]
    poucos_runs = runs_validos < inclusao["min_runs_validos"]
    if poucas_releases and poucos_runs:
        return MOTIVO_AMBOS
    if poucas_releases:
        return MOTIVO_RELEASES
    if poucos_runs:
        return MOTIVO_RUNS
    return None


def avaliar_etapa(nome, anteriores, aprovados, descartes):
    """Separa os que seguiram adiante dos descartados entre os `anteriores`.

    `anteriores` é a lista de IDs que chegaram à etapa, na ordem original. Os
    arquivos de coleta podem conter repositórios já descartados antes (por
    exemplo, releases coletadas a partir dos metadados), que são ignorados.
    Um repositório que chegou à etapa e não aparece no arquivo indica saídas de
    execuções diferentes.
    """
    ids_aprovados = {r["id"] for r in aprovados}
    por_id = {d["id"]: d for d in descartes}
    ausentes = [i for i in anteriores if i not in ids_aprovados and i not in por_id]
    if ausentes:
        raise ConfigError(f"{len(ausentes)} repositórios não aparecem na etapa {nome} "
                          f"(ex.: id {ausentes[0]}); as saídas parecem ser de execuções diferentes.")
    duplos = [i for i in anteriores if i in ids_aprovados and i in por_id]
    if duplos:
        raise ConfigError(f"Repositório {duplos[0]} aparece como aprovado e descartado na etapa {nome}.")
    seguem = [i for i in anteriores if i in ids_aprovados]
    descartados = [{**por_id[i], "etapa": nome} for i in anteriores if i in por_id]
    return seguem, descartados


def _contar_motivos(descartados):
    motivos = {}
    for d in descartados:
        motivos[d["motivo"]] = motivos.get(d["motivo"], 0) + 1
    return dict(sorted(motivos.items()))


def _ler(raw_dir, arquivo, etapa):
    caminho = Path(raw_dir) / arquivo
    if not caminho.is_file():
        origem = "a coleta de releases (S01-10)" if etapa == "releases" else f"a etapa {etapa}"
        raise FileNotFoundError(f"{caminho} não encontrado; execute antes {origem}.")
    return json.loads(caminho.read_text(encoding="utf-8"))


def montar_funil(dados, config, etapas_coleta=ETAPAS):
    """Monta as etapas, os descartes e a amostra a partir das saídas carregadas.

    `dados` mapeia o nome de cada etapa em ETAPAS para o JSON da sua saída.
    """
    inicio, fim = janela_utc(config)
    janela = {"inicio": _iso(inicio), "fim_exclusivo": _iso(fim)}
    for etapa in ("workflow_runs", "releases"):
        if dados[etapa].get("janela") != janela:
            raise ConfigError(f"A janela de {etapa} não corresponde à janela configurada para o funil.")

    etapas, descartes = [], []
    anteriores = None
    for nome, descricao, _, chave in etapas_coleta:
        aprovados = dados[nome][chave]
        if anteriores is None:
            seguem, descartados = list(dict.fromkeys(r["id"] for r in aprovados)), []
            entrada = len(seguem)
        else:
            seguem, descartados = avaliar_etapa(nome, anteriores, aprovados, dados[nome].get("descartes", []))
            entrada = len(anteriores)
        etapas.append({"etapa": nome, "descricao": descricao, "entrada": entrada,
                       "descartados": len(descartados), "restantes": len(seguem),
                       "motivos": _contar_motivos(descartados)})
        descartes.extend(descartados)
        anteriores = seguem

    runs = {r["id"]: r for r in dados["workflow_runs"]["repositorios"]}
    releases = {r["id"]: r for r in dados["releases"]["repositorios"]}
    inclusao = config["inclusao"]
    amostra, excluidos = [], []
    for repo_id in anteriores:
        contagem_runs = calcular_repositorio(runs[repo_id], inicio, fim)
        contagem_releases = contar_releases(releases[repo_id], inicio, fim)
        registro = {"id": repo_id, "full_name": runs[repo_id]["full_name"],
                    **contagem_releases, "runs_validos": contagem_runs["runs_validos"],
                    "coleta_runs_incompleta": contagem_runs["coleta_incompleta"]}
        motivo = motivo_exclusao(registro["releases_publicadas"], registro["runs_validos"], inclusao)
        if motivo is None:
            amostra.append(registro)
        else:
            detalhe = (f"{registro['releases_publicadas']} releases (mínimo {inclusao['min_releases']}), "
                       f"{registro['runs_validos']} runs válidos (mínimo {inclusao['min_runs_validos']})")
            excluidos.append({"id": repo_id, "full_name": registro["full_name"], "motivo": motivo,
                              "detalhe": detalhe, "etapa": "inclusao"})
    etapas.append({"etapa": "inclusao", "descricao": "Critério mínimo de inclusão",
                   "entrada": len(anteriores), "descartados": len(excluidos),
                   "restantes": len(amostra), "motivos": _contar_motivos(excluidos)})
    descartes.extend(excluidos)
    return {"janela": janela, "criterio": {"min_releases": inclusao["min_releases"],
                                           "min_runs_validos": inclusao["min_runs_validos"]},
            "etapas": etapas, "total_amostra": len(amostra), "amostra": amostra, "descartes": descartes}


def tabela_markdown(funil):
    """Tabela do funil com a quantidade por etapa e os motivos de descarte."""
    criterio = funil["criterio"]
    linhas = [
        "# Funil de seleção",
        "",
        f"Janela: `{funil['janela']['inicio']}` a `{funil['janela']['fim_exclusivo']}` (exclusivo). "
        f"Critério mínimo: {criterio['min_releases']} releases publicadas e "
        f"{criterio['min_runs_validos']} runs válidos na janela.",
        "",
        "| Etapa | Entrada | Descartados | Restantes | Motivos de descarte |",
        "|---|---:|---:|---:|---|",
    ]
    for etapa in funil["etapas"]:
        motivos = "; ".join(f"`{m}`: {n}" for m, n in etapa["motivos"].items()) or "—"
        linhas.append(f"| {etapa['descricao']} | {etapa['entrada']} | {etapa['descartados']} | "
                      f"{etapa['restantes']} | {motivos} |")
    linhas += ["", f"Amostra final: **{funil['total_amostra']}** repositórios.", ""]
    return "\n".join(linhas)


def executar(config, raw=None, saida=None):
    """Lê as saídas em `raw` e grava funil.json e funil.md em `saida`."""
    raw = Path(raw) if raw is not None else Path(config["caminhos"]["raw"])
    saida = Path(saida) if saida is not None else Path(config["caminhos"]["processed"])
    if saida.resolve() == raw.resolve():
        raise ConfigError("A saída do funil deve ser diferente da pasta de dados brutos.")
    dados = {nome: _ler(raw, arquivo, nome) for nome, _, arquivo, _ in ETAPAS}
    funil = montar_funil(dados, config)
    incompletas = sum(r["coleta_runs_incompleta"] for r in funil["amostra"])
    if incompletas:
        log.warning("%d repositórios da amostra têm coleta de runs incompleta.", incompletas)
    gravar_json(saida / ARQUIVO_SAIDA, {
        "gerado_em": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "origem": str(raw), **funil,
    })
    tabela = saida / ARQUIVO_TABELA
    tabela.write_text(tabela_markdown(funil), encoding="utf-8")
    return saida / ARQUIVO_SAIDA, tabela, funil


def main(argv=None):
    parser = argparse.ArgumentParser(description="Funil de seleção e critério mínimo de inclusão.")
    parser.add_argument("--config", default="config.yaml", help="caminho da configuração")
    parser.add_argument("--raw", help="pasta com as saídas da coleta (padrão: caminhos.raw)")
    parser.add_argument("--saida", help="pasta de funil.json e funil.md (padrão: caminhos.processed)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        caminho, tabela, funil = executar(load_config(args.config), args.raw, args.saida)
    except (ConfigError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    print(tabela_markdown(funil))
    print(f"Funil: {funil['etapas'][0]['entrada']} candidatos -> {funil['total_amostra']} na amostra "
          f"-> {caminho} e {tabela}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
