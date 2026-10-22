"""Restaura o CFR(b) integral publicado, verificando hashes e sem sobrescrever dados (#162)."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path

BLOCO = 4 * 1024 * 1024
PASTA = Path(__file__).resolve().parent


def sha(caminho):
    h = hashlib.sha256()
    with Path(caminho).open('rb') as f:
        for b in iter(lambda: f.read(BLOCO), b''):
            h.update(b)
    return h.hexdigest()


def restaurar(destino, pasta=PASTA):
    pasta, destino = Path(pasta), Path(destino)
    m = json.loads((pasta / 'cfr_b-manifesto.json').read_text(encoding='utf-8'))
    nome = m['arquivo_gzip']
    if Path(nome).name != nome or '/' in nome or '\\' in nome:
        raise ValueError('Nome de arquivo inseguro no manifesto.')
    origem = pasta / nome
    if origem.stat().st_size != m['bytes_gzip'] or sha(origem) != m['sha256_gzip']:
        raise ValueError('Gzip corrompido.')
    if destino.exists() or not destino.parent.is_dir():
        raise ValueError('Destino deve ser um arquivo novo em pasta existente.')
    temporario = destino.with_name(destino.name + '.restaurando')
    h, n = hashlib.sha256(), 0
    out = temporario.open('xb')
    try:
        with out, gzip.open(origem, 'rb') as f:
            for b in iter(lambda: f.read(BLOCO), b''):
                out.write(b)
                h.update(b)
                n += len(b)
        if n != m['bytes_json'] or h.hexdigest() != m['sha256_json']:
            raise ValueError('JSON restaurado diverge do manifesto.')
        if os.name == 'nt':
            temporario.rename(destino)
        else:
            destino.hardlink_to(temporario)
    finally:
        temporario.unlink(missing_ok=True)
    return {'verificado': True, 'bytes': n, 'sha256': h.hexdigest(), 'destino': str(destino)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destino', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(restaurar(args.destino), ensure_ascii=False))
