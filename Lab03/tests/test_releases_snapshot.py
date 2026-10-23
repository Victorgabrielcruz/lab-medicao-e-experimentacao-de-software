import json
import runpy
import sys

import pytest

from pipeline import releases_snapshot as mod
from pipeline.config import ConfigError
from test_avaliacao_snapshot import pacote, entradas


def test_reconstroi_sequencia_integral_sem_notas_cache_ou_rede(entradas, tmp_path, monkeypatch):
    _, _, manifesto, *_ = entradas
    fonte = pacote(tmp_path, manifesto)
    antes = {p: p.read_bytes() for p in fonte.iterdir()}
    monkeypatch.setattr('requests.sessions.Session.request', lambda *a, **k: pytest.fail('Acesso à rede'))
    destino = tmp_path / 'out/releases.json'
    d = mod.preparar(fonte, destino)
    assert d['total_repositorios'] == 1 and len(d['repositorios'][0]['releases']) == 4
    assert d['janela'] == manifesto['janela'] and d['origens']['novas_consultas_api'] == 0
    assert len(d['origens']['checkpoints_usados_sha256']) == 1
    assert set(d['repositorios'][0]['releases'][0]) == {'id', 'tag_name', 'published_at', 'draft', 'prerelease'}
    assert json.loads(destino.read_text(encoding='utf-8')) == d
    assert all(p.read_bytes() == b for p, b in antes.items())
    assert mod.preparar(fonte, destino) == d


@pytest.mark.parametrize('erro', ['parte_corrompida', 'checkpoint_corrompido', 'membro_ausente',
                                 'membro_duplicado', 'parte_insegura', 'releases_ausentes_manifesto',
                                 'populacao_divergente'])
def test_fonte_invalida_recusada_sem_publicar_saida(entradas, tmp_path, erro):
    _, _, manifesto, *_ = entradas
    fonte = pacote(tmp_path, manifesto, erro=erro)
    destino = tmp_path / 'out/releases.json'
    with pytest.raises(ConfigError):
        mod.preparar(fonte, destino)
    assert not destino.exists()


def test_recusa_populacao_duplicada_e_sobrescrita_do_pacote(entradas, tmp_path):
    _, _, manifesto, *_ = entradas
    fonte = pacote(tmp_path, manifesto)
    with pytest.raises(ConfigError, match='sobrescrever'):
        mod.preparar(fonte, fonte / 'manifesto.json')
    p = fonte / 'manifesto.json'
    m = json.loads(p.read_text(encoding='utf-8')); m['ids_amostra'] *= 2
    p.write_text(json.dumps(m), encoding='utf-8')
    with pytest.raises(ConfigError, match='repetidos'):
        mod.preparar(fonte, tmp_path / 'out.json')


def test_cli_e_entrypoint(entradas, tmp_path, monkeypatch):
    _, _, manifesto, *_ = entradas
    fonte = pacote(tmp_path, manifesto)
    args = ['--pacote', str(fonte), '--saida', str(tmp_path / 'out.json')]
    assert mod.main(args) == 0
    (fonte / 'manifesto.json').unlink()
    assert mod.main(args) == 2
    monkeypatch.setattr(sys, 'argv', ['releases_snapshot', *args])
    with pytest.warns(RuntimeWarning, match='found in sys.modules'):
        with pytest.raises(SystemExit) as exc:
            runpy.run_module('pipeline.releases_snapshot', run_name='__main__')
    assert exc.value.code == 2
