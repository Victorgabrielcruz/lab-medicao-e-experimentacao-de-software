"""Restaura o snapshot bruto publicado e verifica todos os hashes, sem API."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        while bloco := f.read(1024 * 1024):
            h.update(bloco)
    return h.hexdigest()


def restaurar(pacote, destino):
    manifesto_bytes = (pacote / 'manifesto.json').read_bytes()
    manifesto = json.loads(manifesto_bytes)
    esperados = manifesto['arquivos_sha256']
    destino = destino.resolve()
    if destino.exists():
        raise ValueError('O destino ja existe. Escolha uma pasta nova para preservar dados e rotulos.')
    partes = []
    for parte in manifesto['partes']:
        nome = parte['arquivo']
        if Path(nome).name != nome or '/' in nome or '\\' in nome:
            raise ValueError('Nome de parte invalido')
        caminho = pacote / nome
        if caminho.stat().st_size != parte['bytes'] or sha(caminho) != parte['sha256']:
            raise ValueError(f'Parte ausente ou corrompida: {nome}')
        partes.append(caminho)
    vistos = set()
    with tempfile.TemporaryFile() as arquivo:
        for caminho in partes:
            with caminho.open('rb') as origem:
                shutil.copyfileobj(origem, arquivo)
        arquivo.seek(0)
        destino.mkdir(parents=True, exist_ok=False)
        with tarfile.open(fileobj=arquivo, mode='r|gz') as tar:
            for membro in tar:
                nome = membro.name
                relativo = PurePosixPath(nome)
                if (nome not in esperados or nome in vistos or not membro.isfile()
                        or relativo.is_absolute() or '..' in relativo.parts
                        or '\\' in nome or ':' in nome):
                    raise ValueError(f'Membro inesperado ou inseguro: {nome}')
                caminho = destino.joinpath(*relativo.parts)
                if not caminho.resolve().is_relative_to(destino):
                    raise ValueError('Caminho fora do destino')
                caminho.parent.mkdir(parents=True, exist_ok=True)
                h = hashlib.sha256()
                with tar.extractfile(membro) as origem, caminho.open('xb') as saida:
                    while bloco := origem.read(1024 * 1024):
                        h.update(bloco)
                        saida.write(bloco)
                if h.hexdigest() != esperados[nome]:
                    raise ValueError(f'Hash divergente: {nome}')
                vistos.add(nome)
    if vistos != set(esperados):
        raise ValueError('Snapshot incompleto')
    for parte, caminho in zip(manifesto['partes'], partes):
        if sha(caminho) != parte['sha256']:
            raise ValueError('Parte modificada durante a restauracao')
    if (pacote / 'manifesto.json').read_bytes() != manifesto_bytes:
        raise ValueError('Manifesto modificado durante a restauracao')
    autoridade = json.loads((destino / 'encerramento-amostra.json').read_bytes())
    if len(set(autoridade['ids_amostra'])) != manifesto['total_amostra']:
        raise ValueError('Identidade ou contagem da populacao divergente')
    if autoridade['contexto']['janela'] != manifesto['janela']:
        raise ValueError('Janela divergente')
    # A autoridade original permanece byte a byte intacta. Esta copia altera
    # somente os caminhos locais para permitir a consolidacao em outra maquina.
    autoridade['snapshot'] = str(destino / 'snapshot')
    autoridade['origem'] = str(destino / 'snapshot')
    local = destino / 'encerramento-local.json'
    local.write_text(json.dumps(autoridade, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'arquivos_verificados': len(vistos), 'total_amostra': manifesto['total_amostra'],
            'autoridade_original_sha256': manifesto['autoridade_sha256'],
            'autoridade_local': str(local), 'novas_consultas_api': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destino', required=True, type=Path, help='pasta nova para restauracao')
    args = parser.parse_args()
    try:
        resultado = restaurar(Path(__file__).resolve().parent, args.destino)
    except (ValueError, OSError, tarfile.TarError) as exc:
        parser.exit(2, f'erro: {exc}\n')
    print(json.dumps(resultado, ensure_ascii=True))


if __name__ == '__main__':
    main()
