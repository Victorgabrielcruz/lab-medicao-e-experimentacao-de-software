"""Verifica ou restaura os pacotes de dados e cache publicados, sem acessar a API."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile


def sha(caminho):
    h = hashlib.sha256()
    with caminho.open('rb') as arquivo:
        while bloco := arquivo.read(1024 * 1024):
            h.update(bloco)
    return h.hexdigest()


def restaurar(pacote, destino=None):
    pacote = Path(pacote)
    manifesto_bytes = (pacote / 'manifesto.json').read_bytes()
    manifesto = json.loads(manifesto_bytes)
    destino = Path(destino).resolve() if destino is not None else None
    if destino is not None and destino.exists():
        raise ValueError('Destino existente; escolha uma pasta nova')
    total = 0
    for grupo in manifesto['pacotes']:
        esperados = grupo['arquivos']
        partes = []
        for parte in grupo['partes']:
            nome = parte['arquivo']
            if Path(nome).name != nome or '/' in nome or '\\' in nome:
                raise ValueError('Nome de parte inseguro')
            caminho = pacote / nome
            if caminho.stat().st_size != parte['bytes'] or sha(caminho) != parte['sha256']:
                raise ValueError(f'Parte ausente ou corrompida: {nome}')
            partes.append(caminho)
        # Apenas o pacote comprimido ocupa espaço temporário durante a verificação.
        with tempfile.TemporaryFile() as unido:
            for caminho in partes:
                with caminho.open('rb') as origem:
                    shutil.copyfileobj(origem, unido)
            unido.seek(0)
            vistos = set()
            with tarfile.open(fileobj=unido, mode='r|gz') as tar:
                for membro in tar:
                    nome = membro.name
                    relativo = PurePosixPath(nome)
                    if (nome not in esperados or nome in vistos or not membro.isfile()
                            or relativo.is_absolute() or '..' in relativo.parts
                            or '\\' in nome or ':' in nome):
                        raise ValueError('Membro inesperado ou inseguro')
                    meta = esperados[nome]
                    if membro.size != meta['bytes']:
                        raise ValueError(f'Tamanho divergente: {nome}')
                    h = hashlib.sha256()
                    saida = None
                    try:
                        if destino is not None:
                            caminho = destino.joinpath(*relativo.parts)
                            if not caminho.resolve().is_relative_to(destino):
                                raise ValueError('Caminho fora do destino')
                            caminho.parent.mkdir(parents=True, exist_ok=True)
                            saida = caminho.open('xb')
                        with tar.extractfile(membro) as origem:
                            while bloco := origem.read(1024 * 1024):
                                h.update(bloco)
                                if saida is not None:
                                    saida.write(bloco)
                    finally:
                        if saida is not None:
                            saida.close()
                    if h.hexdigest() != meta['sha256']:
                        raise ValueError(f'Hash divergente: {nome}')
                    vistos.add(nome)
            if vistos != set(esperados):
                raise ValueError('Pacote incompleto')
            total += len(vistos)
    if (pacote / 'manifesto.json').read_bytes() != manifesto_bytes:
        raise ValueError('Manifesto modificado durante a leitura')
    if destino is not None:
        # A configuração original é preservada; a cópia abaixo é portátil.
        original = destino / 'raw/amostra-final-500/config.yaml'
        if original.is_file():
            config = original.read_text(encoding='utf-8').split('\ncaminhos:', 1)[0]
            config += '\ncaminhos:\n'
            for chave, pasta in [('cache', 'cache'), ('raw', 'raw/amostra-final-500'),
                                  ('processed', 'processed/amostra-final-500')]:
                config += f'  {chave}: {json.dumps(str(destino / pasta))}\n'
            (destino / 'config-local.yaml').write_text(config, encoding='utf-8')
    return {'arquivos_verificados': total, 'elegiveis': manifesto['total_amostra'],
            'processamento_final_completo': False, 'consultas_api': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modos = parser.add_mutually_exclusive_group(required=True)
    modos.add_argument('--destino', type=Path)
    modos.add_argument('--verificar', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(restaurar(Path(__file__).resolve().parent, args.destino)))
    except (ValueError, OSError, tarfile.TarError) as exc:
        parser.exit(2, f'erro: {exc}\n')


if __name__ == '__main__':
    main()
