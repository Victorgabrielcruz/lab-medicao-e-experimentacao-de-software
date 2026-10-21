"""Reproduz a avaliação #162 com o corte histórico publicado, sem restaurar todo o cache."""

import argparse
import hashlib
import json
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

from pipeline import avaliacao_heuristica as av, cfr_b, consolidado
from pipeline.cache import gravar_json


def reduzir_compare(cp, ids):
    """Só reduz campos não usados pela #161; não decide o rótulo corretiva."""
    resultado = {"id": cp["id"], "full_name": cp["full_name"], "comparacoes": []}
    for c in cp["comparacoes"]:
        if av.identificador(c["release"]["id"]) not in ids:
            continue
        r = {k: v for k, v in c.items() if k != "commits"}
        r["commits"] = [{"sha": x.get("sha"), "commit": {"message": (x.get("commit") or {}).get("message")}}
                        for x in c.get("commits", [])]
        resultado["comparacoes"].append(r)
    return resultado


def carregar(pacote, pasta, sequencia_completa=False):
    pacote, pasta = Path(pacote), Path(pasta)
    caminho = pacote / "manifesto.json"
    original = caminho.read_bytes()
    m = json.loads(original)
    amostra, esperadas = av.carregar_amostra(pasta / "amostra_ouro.json")
    av.exigir(av.janela(m["contexto"]) == av.janela(amostra), "Snapshot tem janela divergente da amostra.")
    ids = {i for i, _ in esperadas}
    av.exigir(ids <= {av.identificador(i) for i in m["ids_amostra"]}, "Snapshot não contém todos os repositórios da amostra.")
    grupo = next(p for p in m["pacotes"] if p["nome"] == "snapshot-500")
    arquivos = grupo["arquivos"]
    prefixo = "raw/amostra-final-500/checkpoints/"
    releases_esperadas = {f"{prefixo}{m['contexto_sha256']}/{i}.json": i for i in ids}
    av.exigir(releases_esperadas.keys() <= arquivos.keys(), "Checkpoint de releases ausente no manifesto.")
    compares_esperados = {n for n in arquivos if n.startswith(prefixo + "compare/") and PurePosixPath(n).stem in ids}
    alvos = set(releases_esperadas) | compares_esperados
    fontes, bases, compares, usados = {}, {}, {}, {}
    with tempfile.TemporaryFile() as unido:
        for parte in grupo["partes"]:
            nome = parte["arquivo"]
            av.exigir(Path(nome).name == nome and "/" not in nome and "\\" not in nome, "Nome de parte inseguro.")
            arquivo = pacote / nome
            av.exigir(arquivo.stat().st_size == parte["bytes"] and consolidado.sha256(arquivo) == parte["sha256"],
                       f"Parte ausente ou corrompida: {nome}")
            with arquivo.open("rb") as origem:
                shutil.copyfileobj(origem, unido)
        unido.seek(0)
        with tarfile.open(fileobj=unido, mode="r|gz") as tar:
            for membro in tar:
                if membro.name not in alvos:
                    continue
                av.exigir(membro.isfile() and membro.name not in usados, "Checkpoint inválido ou repetido no pacote.")
                meta = arquivos[membro.name]
                conteudo = tar.extractfile(membro).read()
                av.exigir(len(conteudo) == meta["bytes"] and hashlib.sha256(conteudo).hexdigest() == meta["sha256"],
                           f"Checkpoint corrompido: {membro.name}")
                cp = json.loads(conteudo)
                usados[membro.name] = meta["sha256"]
                if membro.name in releases_esperadas:
                    i = releases_esperadas[membro.name]
                    repo = cp["aprovados"]["releases"]
                    av.exigir(av.identificador(repo["id"]) == i, "ID divergente no checkpoint de releases.")
                    contexto = {"releases": repo, "janela": amostra["janela"],
                                "api": m["contexto"]["api"], "versao_compare": 1}
                    digest = hashlib.sha256(json.dumps(contexto, sort_keys=True).encode()).hexdigest()
                    bases[i] = prefixo + f"compare/{digest}/{i}.json"
                    release_ids = [av.identificador(r["id"]) for r in repo["releases"]]
                    av.exigir(len(release_ids) == len(set(release_ids)), "Releases repetidas no checkpoint.")
                    fontes[i] = {"id": repo["id"], "full_name": repo["full_name"],
                                 "coleta_incompleta": repo.get("coleta_incompleta", False),
                                 "releases": [{k: r.get(k) for k in ("id", "tag_name", "published_at", "draft", "prerelease")}
                                              for r in repo["releases"]]}
                    del repo, contexto
                else:
                    i = av.identificador(cp["id"])
                    av.exigir(i == PurePosixPath(membro.name).stem, "ID divergente no checkpoint de compare.")
                    ids_compare = ({av.identificador(c["release"]["id"]) for c in cp["comparacoes"]}
                                   if sequencia_completa else {rel for rid, rel in esperadas if rid == i})
                    compares[membro.name] = reduzir_compare(cp, ids_compare)
                # Não manter os corpos/assets nem os patches grandes na memória entre membros.
                del cp, conteudo
        av.exigir(alvos == usados.keys(), "Pacote incompleto: checkpoints esperados não encontrados.")
    av.exigir(caminho.read_bytes() == original, "Manifesto do snapshot mudou durante a leitura.")
    resultados, com_compare, sem_compare = [], [], []
    for i in sorted(ids, key=int):
        cp = compares.get(bases[i])
        (com_compare if cp is not None else sem_compare).append(int(i))
        r = cfr_b.calcular_repositorio(fontes[i], *av.janela(amostra), cp)
        if sequencia_completa:
            resultados.append(r)
            continue
        selecionadas = {key[1] for key in esperadas if key[0] == i}
        r["releases"] = [rel for rel in r["releases"] if av.identificador(rel["release_id"]) in selecionadas]
        # A decisão acima usou todas as mensagens; o artefato de revisão guarda
        # contagem e exemplos dos sinais, pois os membros originais têm hashes.
        for rel in r["releases"]:
            sinais = rel.pop("commits_corretivos")
            rel["total_commits_corretivos"] = len(sinais)
            rel["exemplos_commits_corretivos"] = sinais[:5]
        resultados.append({k: r[k] for k in ("id", "full_name", "releases")})
    fonte = {"snapshot": str(pacote), "manifesto_sha256": hashlib.sha256(original).hexdigest(),
             "partes_verificadas": grupo["partes"], "checkpoints_usados_sha256": usados,
             "capturado_em_utc": m.get("capturado_em_utc"),
             "repositorios_com_compare_compativel": com_compare, "repositorios_sem_compare_compativel": sem_compare,
             "processamento_final_completo_do_snapshot": m.get("processamento_final_completo"),
             "codigo_heuristica_sha256": consolidado.sha256(Path(cfr_b.__file__)),
             "codigo_recuperacao_sha256": consolidado.sha256(Path(__file__)),
             "limite_exemplos_commits_corretivos": 5, "novas_consultas_api": 0}
    dados = {"janela": amostra["janela"], "variante": "b", "versao_heuristica": cfr_b.VERSAO_HEURISTICA,
             "origens_snapshot": fonte, "repositorios": resultados}
    if sequencia_completa:
        dados.update(
            versao_classificacao=cfr_b.VERSAO_REFERENCIA, validacao_manual_pendente=True,
            regra_temporal="qualquer release corretiva posterior; 0 < intervalo <= 7 dias",
            censura="published_at >= fim_exclusivo - 7 dias", total_repositorios=len(resultados),
            total_releases=sum(r["total_releases"] for r in resultados),
            repositorios_com_cfr=sum(r["change_failure_rate"] is not None for r in resultados),
            repositorios_com_coleta_incompleta=sum(r["coleta_incompleta"] for r in resultados),
            repositorios_com_calculo_parcial=sum(r["calculo_parcial"] for r in resultados),
            escopo="Sequência completa dos repositórios da amostra-ouro; snapshot histórico parcial, anterior aos compares finais dos 500.",
            processamento_final_completo=False,
        )
    return dados


def gerar_cfr_b(pacote, *, pasta=av.PASTA_SAIDA, saida):
    """Gera o contrato completo da #161 para os projetos sorteados, sem inventar compares."""
    destino = Path(saida).resolve()
    for origem in (Path(pacote).resolve(), Path(pasta).resolve()):
        av.exigir(not destino.is_relative_to(origem), "CFR(b) não pode sobrescrever o pacote ou a amostra oficial.")
    dados = carregar(pacote, pasta, sequencia_completa=True)
    gravar_json(saida, dados)
    return dados


def executar(pacote, *, pasta=av.PASTA_SAIDA, saida="validacao/avaliacao-heuristica/snapshot-500"):
    saida = Path(saida)
    fonte = saida / "entrada_snapshot.json"
    # Os pacotes e as planilhas oficiais permanecem somente leitura.
    origem = Path(pacote).resolve()
    av.exigir(not saida.resolve().is_relative_to(origem) and not origem.is_relative_to(saida.resolve()),
               "Saída não pode invadir o pacote do snapshot.")
    dados = carregar(pacote, pasta)
    gravar_json(fonte, dados)
    return av.executar(fonte, pasta=pasta, saida=saida)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pacote", default="entregas/dados-brutos-500")
    parser.add_argument("--pasta", default=av.PASTA_SAIDA)
    parser.add_argument("--saida", default="validacao/avaliacao-heuristica/snapshot-500")
    parser.add_argument("--cfr-b", metavar="ARQUIVO", help="Gera somente cfr_b.json com toda a sequência dos projetos sorteados")
    args = parser.parse_args(argv)
    try:
        if args.cfr_b:
            dados = gerar_cfr_b(args.pacote, pasta=args.pasta, saida=args.cfr_b)
            print(f"CFR(b) do snapshot parcial: {dados['total_repositorios']} repositórios, "
                  f"{dados['total_releases']} releases -> {args.cfr_b}")
            return 0
        r = executar(args.pacote, pasta=args.pasta, saida=args.saida)
    except (av.ConfigError, OSError, ValueError, KeyError, TypeError, StopIteration, tarfile.TarError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    print(f"Snapshot: {r['cobertura']['avaliadas']}/{r['cobertura']['total_amostra']} releases avaliadas -> {args.saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
