"""Consolida offline o corte publicado de 500, preservando lacunas (#151, #153)."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

from pipeline import auditoria, cfr_b, compare, consolidado, lead_time_commit, lead_time_release, metricas
from pipeline.amostra_encerrada import finalizar_funil
from pipeline.cache import gravar_json
from pipeline.classificacao import VERSAO_REFERENCIA, classificar_frequencia
from pipeline.config import janela_utc, load_config
from pipeline.dataset_csv import exigir, exportar, indice
from pipeline.funil import contar_releases, tabela_markdown


def executar(manifesto, raiz_dados, saida, entrega):
    manifesto, raiz_dados, saida, entrega = map(Path, (manifesto, raiz_dados, saida, entrega))
    original = manifesto.read_bytes()
    m = json.loads(original)
    pacote = next(p for p in m['pacotes'] if p['nome'] == 'snapshot-500')
    arquivos, usados = pacote['arquivos'], {}
    exigir(not saida.exists() and not entrega.exists(), 'Escolha pastas de saída novas')
    for destino in (saida, entrega):
        for pasta in ('raw/amostra-final-500', 'processed/amostra-final-500'):
            origem = (raiz_dados / pasta).resolve()
            exigir(not destino.resolve().is_relative_to(origem) and
                   not origem.is_relative_to(destino.resolve()), 'Saída invade a origem')
    exigir(not saida.resolve().is_relative_to(entrega.resolve()) and
           not entrega.resolve().is_relative_to(saida.resolve()), 'Saídas sobrepostas')

    def entrada(rel):
        caminho = raiz_dados / rel
        meta = arquivos[rel]
        h = consolidado.sha256(caminho)
        exigir((caminho.stat().st_size, h) in
               ((meta['bytes'], meta['sha256']), (meta.get('bytes_origem'), meta.get('sha256_origem'))),
               f'Entrada diverge do snapshot publicado: {rel}')
        usados[rel] = h
        return caminho

    def ler(rel):
        conteudo = entrada(rel).read_bytes()
        if usados[rel] != arquivos[rel]['sha256']:
            conteudo = re.sub(rb'(?:gh[pousr]_[A-Za-z0-9]{36,255}|github_pat_[A-Za-z0-9_]{60,255})',
                              b'[TOKEN_GITHUB_REMOVIDO]', conteudo)
            exigir(hashlib.sha256(conteudo).hexdigest() == arquivos[rel]['sha256'], 'Saneamento divergente')
        return json.loads(conteudo)

    prefixo = 'raw/amostra-final-500/'
    proc = 'processed/amostra-final-500/'
    progresso = ler(prefixo + 'progresso.json')
    ids = m['ids_amostra']
    exigir(len(ids) == len(set(ids)) == m['total_amostra'], 'População inválida')
    exigir(progresso['contexto'] == m['contexto'] and
           progresso['candidatos_avaliados'] == m['candidatos_avaliados'] and
           progresso['elegiveis_com_coleta_completa'] == len(ids), 'Progresso divergente')
    config = load_config(entrada(prefixo + 'config.yaml'))
    inicio, fim = janela_utc(config)
    janela = m['contexto']['janela']
    exigir(inicio.isoformat().replace('+00:00', 'Z') == janela['inicio'] and
           fim.isoformat().replace('+00:00', 'Z') == janela['fim_exclusivo'], 'Janela divergente')
    raw, processed = saida / 'raw', saida / 'processed'
    raw.mkdir(parents=True)
    processed.mkdir()
    config['caminhos'] = {'raw': str(raw), 'processed': str(processed), 'cache': str(saida / 'cache-nao-utilizado')}
    filtro = set(ids)
    fontes = {}
    for nome in ('metadados', 'releases'):
        itens = [r for r in consolidado.repositorios(entrada(prefixo + nome + '.json')) if r['id'] in filtro]
        exigir(set(indice(itens)) == filtro, f'População divergente: {nome}')
        fontes[nome] = indice(itens)
        gravar_json(raw / (nome + '.json'), {'janela': janela, 'repositorios': itens})
    for nome in ('cfr', 'tempo_recuperacao'):
        dados = ler(proc + nome + '.json')
        exigir(dados['janela'] == janela and set(indice(dados['repositorios'])) == filtro, 'Métrica divergente')
        shutil.copyfile(raiz_dados / (proc + nome + '.json'), processed / (nome + '.json'))
    audit = ler(proc + 'auditoria.json')
    exigir(audit['validado'] and audit['total_repositorios'] == len(ids), 'Auditoria inválida')
    exigir(consolidado.sha256(entrada(prefixo + 'amostra_workflow_runs.json')) == audit['entrada_sha256'],
           'Auditoria não corresponde aos runs publicados')
    f = finalizar_funil(ler(proc + 'funil.json'), ids)
    gravar_json(processed / 'funil.json', f)
    frequencias, compares, faltantes = [], [], []
    lt_a, lt_b, corretivas, auditorias_lt = [], [], [], []
    for i in ids:
        r = fontes['releases'][i]
        exigir(fontes['metadados'][i]['full_name'].lower() == r['full_name'].lower(), 'Identidade divergente')
        n = contar_releases(r, inicio, fim, False)['releases_publicadas']
        valor, classe = classificar_frequencia(n, inicio, fim)
        frequencias.append({'id': i, 'full_name': r['full_name'], 'releases_ano': n,
                            'releases_janela': n, 'deployment_frequency': valor, 'classe': classe})
        contexto = {'releases': r, 'janela': janela, 'api': m['contexto']['api'], 'versao_compare': 1}
        digest = hashlib.sha256(json.dumps(contexto, sort_keys=True).encode()).hexdigest()
        rel = prefixo + f'checkpoints/compare/{digest}/{i}.json'
        if rel in arquivos:
            cp = ler(rel)
            exigir(cp['id'] == i and cp['full_name'].lower() == r['full_name'].lower(), 'Compare divergente')
            # Cada compare é processado isoladamente para limitar memória.
            compare.gravar_consolidado(config, [cp], inicio, fim)
            a, resultados_a = lead_time_release.executar(config)
            _, resultados_b = lead_time_commit.executar(config)
            auditorias_lt.append(auditoria.validar_lead_time(config, raw / 'compare.json', a))
            lt_a.extend({k: v for k, v in item.items() if k != 'releases'} for item in resultados_a)
            lt_b.extend({k: v for k, v in item.items() if k != 'releases'} for item in resultados_b)
            corretiva = cfr_b.calcular_repositorio(r, inicio, fim, cp)
            compares.append(i)
        else:
            faltantes.append(i)
            corretiva = cfr_b.calcular_repositorio(r, inicio, fim)
        corretivas.append({k: v for k, v in corretiva.items() if k != 'releases'})
        if len(frequencias) % 50 == 0:
            print(f'Repositórios offline: {len(frequencias)}/{len(ids)}', flush=True)
    for nome, lista in (('lead_time_release', lt_a), ('lead_time_commit', lt_b), ('cfr_b', corretivas)):
        gravar_json(processed / (nome + '.json'), {'janela': janela, 'repositorios': lista,
            'versao_classificacao': VERSAO_REFERENCIA, 'resumo_sem_detalhes_por_release': True})
    gravar_json(processed / 'deployment_frequency.json', {'janela': janela,
        'versao_classificacao': VERSAO_REFERENCIA, 'repositorios': frequencias})
    caminho, _, _ = metricas.executar(config)
    dados = json.loads(caminho.read_text(encoding='utf-8'))
    for r in dados['repositorios']:
        if r['id'] in faltantes:
            exigir(r['lead_time_a'] is None and r['lead_time_b'] is None, 'Lead time sem compare')
            r.update(coleta_incompleta=True, calculo_parcial=True)
    dados['repositorios_com_coleta_incompleta'] = sum(r['coleta_incompleta'] for r in dados['repositorios'])
    dados['repositorios_com_calculo_parcial'] = sum(r['calculo_parcial'] for r in dados['repositorios'])
    gravar_json(caminho, dados)
    exigir(manifesto.read_bytes() == original, 'Manifesto modificado')
    for rel, esperado in usados.items():
        exigir(consolidado.sha256(raiz_dados / rel) == esperado, f'Entrada modificada: {rel}')
    resumo = exportar(raw, processed, entrega / 'dataset-500.csv', entrega / 'manifesto.csv.json')
    evidencia = {'capturado_em_utc': m['capturado_em_utc'], 'manifesto_origem_sha256': hashlib.sha256(original).hexdigest(),
        'entradas_sha256': usados, 'total_amostra': len(ids), 'candidatos_avaliados': m['candidatos_avaliados'],
        'novas_consultas_api': 0, 'processamento_final_completo': False, 'consolidacao_offline_completa': True,
        'repositorios_com_compare_local': len(compares), 'repositorios_sem_compare': len(faltantes),
        'auditoria_runs_publicada': audit, 'auditorias_lead_time_por_compare': auditorias_lt,
        'validacao_manual_cfr_b_pendente': True, 'exportacao': resumo}
    gravar_json(entrega / 'evidencias.json', evidencia)
    (entrega / 'funil.md').write_text(tabela_markdown(f), encoding='utf-8')
    print(json.dumps(resumo, ensure_ascii=False))
    return evidencia


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for nome in ('manifesto', 'raiz-dados', 'saida', 'entrega'):
        p.add_argument('--' + nome, required=True)
    args = p.parse_args()
    executar(args.manifesto, args.raiz_dados, args.saida, args.entrega)


if __name__ == '__main__':
    main()
