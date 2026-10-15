import copy
import json
from pathlib import Path
import pytest
from pipeline import agendamento, integrado, auxiliar_compare as aux
from pipeline.cache import gravar_json
from pipeline.config import ConfigError, load_config


def test_libera_grandes_na_proxima_vaga_depois_do_minimo():
    total = [0]
    candidatos = [{"id": i} for i in range(1, 6)]
    politica = agendamento.validar({"liberar_adiados_com_elegiveis": 2, "adiados_ids": [2]}, candidatos)
    fila = agendamento.iterar(candidatos, politica, lambda: total[0])
    assert next(fila)["id"] == 1
    total[0] = 1
    assert next(fila)["id"] == 3
    total[0] = 2
    assert [c["id"] for c in fila] == [2, 4, 5]


def test_nao_libera_grandes_se_leves_nao_alcancam_minimo():
    assert [r["id"] for r in agendamento.iterar([{"id":1},{"id":2}],
        {"liberar_adiados_com_elegiveis":300,"adiados_ids":[2]}, lambda:299)] == [1]


def test_fila_aceita_iterador_sem_perder_adiados():
    assert [r['id'] for r in agendamento.iterar(iter([{'id':1},{'id':2}]),
        {'liberar_adiados_com_elegiveis':300,'adiados_ids':[2]},lambda:300)]==[2,1]


@pytest.mark.parametrize("politica", [
    {"liberar_adiados_com_elegiveis":True,"adiados_ids":[]},
    {"liberar_adiados_com_elegiveis":300,"adiados_ids":[9]},
    {"liberar_adiados_com_elegiveis":300,"adiados_ids":[1,1]},
])
def test_politica_invalida(politica):
    with pytest.raises(ConfigError):agendamento.validar(politica,[{"id":1}])


def test_pipeline_retomavel_com_grande_antes_dos_restantes_apos_minimo(tmp_path):
    from test_integrado import Api, configurar
    cfg, fonte = configurar(tmp_path,n=8)
    dados=json.loads(fonte.read_text())
    dados['agendamento']={'liberar_adiados_com_elegiveis':3,'adiados_ids':[1]}
    gravar_json(fonte,dados)
    api=Api()
    result=integrado.executar(cfg,api,alvo=5,max_candidatos=8,fonte=fonte)
    progresso=json.loads((Path(cfg['caminhos']['raw'])/'progresso.json').read_text())
    assert progresso['ids_avaliados']==[2,3,4,1,5]
    assert progresso['adiados_liberados']
    assert result['total_amostra_completa']==5
    assert result['agendamento']==dados['agendamento']
    class SemRede:
        def get(self,*args):pytest.fail('Checkpoint reconsultado')
        get_resposta=get
    again=integrado.executar(cfg,SemRede(),alvo=5,max_candidatos=8,fonte=fonte)
    assert again['total_amostra_completa']==5


def test_auxiliar_nao_antecipa_adiado_e_le_confirmados_por_id(tmp_path):
    from test_auxiliar_compare import configurar_futuros,checkpoint
    cfg, _, progresso=configurar_futuros(tmp_path)
    fonte=tmp_path/'fonte.json';dados=json.loads(fonte.read_text())
    dados['agendamento']={'liberar_adiados_com_elegiveis':3,'adiados_ids':[10]}
    gravar_json(fonte,dados)
    p=aux.Principal(cfg,fonte,relogio=lambda:1000)
    progresso['contexto']=copy.deepcopy(p.contexto)
    progresso['ids_avaliados']=[1,2]
    gravar_json(p.raw/'progresso.json',progresso)
    assert 10 not in [r['id'] for _,r in p.proximos()]
    with pytest.raises(aux.PausaAuxiliar):p.conferir_candidato(9)
    # Depois da liberação a ordem efetiva difere da posição no arquivo.
    progresso['elegiveis_com_coleta_completa']=3
    progresso['alvo']=5
    progresso['ids_avaliados']=[1,2,10]
    progresso['candidatos_avaliados']=3
    gravar_json(p.raw/'progresso.json',progresso)
    p.alvo=None
    checkpoint(p,1);checkpoint(p,2,False);checkpoint(p,10)
    assert {r['id'] for r in p.descobrir()}=={1,10}
