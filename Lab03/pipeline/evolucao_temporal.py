"""RQ08: evolução mensal da frequência de releases estáveis, sem API (#175)."""
import argparse
from collections import Counter
import csv
import datetime as dt
import hashlib
import io
import json
import math
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
DATASET = RAIZ / 'entregas/s02-03-dataset-500-final/dataset-500.csv'
EVENTOS = RAIZ / 'analise/dados/rq08_releases.csv'
COLUNAS_EVENTOS = ('repo_id', 'release_id', 'published_at')
COORTES = ('painel_inicial', 'painel_sem_alertas')


def data(texto):
    valor = dt.datetime.fromisoformat(texto.replace('Z', '+00:00'))
    if valor.tzinfo is None:
        raise ValueError('Data sem fuso horário')
    return valor.astimezone(dt.timezone.utc)


def iso(valor):
    return valor.isoformat().replace('+00:00', 'Z')


def sha(caminho):
    h = hashlib.sha256()
    with Path(caminho).open('rb') as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b''):
            h.update(bloco)
    return h.hexdigest()


def ler_populacao(caminho):
    """O CSV e o manifesto fixam IDs, janela, metadados e DF anual observada."""
    caminho = Path(caminho)
    manifesto = json.loads(caminho.with_name('manifesto.csv.json').read_text(encoding='utf-8'))
    if manifesto['contrato'] != 'lab03-dataset-v1' or sha(caminho) != manifesto['csv_sha256']:
        raise ValueError('Contrato ou hash do dataset divergente')
    with caminho.open(encoding='utf-8-sig', newline='') as f:
        linhas = list(csv.DictReader(f))
    if len(linhas) != manifesto['total_repositorios'] or not linhas:
        raise ValueError('População vazia ou quantidade divergente')
    inicio, fim = (data(manifesto['janela'][k]) for k in ('inicio', 'fim_exclusivo'))
    if fim <= inicio:
        raise ValueError('Janela inválida')
    vistos = set()
    for r in linhas:
        r['id'] = int(r['id'])
        if r['id'] <= 0 or r['id'] in vistos:
            raise ValueError('ID inválido ou duplicado')
        vistos.add(r['id'])
        if (data(r['janela_inicio']), data(r['janela_fim_exclusivo'])) != (inicio, fim):
            raise ValueError('Janela divergente no CSV')
        r['created_at'] = data(r['created_at'])
        r['deployment_frequency'] = float(r['deployment_frequency'])
        if not math.isfinite(r['deployment_frequency']) or r['deployment_frequency'] < 0:
            raise ValueError('Frequência inválida')
        for k in ('coleta_incompleta', 'calculo_parcial'):
            if r[k] not in ('true', 'false'):
                raise ValueError('Indicador de qualidade inválido')
            r[k] = r[k] == 'true'
    return linhas, inicio, fim


def csv_bytes(linhas, colunas):
    buffer = io.StringIO(newline='')
    w = csv.DictWriter(buffer, fieldnames=colunas, lineterminator='\n')
    w.writeheader()
    w.writerows(linhas)
    return buffer.getvalue().encode('utf-8')


def conferir_eventos(eventos, populacao, inicio, fim):
    """Recusa IDs/datas inválidos e reconcilia contagens com a DF dos 500."""
    ids = {r['id'] for r in populacao}
    vistos, contagens = set(), Counter()
    for e in eventos:
        i, rel = int(e['repo_id']), int(e['release_id'])
        if i not in ids or rel <= 0 or (i, rel) in vistos:
            raise ValueError('Evento com ID inválido, fora da população ou duplicado')
        if not inicio <= data(e['published_at']) < fim:
            raise ValueError('Evento fora da janela')
        vistos.add((i, rel))
        contagens[i] += 1
    semanas = (fim - inicio).total_seconds() / 604800
    for r in populacao:
        if not math.isclose(contagens[r['id']] / semanas, r['deployment_frequency'], rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError(f"Contagem de releases diverge da DF do CSV: {r['id']}")


def extrair(releases, dataset=DATASET, saida=EVENTOS):
    """Exporta só IDs e datas; notas/commits e a base original permanecem intactos."""
    releases, dataset, saida = map(Path, (releases, dataset, saida))
    manifesto_saida = saida.with_suffix('.json')
    if any(p.resolve() in {releases.resolve(), dataset.resolve(), dataset.with_name('manifesto.csv.json').resolve()}
           for p in (saida, manifesto_saida)):
        raise ValueError('A saída não pode sobrescrever uma entrada')
    populacao, inicio, fim = ler_populacao(dataset)
    fonte_bytes = releases.read_bytes()
    fonte = json.loads(fonte_bytes)
    if tuple(data(fonte['janela'][k]) for k in ('inicio', 'fim_exclusivo')) != (inicio, fim):
        raise ValueError('Janela divergente nas releases')
    ids = {r['id']: r['full_name'] for r in populacao}
    vistos, eventos, descartes = set(), {}, Counter()
    for repo in fonte['repositorios']:
        i = repo['id']
        if i not in ids:
            continue
        if i in vistos or repo['full_name'] != ids[i]:
            raise ValueError('Repositório repetido ou nome divergente')
        vistos.add(i)
        for rel in repo['releases']:
            if rel.get('draft') is not False or rel.get('prerelease') is not False:
                descartes['draft_ou_prerelease'] += 1
                continue
            publicada = data(rel['published_at'])
            if not inicio <= publicada < fim:
                descartes['fora_janela'] += 1
                continue
            if not isinstance(rel['id'], int) or isinstance(rel['id'], bool) or rel['id'] <= 0:
                raise ValueError('ID de release inválido')
            chave = (i, rel['id'])
            evento = dict(repo_id=i, release_id=rel['id'], published_at=iso(publicada))
            if chave in eventos:
                if eventos[chave] != evento:
                    raise ValueError('Release duplicada com data conflitante')
                descartes['duplicada_identica'] += 1
            eventos[chave] = evento
    if vistos != set(ids):
        raise ValueError('Repositórios da população ausentes na fonte')
    linhas = sorted(eventos.values(), key=lambda e: (e['repo_id'], e['published_at'], e['release_id']))
    conferir_eventos(linhas, populacao, inicio, fim)
    conteudo = csv_bytes(linhas, COLUNAS_EVENTOS)
    manifesto = {'issue': 175, 'escolha': 'evolucao_temporal_de_releases_estaveis',
                 'janela': {'inicio': iso(inicio), 'fim_exclusivo': iso(fim)},
                 'dataset_sha256': sha(dataset), 'releases_origem_sha256': hashlib.sha256(fonte_bytes).hexdigest(),
                 'eventos_sha256': hashlib.sha256(conteudo).hexdigest(), 'repositorios': len(ids),
                 'releases_estaveis': len(linhas), 'descartes': dict(descartes),
                 'reconciliacao_df': 'zero divergências por ID; contagem/semanas reais da janela',
                 'campos_publicados': list(COLUNAS_EVENTOS), 'consultas_api': 0}
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_bytes(conteudo)
    manifesto_saida.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2) + '\n',
                               encoding='utf-8', newline='\n')
    return manifesto


def meses(inicio, fim):
    atual, periodos = inicio, []
    while atual < fim:
        proximo = atual.replace(year=atual.year + (atual.month == 12), month=atual.month % 12 + 1,
                                day=1, hour=0, minute=0, second=0, microsecond=0)
        limite = min(proximo, fim)
        periodos.append((atual, limite))
        atual = limite
    return periodos


def analisar(eventos, populacao, inicio, fim):
    """Painel fixo de projetos existentes no início; zero só em meses observados."""
    conferir_eventos(eventos, populacao, inicio, fim)
    painel = [r for r in populacao if r['created_at'] <= inicio]
    if not painel:
        raise ValueError('Nenhum repositório existente no início da janela')
    bins = meses(inicio, fim)
    if len(bins) != 12:
        raise ValueError('A comparação semestral exige 12 meses civis na janela')
    contagens = Counter((int(e['repo_id']), data(e['published_at']).strftime('%Y-%m')) for e in eventos)
    linhas = []
    for r in painel:
        for a, b in bins:
            mes = a.strftime('%Y-%m')
            dias = (b - a).total_seconds() / 86400
            n = contagens[r['id'], mes]
            linhas.append(dict(repo_id=r['id'], full_name=r['full_name'], mes=mes, dias=dias,
                               releases=n, df_semana=n / (dias / 7),
                               sem_alertas=not r['coleta_incompleta'] and not r['calculo_parcial']))
    painel_df = pd.DataFrame(linhas)
    resumos, comparacoes = [], []
    for coorte in COORTES:
        grupo = painel_df if coorte == 'painel_inicial' else painel_df[painel_df['sem_alertas']]
        for (a, b) in bins:
            mes = a.strftime('%Y-%m')
            g = grupo[grupo['mes'] == mes]
            q = g['df_semana'].quantile([.25, .5, .75])
            resumos.append(dict(coorte=coorte, mes=mes, dias=(b-a).total_seconds()/86400, n=len(g),
                                releases=int(g['releases'].sum()), ativos=int((g['releases'] > 0).sum()),
                                mediana=q.loc[.5] if len(g) else None,
                                q1=q.loc[.25] if len(g) else None, q3=q.loc[.75] if len(g) else None,
                                media=g['df_semana'].mean() if len(g) else None))
        corte = bins[6][0]
        semanas_a, semanas_b = ((corte-inicio).total_seconds()/604800, (fim-corte).total_seconds()/604800)
        a = grupo[grupo['mes'] < corte.strftime('%Y-%m')].groupby('repo_id')['releases'].sum()/semanas_a
        b = grupo[grupo['mes'] >= corte.strftime('%Y-%m')].groupby('repo_id')['releases'].sum()/semanas_b
        diferencas = b-a
        iguais = diferencas.abs() <= 1e-12
        comparacoes.append(dict(coorte=coorte, n=len(a), semanas_primeiro=semanas_a,
                                semanas_segundo=semanas_b, mediana_primeiro=a.median() if len(a) else None,
                                mediana_segundo=b.median() if len(b) else None,
                                mediana_diferenca=diferencas.median() if len(a) else None,
                                aumentaram=int(((diferencas > 0) & ~iguais).sum()),
                                diminuiram=int(((diferencas < 0) & ~iguais).sum()), iguais=int(iguais.sum())))
    return painel_df, pd.DataFrame(resumos), pd.DataFrame(comparacoes)


def executar(eventos=EVENTOS, dataset=DATASET, saida=None):
    eventos, dataset = Path(eventos), Path(dataset)
    saida = Path(saida) if saida else RAIZ / 'analise/tabelas'
    if any(p.resolve().is_relative_to(saida.resolve()) for p in (eventos, dataset)):
        raise ValueError('Saída deve ser separada das entradas')
    populacao, inicio, fim = ler_populacao(dataset)
    meta = json.loads(eventos.with_suffix('.json').read_text(encoding='utf-8'))
    if meta['dataset_sha256'] != sha(dataset) or meta['eventos_sha256'] != sha(eventos):
        raise ValueError('Hashes de proveniência divergentes')
    if meta['janela'] != {'inicio': iso(inicio), 'fim_exclusivo': iso(fim)}:
        raise ValueError('Janela divergente no manifesto de eventos')
    with eventos.open(encoding='utf-8', newline='') as f:
        linhas = list(csv.DictReader(f))
    if len(linhas) != meta['releases_estaveis'] or len(populacao) != meta['repositorios']:
        raise ValueError('Contagens divergentes no manifesto de eventos')
    painel, mensal, semestres = analisar(linhas, populacao, inicio, fim)
    saida.mkdir(parents=True, exist_ok=True)
    for nome, df in [('rq08_painel_mensal.csv', painel), ('rq08_mensal.csv', mensal),
                     ('rq08_semestres.csv', semestres)]:
        df.to_csv(saida / nome, index=False, lineterminator='\n')
    resumo = {'escolha': 'evolucao_temporal', 'dataset_sha256': sha(dataset),
              'eventos_sha256': sha(eventos), 'janela': meta['janela'], 'populacao': len(populacao),
              'painel_inicial': int(painel['repo_id'].nunique()),
              'criados_apos_inicio_excluidos': len(populacao)-painel['repo_id'].nunique(),
              'painel_sem_alertas': int(painel[painel['sem_alertas']]['repo_id'].nunique()),
              'metodo': 'Releases estáveis por semana real do mês; painel fixo; quartis lineares. '
                        'Semestres pareados por ID com exposição real; análise descritiva, sem teste de tendência.',
              'limites': 'Seleção retrospectiva por popularidade e >=5 releases anuais; não representa todos os projetos. '
                         'Um ciclo anual não demonstra sazonalidade ou causalidade. Zero observado não prova ausência '
                         'de publicações omitidas pela fonte. Alertas de qualidade são gerais, não específicos de releases.'}
    # int do pandas/numpy é normalizado antes de serializar.
    resumo['criados_apos_inicio_excluidos'] = int(resumo['criados_apos_inicio_excluidos'])
    (saida / 'rq08_proveniencia.json').write_text(json.dumps(resumo, ensure_ascii=False, indent=2)+'\n',
                                                encoding='utf-8', newline='\n')
    return painel, mensal, semestres, resumo


MESES_PT = ('jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez')


def figura(mensal, destino):
    # Formato de artigo: largura de texto do SBC, tons de cinza como as demais
    # figuras, sem título interno (a legenda do LaTeX descreve a figura).
    import matplotlib.pyplot as plt
    with plt.rc_context({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False}):
        fig, ax = plt.subplots(figsize=(6.3, 2.35), layout='constrained')
        inicial = mensal[mensal['coorte'] == COORTES[0]]
        x = list(range(len(inicial)))
        ax.fill_between(x, inicial['q1'].astype(float), inicial['q3'].astype(float), color='#d9d9d9',
                        linewidth=0, label='IQR, painel inicial')
        estilos = {COORTES[0]: dict(color='#1a1a1a', linestyle='-', marker='o', markersize=4.5),
                   COORTES[1]: dict(color='#6e6e6e', linestyle='--', marker='o', markersize=4.5,
                                    markerfacecolor='white')}
        rotulos = {COORTES[0]: 'Mediana, painel inicial', COORTES[1]: 'Mediana, sem alertas'}
        for coorte in COORTES:
            d = mensal[mensal['coorte'] == coorte]
            ax.plot(x, d['mediana'].astype(float), linewidth=1.4,
                    label=f"{rotulos[coorte]} (n = {int(d['n'].iloc[0])})", **estilos[coorte])
        meses = [dt.date.fromisoformat(f'{m}-01') for m in inicial['mes']]
        ax.set_xticks(x, [MESES_PT[m.month - 1] + (f'\n{m.year}' if i == 0 or m.month == 1 else '')
                          for i, m in enumerate(meses)])
        ax.set_xlim(-0.4, len(x) - 0.6)
        ax.set_ylim(0, 1.3)
        ax.set_ylabel('Releases estáveis por semana')
        ax.yaxis.set_major_formatter(lambda v, _: f'{v:.1f}'.replace('.', ','))
        ax.grid(axis='y', color='#e6e6e6', linewidth=0.6)
        ax.set_axisbelow(True)
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.16), ncol=3, frameon=False, fontsize=8,
                  handlelength=2.2, columnspacing=1.2)
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(destino, dpi=300)
    return fig


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--releases', type=Path, help='Exporta datas do JSON local, sem executar o coletor')
    p.add_argument('--dataset', type=Path, default=DATASET)
    p.add_argument('--eventos', type=Path, default=EVENTOS)
    p.add_argument('--saida', type=Path)
    a = p.parse_args()
    if a.releases:
        print(json.dumps(extrair(a.releases, a.dataset, a.eventos), ensure_ascii=True))
    else:
        print(json.dumps(executar(a.eventos, a.dataset, a.saida)[3], ensure_ascii=True))


if __name__ == '__main__':
    main()
