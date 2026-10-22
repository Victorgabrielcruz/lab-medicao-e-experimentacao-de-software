"""Reconstitui as releases dos 500 IDs publicados sem restaurar o cache HTTP (#162)."""

import argparse
import hashlib
import json
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path

from pipeline.avaliacao_heuristica import exigir, identificador
from pipeline.cache import gravar_json
from pipeline.config import ConfigError
from pipeline.consolidado import sha256


def preparar(pacote, saida):
    """Verifica partes e checkpoints; mantém a sequência completa e os campos da CFR(b)."""
    pacote, saida = Path(pacote), Path(saida)
    exigir(not saida.resolve().is_relative_to(pacote.resolve()), "Saída não pode sobrescrever o pacote.")
    caminho = pacote / "manifesto.json"
    original = caminho.read_bytes()
    m = json.loads(original)
    ids = [identificador(i) for i in m["ids_amostra"]]
    exigir(len(ids) == len(set(ids)) and bool(ids), "IDs da população ausentes ou repetidos.")
    grupo = next(g for g in m["pacotes"] if g["nome"] == "snapshot-500")
    prefixo = f"raw/amostra-final-500/checkpoints/{m['contexto_sha256']}/"
    alvos = {f"{prefixo}{i}.json": i for i in ids}
    exigir(alvos.keys() <= grupo["arquivos"].keys(), "Checkpoint de releases ausente no manifesto.")
    fontes, usados = {}, {}
    with tempfile.TemporaryFile() as unido:
        for parte in grupo["partes"]:
            nome = parte["arquivo"]
            exigir(Path(nome).name == nome and "/" not in nome and "\\" not in nome, "Nome de parte inseguro.")
            p = pacote / nome
            exigir(p.stat().st_size == parte["bytes"] and sha256(p) == parte["sha256"],
                   f"Parte ausente ou corrompida: {nome}")
            with p.open("rb") as f:
                shutil.copyfileobj(f, unido)
        unido.seek(0)
        with tarfile.open(fileobj=unido, mode="r|gz") as tar:
            for membro in tar:
                if membro.name not in alvos:
                    continue
                exigir(membro.isfile() and membro.name not in usados, "Checkpoint inválido ou repetido.")
                conteudo = tar.extractfile(membro).read()
                meta = grupo["arquivos"][membro.name]
                h = hashlib.sha256(conteudo).hexdigest()
                exigir(len(conteudo) == meta["bytes"] and h == meta["sha256"], "Checkpoint corrompido.")
                repo = json.loads(conteudo)["aprovados"]["releases"]
                i = identificador(repo["id"])
                exigir(i == alvos[membro.name], "ID divergente no checkpoint de releases.")
                fontes[i] = {"id": repo["id"], "full_name": repo["full_name"],
                             "default_branch": repo.get("default_branch"),
                             "coleta_incompleta": repo.get("coleta_incompleta", False),
                             "releases": [{k: r.get(k) for k in ("id", "tag_name", "published_at", "draft", "prerelease")}
                                          for r in repo["releases"]]}
                usados[membro.name] = h
                del repo, conteudo
    exigir(alvos.keys() == usados.keys(), "Pacote incompleto: checkpoints não encontrados.")
    exigir(caminho.read_bytes() == original, "Manifesto mudou durante a leitura.")
    dados = {"janela": m["contexto"]["janela"], "total_repositorios": len(fontes),
             "origens": {"manifesto": str(caminho), "manifesto_sha256": hashlib.sha256(original).hexdigest(),
                         "partes_verificadas": grupo["partes"], "checkpoints_usados_sha256": usados,
                         "campos_releases": "id, tag_name, published_at, draft, prerelease; sequência integral",
                         "novas_consultas_api": 0},
             "repositorios": [fontes[i] for i in sorted(fontes, key=int)]}
    gravar_json(saida, dados)
    return dados


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pacote", default="entregas/dados-brutos-500")
    parser.add_argument("--saida", default="data/raw/validacao-final-500/releases.json")
    args = parser.parse_args(argv)
    try:
        d = preparar(args.pacote, args.saida)
    except (ConfigError, OSError, ValueError, KeyError, TypeError, StopIteration, tarfile.TarError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    print(f"Releases verificadas: {d['total_repositorios']} repositórios -> {args.saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
