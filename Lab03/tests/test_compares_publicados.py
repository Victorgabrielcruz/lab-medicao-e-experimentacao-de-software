import hashlib
import importlib.util
import io
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('pacote_compares',
    Path(__file__).resolve().parents[1] / 'entregas/compares-500-final/pacote.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


@pytest.mark.parametrize('bloco', [1, 31, 512, 1024, 4096])
def test_saneamento_streaming_equivale_a_regex_inteira(bloco):
    dados = (b'x' * 501 + b'ghp_' + b'A' * 36 + b' ' + b'github_pat_' + b'B' * 83
             + b' ' + b'ghs_' + b'C' * 300 + b' ' + b'ghp_curto ' + b'z' * 1000)
    estatisticas = {}
    resultado = b''.join(mod.sanear(io.BytesIO(dados), estatisticas, bloco))
    esperado, n = mod.TOKEN.subn(mod.SUBSTITUTO, dados)
    assert resultado == esperado
    assert estatisticas['sha256_origem'] == hashlib.sha256(dados).hexdigest()
    assert estatisticas['bytes_origem'] == len(dados)
    assert estatisticas['ocorrencias_removidas'] == n


def publicar(tmp_path, monkeypatch):
    dados = json.dumps({'repositorios': [], 'message': 'ghp_' + 'A' * 36}).encode()
    origem = tmp_path / 'origem.json'
    origem.write_bytes(dados)
    validacao = tmp_path / 'validacao.json'
    validacao.write_text(json.dumps({
        'execucao_completa': True, 'repositorios_com_compare': 500,
        'fontes_sha256': {'raw/compare.json': hashlib.sha256(dados).hexdigest()},
        'execucao': {'total_comparacoes': 34151, 'contexto': {'janela': {'inicio': 'a', 'fim_exclusivo': 'b'}},
                     'coletas_compare_incompletas': 11, 'releases_compare_ignoradas': 104}}))
    writer = mod.PartesWriter
    monkeypatch.setattr(mod, 'PartesWriter', lambda pasta: writer(pasta, limite=32))
    pasta = tmp_path / 'pacote'
    manifesto = mod.publicar(origem, pasta, validacao)
    return pasta, manifesto, dados, origem, validacao


def test_publica_verifica_restaura_e_preserva_origem(tmp_path, monkeypatch):
    pasta, m, dados, origem, _ = publicar(tmp_path, monkeypatch)
    assert len(m['partes']) > 1
    assert all(p['bytes'] <= 32 for p in m['partes'])
    assert m['ocorrencias_removidas'] == 1
    assert origem.read_bytes() == dados
    assert mod.restaurar(pasta)['verificado']
    destino = tmp_path / 'compare.json'
    mod.restaurar(pasta, destino)
    assert destino.read_bytes() == mod.TOKEN.sub(mod.SUBSTITUTO, dados)
    assert json.loads(destino.read_bytes())['message'] == mod.SUBSTITUTO.decode()
    with pytest.raises(ValueError, match='novo'):
        mod.restaurar(pasta, destino)


def test_recusa_corrupcao_da_parte_e_caminho_inseguro(tmp_path, monkeypatch):
    pasta, m, *_ = publicar(tmp_path, monkeypatch)
    primeira = pasta / m['partes'][0]['arquivo']
    primeira.write_bytes(b'corrompida')
    with pytest.raises(ValueError, match='corrompida'):
        mod.restaurar(pasta)
    m['partes'][0]['arquivo'] = '../fora'
    (pasta / 'manifesto.json').write_text(json.dumps(m))
    with pytest.raises(ValueError, match='inválido'):
        mod.restaurar(pasta)


def test_recusa_hash_descompactado_errado_sem_publicar_destino(tmp_path, monkeypatch):
    pasta, m, *_ = publicar(tmp_path, monkeypatch)
    m['sha256'] = '0' * 64
    (pasta / 'manifesto.json').write_text(json.dumps(m))
    destino = tmp_path / 'compare.json'
    with pytest.raises(ValueError, match='descompactado'):
        mod.restaurar(pasta, destino)
    assert not destino.exists()
    assert not destino.with_name('compare.json.restaurando').exists()


def test_publicacao_e_reproduzivel_e_nao_sobrescreve(tmp_path, monkeypatch):
    pasta, m, _, origem, validacao = publicar(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match='existente'):
        mod.publicar(origem, pasta, validacao)
    outra = tmp_path / 'outra'
    mod.publicar(origem, outra, validacao)
    for p in pasta.iterdir():
        assert p.read_bytes() == (outra / p.name).read_bytes()


def test_recusa_origem_diferente_da_auditoria(tmp_path, monkeypatch):
    _, _, _, origem, validacao = publicar(tmp_path, monkeypatch)
    origem.write_bytes(b'{}')
    with pytest.raises(ValueError, match='auditoria'):
        mod.publicar(origem, tmp_path / 'outra', validacao)
