"""Publica, verifica e restaura compare.json em gzip dividido, sem API (#151 #153)."""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re

BLOCO = 4 * 1024 * 1024
LIMITE = 40 * 1024 * 1024
TOKEN = re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{36,255}|github_pat_[A-Za-z0-9_]{60,255})')
SUBSTITUTO = b'[TOKEN_GITHUB_REMOVIDO]'
PASTA = Path(__file__).resolve().parent


def sha(caminho):
    h = hashlib.sha256()
    with Path(caminho).open('rb') as f:
        for b in iter(lambda: f.read(BLOCO), b''):
            h.update(b)
    return h.hexdigest()


def sanear(origem, estatisticas, bloco=BLOCO):
    """Regex equivalente ao snapshot anterior, incluindo tokens entre blocos."""
    resto = b''
    h = hashlib.sha256()
    tamanho = ocorrencias = 0
    while True:
        novo = origem.read(bloco)
        h.update(novo)
        tamanho += len(novo)
        dados = resto + novo
        corte = max(0, len(dados) - 512) if novo else len(dados)
        for m in TOKEN.finditer(dados):
            if m.start() < corte < m.end():
                corte = m.start()
                break
        limpo, n = TOKEN.subn(SUBSTITUTO, dados[:corte])
        ocorrencias += n
        yield limpo
        resto = dados[corte:]
        if not novo:
            break
    estatisticas.update(bytes_origem=tamanho, sha256_origem=h.hexdigest(),
                        ocorrencias_removidas=ocorrencias)


class PartesWriter:
    def __init__(self, pasta, limite=LIMITE):
        self.pasta, self.limite = Path(pasta), limite
        self.arquivo, self.partes, self.tamanho, self.posicao = None, [], 0, 0

    def write(self, dados):
        total = len(dados)
        while dados:
            if self.arquivo is None:
                self.nome = f'compare.json.gz.part{len(self.partes) + 1:03d}'
                self.arquivo = (self.pasta / self.nome).open('xb')
                self.tamanho, self.hash = 0, hashlib.sha256()
            n = min(len(dados), self.limite - self.tamanho)
            self.arquivo.write(dados[:n])
            self.hash.update(dados[:n])
            self.tamanho += n
            self.posicao += n
            dados = dados[n:]
            if self.tamanho == self.limite:
                self.fechar_parte()
        return total

    def tell(self):
        return self.posicao

    def fechar_parte(self):
        if self.arquivo is not None:
            self.arquivo.close()
            self.partes.append({'arquivo': self.nome, 'bytes': self.tamanho, 'sha256': self.hash.hexdigest()})
            self.arquivo = None


class PartesReader(io.RawIOBase):
    def __init__(self, caminhos):
        super().__init__()
        self.caminhos = iter(caminhos)
        self.arquivo = None

    def readable(self):
        return True

    def readinto(self, buffer):
        while True:
            if self.arquivo is None:
                caminho = next(self.caminhos, None)
                if caminho is None:
                    return 0
                self.arquivo = caminho.open('rb')
            n = self.arquivo.readinto(buffer)
            if n:
                return n
            self.arquivo.close()
            self.arquivo = None

    def close(self):
        if self.arquivo is not None:
            self.arquivo.close()
        super().close()


def publicar(origem, pasta=PASTA, validacao=None):
    origem, pasta = Path(origem), Path(pasta)
    validacao = Path(validacao) if validacao else pasta.parent / 's02-03-dataset-500-final/validacao.json'
    v = json.loads(validacao.read_text(encoding='utf-8'))
    if v['execucao_completa'] is not True or v['repositorios_com_compare'] != 500:
        raise ValueError('Execução final de 500 não comprovada')
    if origem.resolve().is_relative_to(pasta.resolve()):
        raise ValueError('Origem dentro da pasta de publicação')
    pasta.mkdir(parents=True, exist_ok=True)
    if (pasta / 'manifesto.json').exists() or list(pasta.glob('compare.json.gz.part*')):
        raise ValueError('Publicação existente; use uma pasta nova')
    antes = origem.stat()
    writer = PartesWriter(pasta)
    estatisticas, h, tamanho = {}, hashlib.sha256(), 0
    try:
        with origem.open('rb') as f, gzip.GzipFile(filename='', mode='wb', fileobj=writer,
                                                compresslevel=6, mtime=0) as gz:
            for b in sanear(f, estatisticas):
                h.update(b)
                tamanho += len(b)
                gz.write(b)
        writer.fechar_parte()
    finally:
        writer.fechar_parte()
    depois = origem.stat()
    if (antes.st_size, antes.st_mtime_ns) != (depois.st_size, depois.st_mtime_ns):
        raise ValueError('Origem mudou durante a publicação')
    if estatisticas['sha256_origem'] != v['fontes_sha256']['raw/compare.json']:
        raise ValueError('Hash da origem diverge da auditoria final')
    m = {'versao': 1, 'arquivo_restaurado': 'compare.json', 'compressao': 'gzip em partes concatenáveis',
         'bytes': tamanho, 'sha256': h.hexdigest(), **estatisticas,
         'total_repositorios': v['repositorios_com_compare'],
         'total_comparacoes': v['execucao']['total_comparacoes'],
         'janela': v['execucao']['contexto']['janela'],
         'coletas_compare_incompletas': v['execucao']['coletas_compare_incompletas'],
         'releases_compare_ignoradas': v['execucao']['releases_compare_ignoradas'],
         'validacao_sha256_lf': hashlib.sha256(validacao.read_bytes().replace(b'\r\n', b'\n')).hexdigest(),
         'partes': writer.partes,
         'saneamento': 'Mesmo padrão de tokens do snapshot anterior; apenas textos públicos saneados. '
                       'IDs, datas e decisões não são recalculados.'}
    (pasta / 'manifesto.json').write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n',
                                        encoding='utf-8', newline='\n')
    return m


def restaurar(pasta=PASTA, destino=None):
    pasta = Path(pasta)
    m = json.loads((pasta / 'manifesto.json').read_text(encoding='utf-8'))
    partes = []
    for i, parte in enumerate(m['partes'], 1):
        if parte['arquivo'] != f'compare.json.gz.part{i:03d}':
            raise ValueError('Nome ou ordem de parte inválido')
        p = pasta / parte['arquivo']
        if p.stat().st_size != parte['bytes'] or sha(p) != parte['sha256']:
            raise ValueError(f'Parte corrompida: {p.name}')
        partes.append(p)
    if not partes:
        raise ValueError('Nenhuma parte')
    destino = Path(destino) if destino is not None else None
    temporario = None
    if destino is not None:
        if destino.exists() or not destino.parent.is_dir():
            raise ValueError('Destino deve ser um arquivo novo em pasta existente')
        temporario = destino.with_name(destino.name + '.restaurando')
    arquivo = temporario.open('xb') if temporario else None
    h, n = hashlib.sha256(), 0
    try:
        with io.BufferedReader(PartesReader(partes)) as unido, gzip.GzipFile(fileobj=unido) as gz:
            for b in iter(lambda: gz.read(BLOCO), b''):
                h.update(b)
                n += len(b)
                if arquivo is not None:
                    arquivo.write(b)
        if n != m['bytes'] or h.hexdigest() != m['sha256']:
            raise ValueError('Hash ou tamanho do JSON descompactado divergente')
        if arquivo is not None:
            arquivo.close()
            # No Windows, rename recusa destino existente; no POSIX, link faz o mesmo.
            if os.name == 'nt':
                temporario.rename(destino)
            else:
                destino.hardlink_to(temporario)
        return {'verificado': True, 'total_repositorios': m['total_repositorios'],
                'total_comparacoes': m['total_comparacoes'], 'bytes': n, 'sha256': h.hexdigest(),
                'partes': len(partes), 'consultas_api': 0}
    finally:
        if arquivo is not None:
            arquivo.close()
            temporario.unlink(missing_ok=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    modos = p.add_mutually_exclusive_group(required=True)
    modos.add_argument('--publicar', type=Path)
    modos.add_argument('--verificar', action='store_true')
    modos.add_argument('--destino', type=Path)
    p.add_argument('--pasta', type=Path, default=PASTA)
    args = p.parse_args()
    r = publicar(args.publicar, args.pasta) if args.publicar else restaurar(args.pasta, args.destino)
    print(json.dumps(r, ensure_ascii=True))


if __name__ == '__main__':
    main()
