"""A coleta de testes continua quando o checkout omite scripts de publicação (#253)."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


@pytest.mark.parametrize('nome,script', [
    ('test_publicacao_500.py', 'dados-brutos-500/restaurar.py'),
    ('test_compares_publicados.py', 'compares-500-final/pacote.py'),
])
def test_modulo_publicacao_omitido_e_ignorado_com_motivo(tmp_path, nome, script):
    testes = tmp_path / 'tests'
    testes.mkdir()
    copia = testes / nome
    shutil.copyfile(Path(__file__).with_name(nome), copia)
    ambiente = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTEST_ADDOPTS='',
                    PYTHONIOENCODING='utf-8')
    r = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-rs', '-p', 'no:cacheprovider', str(copia)],
                       cwd=tmp_path, env=ambiente, capture_output=True, text=True, encoding='utf-8', timeout=30)
    assert r.returncode == 5  # módulo ignorado, sem testes selecionados nesta execução isolada
    assert '1 skipped' in r.stdout and script in r.stdout
    assert 'FileNotFoundError' not in r.stdout + r.stderr
