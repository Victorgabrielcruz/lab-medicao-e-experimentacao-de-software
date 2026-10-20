import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile

import pytest

spec = importlib.util.spec_from_file_location('restaurar500',
    Path(__file__).resolve().parents[1] / 'entregas/dados-brutos-500/restaurar.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def pacote(tmp_path, nome='raw/amostra-final-500/config.yaml'):
    pasta = tmp_path / 'pacote'
    pasta.mkdir()
    conteudo = b'api: {}\ncaminhos:\n  raw: antigo\n'
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as tar:
        info = tarfile.TarInfo(nome)
        info.size = len(conteudo)
        tar.addfile(info, io.BytesIO(conteudo))
    bloco = buffer.getvalue()
    parte = pasta / 'snapshot.tar.gz.part001'
    parte.write_bytes(bloco)
    manifesto = {'total_amostra': 500, 'pacotes': [{'arquivos': {
        nome: {'bytes': len(conteudo), 'sha256': hashlib.sha256(conteudo).hexdigest()}},
        'partes': [{'arquivo': parte.name, 'bytes': len(bloco),
                    'sha256': hashlib.sha256(bloco).hexdigest()}]}]}
    (pasta / 'manifesto.json').write_text(json.dumps(manifesto))
    return pasta, conteudo


def test_verifica_e_restaura_bytes_com_configuracao_portatil(tmp_path):
    pasta, conteudo = pacote(tmp_path)
    assert mod.restaurar(pasta)['arquivos_verificados'] == 1
    destino = tmp_path / 'restaurado'
    assert mod.restaurar(pasta, destino)['consultas_api'] == 0
    assert (destino / 'raw/amostra-final-500/config.yaml').read_bytes() == conteudo
    assert 'antigo' not in (destino / 'config-local.yaml').read_text()
    with pytest.raises(ValueError, match='existente'):
        mod.restaurar(pasta, destino)


def test_recusa_parte_corrompida_e_caminho_fora_do_destino(tmp_path):
    pasta, _ = pacote(tmp_path, '../fora.txt')
    with pytest.raises(ValueError, match='inseguro'):
        mod.restaurar(pasta, tmp_path / 'destino')
    parte = pasta / 'snapshot.tar.gz.part001'
    parte.write_bytes(b'corrompida')
    with pytest.raises(ValueError, match='corrompida'):
        mod.restaurar(pasta)
