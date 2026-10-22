import json

import pytest

from pipeline.auditoria_cfr_final import auditar, main
from pipeline.config import ConfigError


@pytest.fixture
def fontes(tmp_path):
    def gravar(nome, obj):
        p = tmp_path / nome
        p.write_text(json.dumps(obj))
        return p
    cfr = gravar('cfr.json', {'repositorios': [{'id': 1, 'full_name': 'x/y',
        'change_failure_rate': 0.5, 'releases': [{'release_id': 10, 'tag_name': 'v1.0.0',
        'published_at': '2026-01-01T00:00:00Z', 'corretiva': None}]}]})
    compare = gravar('compare.json', {'repositorios': [{'id': 1, 'comparacoes': [
        {'release': {'id': 10}, 'release_anterior': None, 'ignorada': True,
         'motivo': 'sem_release_anterior', 'total_commits_coletados': 0}]}]})
    dataset = tmp_path / 'dataset.csv'
    dataset.write_text('id,cfr_b\n1,0.5\n')
    ouro = gravar('ouro.json', {'repositorios': [{'repo_id': 1, 'releases': [{'release_id': 10}]}]})
    return cfr, compare, dataset, ouro


def test_conferencia_e_diagnostico_rastreaveis(fontes, tmp_path):
    r = auditar(*fontes)
    assert r['comparacao_cfr_b_com_csv_final']['divergencias'] == 0
    assert r['releases_indeterminadas'] == 1
    assert r['indeterminadas'][0]['na_amostra_ouro'] is True
    assert r['motivos_indeterminacao'] == {'sem_release_anterior': 1}
    assert len(r['entradas_sha256']) == 4
    saida = tmp_path / 'auditoria.json'
    args = [t for nome, p in zip(('cfr', 'compare', 'dataset', 'amostra', 'saida'), (*fontes, saida))
            for t in ('--' + nome, str(p))]
    assert main(args) == 0 and json.loads(saida.read_text()) == r
    args[-1] = str(fontes[0])
    with pytest.raises(ConfigError, match='sobrescrever'):
        main(args)


@pytest.mark.parametrize('csv', ['id,cfr_b\n2,0.5\n', 'id,cfr_b\n1,0.1\n',
                                'id,cfr_b\n1,\n', 'id,cfr_b\n1,0.5\n1,0.5\n'])
def test_populacao_valor_ou_ausencia_divergentes(fontes, csv):
    fontes[2].write_text(csv)
    with pytest.raises(ConfigError):
        auditar(*fontes)


def test_indeterminacao_sem_origem_nao_e_justificada(fontes):
    fontes[1].write_text(json.dumps({'repositorios': []}))
    with pytest.raises(ConfigError, match='não cobre'):
        auditar(*fontes)


def test_ausencias_concordantes_sao_validas(fontes):
    d = json.loads(fontes[0].read_text()); d['repositorios'][0]['change_failure_rate'] = None
    fontes[0].write_text(json.dumps(d)); fontes[2].write_text('id,cfr_b\n1,\n')
    assert auditar(*fontes)['comparacao_cfr_b_com_csv_final']['divergencias'] == 0
