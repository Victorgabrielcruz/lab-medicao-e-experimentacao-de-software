"""Integridade e proteção de arquivos do pacote completo de CFR(b) (#162)."""
import gzip
import importlib.util
import json
from pathlib import Path

import pytest

CAMINHO = Path(__file__).resolve().parents[1] / 'validacao/avaliacao-heuristica/final-500/restaurar_cfr_b.py'
spec = importlib.util.spec_from_file_location('restaurar_cfr_final', CAMINHO)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


@pytest.fixture
def pacote(tmp_path):
    conteudo = b'{"repositorios": []}\n'
    p = tmp_path / 'pacote'
    p.mkdir()
    z = p / 'cfr_b.json.gz'
    z.write_bytes(gzip.compress(conteudo, mtime=0))
    import hashlib
    m = {'arquivo_gzip': z.name, 'bytes_gzip': z.stat().st_size,
         'sha256_gzip': mod.sha(z), 'bytes_json': len(conteudo),
         'sha256_json': hashlib.sha256(conteudo).hexdigest()}
    (p / 'cfr_b-manifesto.json').write_text(json.dumps(m))
    return p, m, conteudo


def test_restauracao_confere_hash_e_preserva_fonte(pacote, tmp_path):
    p, m, conteudo = pacote
    antes = {f.name: f.read_bytes() for f in p.iterdir()}
    destino = tmp_path / 'saida.json'
    d = mod.restaurar(destino, p)
    assert d['verificado'] and d['sha256'] == m['sha256_json']
    assert destino.read_bytes() == conteudo
    assert {f.name: f.read_bytes() for f in p.iterdir()} == antes
    assert not destino.with_name(destino.name + '.restaurando').exists()


@pytest.mark.parametrize('campo,valor', [('bytes_gzip', 0), ('sha256_gzip', 'x'),
    ('bytes_json', 0), ('sha256_json', 'x'), ('arquivo_gzip', '../cfr_b.json.gz')])
def test_corrupcao_recusada_sem_publicar_saida(pacote, tmp_path, campo, valor):
    p, m, _ = pacote
    m[campo] = valor
    (p / 'cfr_b-manifesto.json').write_text(json.dumps(m))
    destino = tmp_path / 'saida.json'
    with pytest.raises(ValueError):
        mod.restaurar(destino, p)
    assert not destino.exists()
    assert not destino.with_name(destino.name + '.restaurando').exists()


def test_preserva_destino_e_temporario_preexistentes(pacote, tmp_path):
    p, _, _ = pacote
    destino = tmp_path / 'saida.json'
    destino.write_bytes(b'dado do usuario')
    with pytest.raises(ValueError):
        mod.restaurar(destino, p)
    assert destino.read_bytes() == b'dado do usuario'
    destino.unlink()
    temporario = destino.with_name(destino.name + '.restaurando')
    temporario.write_bytes(b'outro processo')
    with pytest.raises(FileExistsError):
        mod.restaurar(destino, p)
    assert temporario.read_bytes() == b'outro processo'
    assert not destino.exists()
