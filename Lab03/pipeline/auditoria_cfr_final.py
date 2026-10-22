"""Confere CFR(b) contra o CSV e rastreia indeterminações nos compares publicados (#162)."""
import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path

from pipeline import consolidado
from pipeline.avaliacao_heuristica import exigir, identificador
from pipeline.cache import gravar_json


def auditar(cfr, compare, dataset, amostra):
    caminhos = [Path(p) for p in (cfr, compare, dataset, amostra)]
    hashes = {str(p): consolidado.sha256(p) for p in caminhos}
    dados = json.loads(caminhos[0].read_text(encoding='utf-8'))
    repos = dados['repositorios']
    ids = [identificador(r['id']) for r in repos]
    exigir(len(ids) == len(set(ids)), 'Repositório repetido no CFR.')
    with caminhos[2].open(encoding='utf-8', newline='') as f:
        linhas = list(csv.DictReader(f))
    csv_ids = [identificador(r['id']) for r in linhas]
    exigir(len(csv_ids) == len(set(csv_ids)) and set(csv_ids) == set(ids), 'População divergente no CSV.')
    valores = {r['id']: r['cfr_b'] for r in linhas}
    for r in repos:
        obtido = r['change_failure_rate']
        esperado = float(valores[str(r['id'])]) if valores[str(r['id'])] else None
        exigir((obtido is None and esperado is None) or
               (obtido is not None and esperado is not None and
                math.isclose(obtido, esperado, rel_tol=1e-12, abs_tol=1e-12)),
               f"CFR divergente no CSV: {r['id']}")
    ouro = json.loads(caminhos[3].read_text(encoding='utf-8'))
    # O manifesto oficial contém releases por repositório.
    pares = {(identificador(r['repo_id']), identificador(s['release_id']))
             for r in ouro['repositorios'] for s in r['releases']}
    desconhecidas = {(identificador(r['id']), identificador(s['release_id'])): (r, s)
                    for r in repos for s in r['releases'] if s['corretiva'] is None}
    registros, motivos_ignorados, vistos = [], Counter(), set()
    for r in consolidado.repositorios(compare):
        i = identificador(r['id'])
        exigir(i not in vistos, 'Compare de repositório repetido.')
        vistos.add(i)
        for c in r['comparacoes']:
            if c.get('ignorada'):
                motivos_ignorados[c.get('motivo')] += 1
            chave = (i, identificador(c['release']['id']))
            if chave in desconhecidas:
                repo, s = desconhecidas.pop(chave)
                registros.append({'repo_id': repo['id'], 'full_name': repo['full_name'],
                    'release_id': s['release_id'], 'tag_name': s['tag_name'],
                    'published_at': s['published_at'], 'release_anterior': c.get('release_anterior'),
                    'motivo': c.get('motivo'), 'detalhe': c.get('detalhe'),
                    'total_commits_coletados': c.get('total_commits_coletados'),
                    'na_amostra_ouro': chave in pares})
    exigir(vistos == set(ids) and not desconhecidas, 'Compare não cobre a população/indeterminações.')
    exigir(hashes == {str(p): consolidado.sha256(p) for p in caminhos}, 'Entrada alterada durante a auditoria.')
    return {'repositorios_processados': len(repos),
            'releases_processadas': sum(len(r['releases']) for r in repos),
            'releases_indeterminadas': len(registros),
            'motivos_indeterminacao': dict(Counter(r['motivo'] for r in registros)),
            'releases_ignoradas_compare_por_motivo': dict(motivos_ignorados),
            'indeterminadas': registros,
            'comparacao_cfr_b_com_csv_final': {'repositorios': len(repos), 'divergencias': 0,
                                             'tolerancia_absoluta_e_relativa': 1e-12},
            'entradas_sha256': hashes}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    for nome in ('cfr', 'compare', 'dataset', 'amostra', 'saida'):
        p.add_argument('--' + nome, required=True, type=Path)
    a = p.parse_args(argv)
    entradas = (a.cfr, a.compare, a.dataset, a.amostra)
    exigir(a.saida.resolve() not in {p.resolve() for p in entradas}, 'Saída não pode sobrescrever entrada.')
    relatorio = auditar(*entradas)
    gravar_json(a.saida, relatorio)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
