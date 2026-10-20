import copy
import hashlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
import requests

from pipeline import coleta_paralela as coleta, integrado
from pipeline.cache import gravar_json
from pipeline.concorrencia import mapear_concluidos
from pipeline.config import ConfigError, janela_utc
from pipeline.workflow_runs import _iso
from test_integrado import Api, configurar


def test_tokens_lidos_sem_executar_env_e_sem_expor_segredos(tmp_path):
    env = tmp_path / '.env'
    env.write_text('# comentario\nGITHUB_TOKEN_1="um"\nGITHUB_TOKEN_2=dois\nGITHUB_TOKEN_3=tres\n')
    assert coleta.ler_tokens(env, {}) == ['um', 'dois', 'tres']
    assert coleta.ler_tokens(env, {'GITHUB_TOKEN_1': 'outro'}) == ['outro', 'dois', 'tres']
    env.write_text('GITHUB_TOKEN_1=segredo\n')
    with pytest.raises(ConfigError, match='GITHUB_TOKEN_2') as erro:
        coleta.ler_tokens(env, {})
    assert 'segredo' not in str(erro.value)
    with pytest.raises(ConfigError, match='diferentes'):
        coleta.ler_tokens(env, {f'GITHUB_TOKEN_{i}': 'igual' for i in range(1, 4)})


def test_repositorio_lento_nao_bloqueia_novas_tarefas():
    liberar = threading.Event()
    def buscar(i):
        if i == 0:
            assert liberar.wait(5)
        return i
    try:
        with mapear_concluidos(buscar, range(5), 2) as resultados:
            assert [next(resultados) for _ in range(4)] == [1, 2, 3, 4]
            liberar.set()
            assert list(resultados) == [0]
    finally:
        liberar.set()


def test_fila_nao_ultrapassa_meta_com_conclusao_fora_de_ordem():
    restantes = 5
    feitas = []
    def buscar(i):
        feitas.append(i)
        return i
    with mapear_concluidos(buscar, range(100), 3, lambda: restantes) as registros:
        for _ in registros:
            restantes -= 1
            if not restantes:
                break
    assert sorted(feitas) == list(range(5))


class ClienteTeste(Api):
    paralelismo = 1
    def estatisticas(self):
        return {'requisicoes': len(self.chamadas), 'cache_hits': 0}
    def close(self):
        pass
    @property
    def controle(self):
        return self


def test_tres_tokens_sao_reservados_por_tarefa_e_devolvidos_apos_falha():
    pool = coleta.Sessoes([ClienteTeste() for _ in range(3)])
    barreira = threading.Barrier(3)
    def trabalhar(i):
        with pool.sessao({'full_name': str(i)}) as cliente:
            barreira.wait(timeout=5)
            assert len(pool.status()) == 3
            return id(cliente)
    with ThreadPoolExecutor(max_workers=3) as executor:
        assert len(set(executor.map(trabalhar, range(3)))) == 3
    with pytest.raises(RuntimeError):
        with pool.sessao({'full_name': 'falha'}):
            raise RuntimeError()
    assert pool.fila.qsize() == 3
    assert set(pool.status().values()) == {'livre'}


def test_integracao_tres_sessoes_reaproveita_coleta_e_compares_sem_api(tmp_path):
    config, fonte = configurar(tmp_path, 6)
    config['api']['repositorios_paralelos'] = 3
    clientes = [ClienteTeste() for _ in range(3)]
    resultado = integrado.executar(config, coleta.Sessoes(clientes), 5, 6, fonte)
    assert resultado['total_amostra_completa'] == 5
    assert resultado['total_comparacoes'] == 20
    assert integrado._ler(tmp_path / 'raw/progresso.json')['etapa'] == 'concluido'
    class SemRede(ClienteTeste):
        def get(self, *a, **k):
            raise AssertionError('checkpoint deveria dispensar a API')
        def get_resposta(self, *a, **k):
            raise AssertionError('compare deveria dispensar a API')
    retomada = integrado.executar(config, coleta.Sessoes([SemRede() for _ in range(3)]), 5, 6, fonte)
    assert retomada['total_amostra_completa'] == 5
    assert retomada['total_comparacoes'] == resultado['total_comparacoes']


def test_migracao_preserva_confirmados_remove_adiamento_e_valida_regras(tmp_path):
    config, original = configurar(tmp_path, 4)
    raw = tmp_path / 'raw'
    inicio, fim = janela_utc(config)
    antiga_fonte = tmp_path / 'antiga.json'
    gravar_json(antiga_fonte, {'agendamento': {'adiados_ids': [1]},
                             'candidatos': integrado._ler(original)['candidatos']})
    contexto = {'janela': {'inicio': _iso(inicio), 'fim_exclusivo': _iso(fim)},
        'inclusao': config['inclusao'], 'runs': config['runs'], 'api': config['api']['base_url'],
        'versao': 2, 'versao_coletor_runs': coleta.workflow_runs_completos.VERSAO_COLETOR,
        'fonte_sha256': hashlib.sha256(antiga_fonte.read_bytes()).hexdigest()}
    digest = hashlib.sha256(json.dumps(contexto, sort_keys=True).encode()).hexdigest()
    antigo = raw / 'checkpoints' / digest / '2.json'
    gravar_json(antigo, {'candidato': {'id': 2, 'full_name': 'org/repo2'}, 'elegivel': True})
    gravar_json(raw / 'progresso.json', {'contexto': contexto, 'ids_avaliados': [2]})
    fonte = coleta.preparar(config, original, antiga_fonte)
    dados = integrado._ler(fonte)
    assert [r['id'] for r in dados['candidatos']] == [2, 1, 3, 4]
    assert not dados.get('agendamento')
    manifesto = integrado._ler(raw / 'retomada-tres-sessoes/migracao.json')
    assert manifesto['elegiveis_reutilizaveis'] == 1
    from pathlib import Path
    assert (Path(manifesto['destino']) / '2.json').read_bytes() == antigo.read_bytes()
    invalida = copy.deepcopy(config)
    invalida['inclusao']['min_releases'] += 1
    with pytest.raises(ConfigError, match='incompatíveis'):
        coleta.preparar(invalida, original, antiga_fonte)


def test_queda_de_rede_retoma_e_fecha_clientes(tmp_path, monkeypatch):
    estado, fechados, tentativas, esperas = {}, [], [], []
    class Pool:
        def close(self):
            fechados.append(True)
    def executar(*args):
        tentativas.append(args)
        if len(tentativas) == 1:
            raise requests.ConnectionError('offline')
        return {'execucao_completa': True}
    monkeypatch.setattr(integrado, 'executar', executar)
    monkeypatch.setattr(coleta.time, 'sleep', esperas.append)
    assert coleta.executar_com_retomada({}, 'fonte', Pool, estado, lambda: None)['execucao_completa']
    assert len(tentativas) == len(fechados) == 2
    assert esperas == [5]
    assert tentativas[0][2:4] == (500, 100000)


def test_falha_autenticacao_nao_entra_em_loop_de_rede(monkeypatch):
    resposta = requests.Response()
    resposta.status_code = 401
    def autenticar():
        raise requests.HTTPError(response=resposta)
    with pytest.raises(requests.HTTPError):
        coleta.executar_com_retomada({}, 'fonte', autenticar, {}, lambda: None)


def test_403_por_cota_esgotada_retoma_sem_confundir_com_permissao(monkeypatch):
    resposta = requests.Response()
    resposta.status_code = 403
    resposta.headers['X-RateLimit-Remaining'] = '0'
    chamadas = []
    class Pool:
        def close(self):
            pass
    def executar(*args):
        chamadas.append(True)
        if len(chamadas) == 1:
            raise requests.HTTPError(response=resposta)
        return {'execucao_completa': True}
    monkeypatch.setattr(integrado, 'executar', executar)
    monkeypatch.setattr(coleta.time, 'sleep', lambda _: None)
    assert coleta.executar_com_retomada({}, 'fonte', Pool, {}, lambda: None)['execucao_completa']
    assert len(chamadas) == 2
    resposta.headers.clear()
    chamadas.clear()
    with pytest.raises(requests.HTTPError):
        coleta.executar_com_retomada({}, 'fonte', Pool, {}, lambda: None)
