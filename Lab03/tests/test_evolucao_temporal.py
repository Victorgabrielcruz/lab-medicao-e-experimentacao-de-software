import csv
import json

import pandas as pd
import pytest

from pipeline import evolucao_temporal as mod

INICIO = '2025-10-01T00:00:00Z'
FIM = '2026-10-01T00:00:00Z'


@pytest.fixture
def fontes(tmp_path):
    pasta = tmp_path / 'fonte'
    pasta.mkdir()
    dataset = pasta / 'dataset.csv'
    janela = dict(inicio=INICIO, fim_exclusivo=FIM)
    def rel(i, publicada, **kw):
        return dict(id=i, published_at=publicada, draft=False, prerelease=False, **kw)
    rs = [dict(id=1, full_name='org/um', releases=[
        rel(11, INICIO), rel(12, '2026-02-01T00:30:00+01:00'),
        rel(13, '2026-03-31T23:59:59Z'), rel(14, '2026-04-01T00:00:00Z'),
        rel(15, '2026-09-30T23:59:59Z')]),
        dict(id=2, full_name='org/dois', releases=[rel(21, '2026-09-01T00:00:00Z')]),
        dict(id=3, full_name='org/novo', releases=[rel(31, '2026-05-01T00:00:00Z')])]
    rows = [dict(id=r['id'], full_name=r['full_name'], janela_inicio=INICIO,
                 janela_fim_exclusivo=FIM, created_at='2026-05-01T00:00:00Z' if r['id']==3 else '2020-01-01T00:00:00Z',
                 deployment_frequency=len(r['releases'])/(365/7), coleta_incompleta='false',
                 calculo_parcial='true' if r['id']==2 else 'false') for r in rs]
    dataset.write_bytes(mod.csv_bytes(rows, rows[0].keys()))
    manifesto = dict(contrato='lab03-dataset-v1', csv_sha256=mod.sha(dataset),
                     total_repositorios=3, janela=janela)
    dataset.with_name('manifesto.csv.json').write_text(json.dumps(manifesto), encoding='utf-8')
    releases = pasta / 'releases.json'
    releases.write_text(json.dumps(dict(janela=janela, repositorios=rs)), encoding='utf-8')
    eventos = tmp_path / 'dados/eventos.csv'
    return dataset, releases, eventos


def test_extrai_publica_minimo_e_reconcilia_todos_os_ids(fontes):
    dataset, releases, eventos = fontes
    m = mod.extrair(releases, dataset, eventos)
    assert m['releases_estaveis'] == 7 and m['repositorios'] == 3
    assert m['campos_publicados'] == list(mod.COLUNAS_EVENTOS)
    assert mod.sha(eventos) == m['eventos_sha256']
    assert 'body' not in eventos.read_text(encoding='utf-8')


def test_zeros_painel_fixo_conversao_utc_e_dias_reais(fontes, tmp_path):
    dataset, releases, eventos = fontes
    mod.extrair(releases, dataset, eventos)
    p, mensal, semestres, meta = mod.executar(eventos, dataset, tmp_path/'saida')
    assert len(p) == 24 and set(p['repo_id']) == {1, 2}  # o projeto novo não recebe zeros antes de existir
    assert meta['criados_apos_inicio_excluidos'] == 1
    assert meta['painel_inicial'] == 2 and meta['painel_sem_alertas'] == 1
    r = p[p['repo_id']==1].set_index('mes')
    assert r.loc['2026-01','releases'] == 1  # offset desloca a publicação para janeiro em UTC
    assert r.loc['2026-02','dias'] == 28
    assert r.loc['2026-02','releases'] == r.loc['2026-02','df_semana'] == 0
    assert r.loc['2025-10','df_semana'] == pytest.approx(7/31)
    assert r.loc['2026-04','df_semana'] == pytest.approx(7/30)
    assert set(mensal[mensal['coorte']=='painel_inicial']['n']) == {2}
    assert semestres['semanas_primeiro'].tolist() == [26, 26]
    assert semestres['semanas_segundo'].tolist() == pytest.approx([183/7, 183/7])
    assert (semestres['aumentaram'] + semestres['diminuiram'] + semestres['iguais']).tolist() == [2,1]


def test_filtros_deduplicacao_e_limites_da_janela(fontes):
    dataset, releases, eventos = fontes
    d = json.loads(releases.read_text(encoding='utf-8'))
    rs = d['repositorios'][0]['releases']
    rs += [dict(rs[0]), dict(id=90, draft=True, prerelease=False, published_at=None),
           dict(id=91, draft=False, prerelease=True, published_at=INICIO),
           dict(id=92, draft=False, prerelease=False, published_at=FIM)]
    releases.write_text(json.dumps(d), encoding='utf-8')
    m = mod.extrair(releases, dataset, eventos)
    assert m['releases_estaveis'] == 7
    assert m['descartes'] == dict(duplicada_identica=1, draft_ou_prerelease=2, fora_janela=1)


@pytest.mark.parametrize('erro', ['nome', 'duplicado', 'data_conflitante', 'repo_ausente', 'contagem', 'janela'])
def test_recusa_fonte_inconsistente_sem_publicar(fontes, erro):
    dataset, releases, eventos = fontes
    d = json.loads(releases.read_text(encoding='utf-8'))
    r = d['repositorios'][0]
    if erro == 'nome': r['full_name'] = 'org/errado'
    if erro == 'duplicado': d['repositorios'].append(r)
    if erro == 'data_conflitante': r['releases'].append(dict(r['releases'][0], published_at='2025-10-02T00:00:00Z'))
    if erro == 'repo_ausente': d['repositorios'].pop()
    if erro == 'contagem': r['releases'].pop()
    if erro == 'janela': d['janela']['inicio'] = '2025-09-01T00:00:00Z'
    releases.write_text(json.dumps(d), encoding='utf-8')
    with pytest.raises(ValueError):
        mod.extrair(releases, dataset, eventos)
    assert not eventos.exists()


def test_hashes_obrigatorios_e_saida_separada(fontes, tmp_path):
    dataset, releases, eventos = fontes
    with pytest.raises(ValueError, match='sobrescrever'):
        mod.extrair(releases, dataset, releases)
    mod.extrair(releases, dataset, eventos)
    with pytest.raises(ValueError, match='separada'):
        mod.executar(eventos, dataset, eventos.parent)
    eventos.write_bytes(eventos.read_bytes() + b'\n')
    with pytest.raises(ValueError, match='Hashes'):
        mod.executar(eventos, dataset, tmp_path/'saida')


def test_duplicados_e_datas_invalidas_na_analise(fontes):
    dataset, releases, eventos = fontes
    mod.extrair(releases, dataset, eventos)
    pop, a, b = mod.ler_populacao(dataset)
    with eventos.open(encoding='utf-8', newline='') as f:
        evs = list(csv.DictReader(f))
    with pytest.raises(ValueError, match='duplicado'):
        mod.analisar(evs + [evs[0]], pop, a, b)
    evs[0]['published_at'] = FIM
    with pytest.raises(ValueError, match='janela'):
        mod.analisar(evs, pop, a, b)
    with pytest.raises(ValueError, match='fuso'):
        mod.data('2025-10-01T00:00:00')


def test_painel_sem_alertas_vazio_e_estimativas_ausentes(fontes, tmp_path):
    dataset, releases, eventos = fontes
    mod.extrair(releases, dataset, eventos)
    pop, a, b = mod.ler_populacao(dataset)
    for r in pop: r['calculo_parcial'] = True
    with eventos.open(encoding='utf-8', newline='') as f:
        evs = list(csv.DictReader(f))
    _, mensal, semestres = mod.analisar(evs, pop, a, b)
    assert mensal[mensal['coorte']=='painel_sem_alertas']['mediana'].isna().all()
    assert semestres.loc[1,'n'] == 0 and pd.isna(semestres.loc[1,'mediana_segundo'])


def test_reproducao_preserva_entradas_e_gera_bytes_identicos(fontes, tmp_path):
    dataset, releases, eventos = fontes
    antes = {p: p.read_bytes() for p in (dataset, releases)}
    mod.extrair(releases, dataset, eventos)
    a, b = tmp_path/'a', tmp_path/'b'
    mod.executar(eventos, dataset, a)
    mod.executar(eventos, dataset, b)
    for p in a.iterdir(): assert p.read_bytes() == (b/p.name).read_bytes()
    assert all(p.read_bytes() == v for p,v in antes.items())


def test_mes_parcial_e_ano_bissexto():
    bins = mod.meses(mod.data('2024-02-15T00:00:00Z'), mod.data('2024-03-01T00:00:00Z'))
    assert len(bins) == 1 and (bins[0][1]-bins[0][0]).days == 15


@pytest.mark.parametrize('campo,valor', [('dataset_sha256','errado'), ('releases_estaveis',8),
                                       ('repositorios',4), ('janela',dict(inicio=FIM, fim_exclusivo=FIM))])
def test_manifesto_de_eventos_inconsistente_e_recusado(fontes, tmp_path, campo, valor):
    dataset, releases, eventos = fontes
    mod.extrair(releases, dataset, eventos)
    p = eventos.with_suffix('.json')
    m = json.loads(p.read_text(encoding='utf-8')); m[campo] = valor
    p.write_text(json.dumps(m), encoding='utf-8')
    with pytest.raises(ValueError):
        mod.executar(eventos, dataset, tmp_path/'saida')
    assert not (tmp_path/'saida').exists()


def test_coorte_sem_projetos_existentes_e_recusada(fontes):
    dataset, releases, eventos = fontes
    mod.extrair(releases, dataset, eventos)
    pop, a, b = mod.ler_populacao(dataset)
    for r in pop: r['created_at'] = mod.data('2026-05-01T00:00:00Z')
    with eventos.open(encoding='utf-8', newline='') as f:
        evs = list(csv.DictReader(f))
    with pytest.raises(ValueError, match='Nenhum'):
        mod.analisar(evs, pop, a, b)


def test_cli_exporta_e_analisa_sem_rede(fontes, tmp_path, monkeypatch, capsys):
    import sys
    dataset, releases, eventos = fontes
    monkeypatch.setattr('requests.sessions.Session.request', lambda *a, **k: pytest.fail('Acesso à rede'))
    args = ['--dataset', str(dataset), '--eventos', str(eventos)]
    monkeypatch.setattr(sys, 'argv', ['evolucao_temporal', *args, '--releases', str(releases)])
    mod.main()
    assert json.loads(capsys.readouterr().out)['consultas_api'] == 0
    monkeypatch.setattr(sys, 'argv', ['evolucao_temporal', *args, '--saida', str(tmp_path/'saida')])
    mod.main()
    assert json.loads(capsys.readouterr().out)['painel_inicial'] == 2
