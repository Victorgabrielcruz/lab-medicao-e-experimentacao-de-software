import json
from pathlib import Path

import pytest

from pipeline import auditoria, consolidado, integrado
from pipeline.config import ConfigError
from test_integrado import Api, configurar


@pytest.mark.parametrize('streaming', [False, True])
def test_hash_semantico_preserva_contrato_ignora_so_instante(tmp_path, streaming):
    dados = {'gerado_em': 'ontem', 'janela': {'inicio': 'UTC'}, 'total': 2,
             'repositorios': [{'id': 2, 'nome': 'açúcar', 'nested': {'z': [1, None], 'a': True}}, {'id': 1}]}
    p = tmp_path / 'compare.json'
    if streaming:
        consolidado.gravar(p, {'gerado_em': dados['gerado_em'], 'janela': dados['janela']},
                           dados['repositorios'], {'total': 2})
    else:
        p.write_text(json.dumps(dados, indent=2), encoding='utf-8')
    esperado = auditoria.hash_compare(dados)
    assert auditoria.hash_compare_arquivo(p) == esperado
    dados['gerado_em'] = 'hoje'
    assert auditoria.hash_compare(dados) == esperado
    dados['repositorios'][0]['id'] = 42
    assert auditoria.hash_compare(dados) != esperado


def test_integrado_e_retomada_nao_leem_compares_inteiros(tmp_path, monkeypatch):
    cfg, fonte = configurar(tmp_path, n=3)
    proibidos = {tmp_path / 'raw/compare.json', tmp_path / 'processed/lead_time_commit.json'}
    original = Path.read_text
    def ler(path, *args, **kwargs):
        assert path not in proibidos, 'Consolidado inteiro carregado em memória'
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'read_text', ler)
    primeiro = integrado.executar(cfg, Api(), 3, 3, fonte)
    assert primeiro['execucao_completa'] and primeiro['repositorios_com_lead_time_release'] == 3
    api = Api(falhar=1)
    segundo = integrado.executar(cfg, api, 3, 3, fonte)
    assert segundo['execucao_completa'] and api.chamadas == []
    # O retorno resumido mantém no disco todos os intervalos por release/commit.
    with (tmp_path / 'processed/lead_time_commit.json').open(encoding='utf-8') as f:
        metricas = json.load(f)
    assert len(metricas['repositorios']) == 3
    assert all(r['releases'] for r in metricas['repositorios'])
    lt = tmp_path / 'processed/lead_time_release.json'
    dados = json.loads(original(lt, encoding='utf-8'))
    dados['repositorios'][0]['lead_time_horas'] = 999
    lt.write_text(json.dumps(dados), encoding='utf-8')
    with pytest.raises(ConfigError, match='mediana'):
        auditoria.validar_lead_time(cfg, tmp_path / 'raw/compare.json', lt)
