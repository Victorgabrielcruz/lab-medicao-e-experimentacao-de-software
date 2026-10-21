import csv
import hashlib
import json
from pathlib import Path

import pytest
import yaml

from pipeline import amostra_capturada, integrado
from pipeline.config import ConfigError
from test_integrado import Api, configurar


def captura(tmp_path, n_compares):
    cfg, fonte = configurar(tmp_path, n=2)
    raiz = tmp_path / 'fonte'
    raw, proc = raiz / 'raw/amostra-final-500', raiz / 'processed/amostra-final-500'
    cfg['caminhos'].update(raw=str(raw), processed=str(proc))
    integrado.executar(cfg, Api(), alvo=2, max_candidatos=2, fonte=fonte)
    (raw / 'config.yaml').write_text(yaml.safe_dump(cfg), encoding='utf-8')
    progresso = json.loads((raw / 'progresso.json').read_text(encoding='utf-8'))
    compares = sorted(raw.glob('checkpoints/compare/*/*.json'))[:n_compares]
    arquivos = [raw / n for n in ('progresso.json', 'config.yaml', 'metadados.json', 'releases.json', 'amostra_workflow_runs.json')]
    arquivos += [proc / n for n in ('cfr.json', 'tempo_recuperacao.json', 'funil.json', 'auditoria.json')]
    arquivos += compares
    m = {'total_amostra': 2, 'ids_amostra': [1, 2], 'candidatos_avaliados': 2,
         'contexto': progresso['contexto'], 'capturado_em_utc': '2026-10-20T11:34:10Z',
         'pacotes': [{'nome': 'snapshot-500', 'arquivos': {
             f.relative_to(raiz).as_posix(): {'bytes': f.stat().st_size, 'sha256': hashlib.sha256(f.read_bytes()).hexdigest()}
             for f in arquivos}}]}
    manifesto = tmp_path / 'manifesto.json'
    manifesto.write_text(json.dumps(m), encoding='utf-8')
    return manifesto, raiz


@pytest.mark.parametrize('n_compares', [0, 1, 2])
def test_corte_publicado_reproduzivel_sem_api(tmp_path, monkeypatch, n_compares):
    manifesto, raiz = captura(tmp_path, n_compares)
    def sem_rede(*args, **kwargs):
        pytest.fail('Consolidação offline tentou acessar a rede')
    monkeypatch.setattr('requests.sessions.Session.request', sem_rede)
    e = amostra_capturada.executar(manifesto, raiz, tmp_path / 'offline', tmp_path / 'entrega')
    assert e['repositorios_com_compare_local'] == n_compares
    assert e['repositorios_sem_compare'] == 2 - n_compares
    assert e['novas_consultas_api'] == 0 and not e['processamento_final_completo']
    assert e['exportacao']['metricas_disponiveis']['lead_time_a'] == n_compares
    assert e['exportacao']['coleta_incompleta'] >= 2 - n_compares
    rows = list(csv.DictReader((tmp_path / 'entrega/dataset-500.csv').open(encoding='utf-8')))
    assert len(rows) == 2 and all(len(r) == 28 for r in rows)
    assert sum(r['lead_time_a'] == '' and r['coleta_incompleta'] == 'true' and
               r['calculo_parcial'] == 'true' for r in rows) == 2 - n_compares
    e2 = amostra_capturada.executar(manifesto, raiz, tmp_path / 'offline2', tmp_path / 'entrega2')
    assert e['exportacao']['csv_sha256'] == e2['exportacao']['csv_sha256']
    assert (tmp_path / 'entrega/dataset-500.csv').read_bytes() == (tmp_path / 'entrega2/dataset-500.csv').read_bytes()
    with pytest.raises(ConfigError, match='novas'):
        amostra_capturada.executar(manifesto, raiz, tmp_path / 'offline', tmp_path / 'entrega')


def test_recusa_fonte_modificada_e_saida_que_invade_origem(tmp_path):
    manifesto, raiz = captura(tmp_path, 0)
    with pytest.raises(ConfigError, match='invade'):
        amostra_capturada.executar(manifesto, raiz, raiz / 'raw/amostra-final-500/saida', tmp_path / 'entrega')
    p = raiz / 'raw/amostra-final-500/progresso.json'
    p.write_bytes(p.read_bytes() + b' ')
    with pytest.raises(ConfigError, match='diverge'):
        amostra_capturada.executar(manifesto, raiz, tmp_path / 'offline', tmp_path / 'entrega')
