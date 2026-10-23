"""Compara os CSVs congelados da FIN-01/02, sem consultas à API."""
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import median

PASTA = Path(__file__).resolve().parent
METRICAS = (
    'freq_deploy_semana', 'lead_time_a_h', 'lead_time_b_h',
    'cfr_ci', 'cfr_entrega', 'recuperacao_h',
)
CLASSES = ('cls_freq', 'cls_lead_a', 'cls_cfr_ci', 'cls_recuperacao', 'classe_dora_c1')


def carregar(caminho):
    with caminho.open(encoding='utf-8-sig', newline='') as arquivo:
        linhas = list(csv.DictReader(arquivo))
    indice = {linha['repo'].casefold(): linha for linha in linhas}
    if len(indice) != len(linhas):
        raise ValueError(f'Repositórios duplicados: {caminho}')
    return indice


def numero(valor):
    if not valor.strip():
        return None
    resultado = float(valor)
    if not math.isfinite(resultado):
        raise ValueError(f'Valor não finito: {valor}')
    return resultado


def diferenca(publicado, replicado):
    if publicado is None or replicado is None:
        return None, 'ausente'
    if publicado == 0:
        return None, 'base_zero'
    return 100 * (replicado - publicado) / abs(publicado), 'calculada'


def main():
    fontes = {
        'publicado': PASTA / 'dataset_publicado.csv',
        'replicado': PASTA.parent / 'fin-01-execucao' / 'dataset_dora.csv',
    }
    publicado, replicado = (carregar(fontes[chave]) for chave in ('publicado', 'replicado'))
    comuns = sorted(publicado.keys() & replicado.keys())
    resumo = {
        'sha256': {chave: hashlib.sha256(path.read_bytes()).hexdigest() for chave, path in fontes.items()},
        'n_publicado': len(publicado), 'n_replicado': len(replicado), 'n_comuns': len(comuns),
        'ausentes_publicacao': [replicado[k]['repo'] for k in sorted(replicado.keys() - publicado.keys())],
        'metricas': {}, 'classes': {},
    }
    pares = []
    for metrica in METRICAS:
        relativos, absolutos = [], []
        iguais = ausentes = base_zero = 0
        for chave in comuns:
            pub, rep = (numero(origem[chave][metrica]) for origem in (publicado, replicado))
            relativo, motivo = diferenca(pub, rep)
            absoluto = None if pub is None or rep is None else rep - pub
            pares.append(dict(repo=replicado[chave]['repo'], metrica=metrica,
                              publicado=pub, replicado=rep, diferenca=absoluto,
                              diferenca_relativa_pct=relativo, situacao=motivo))
            if absoluto is None:
                ausentes += 1
                continue
            absolutos.append(absoluto)
            iguais += math.isclose(pub, rep, rel_tol=1e-9, abs_tol=1e-12)
            if relativo is None:
                base_zero += 1
            else:
                relativos.append(relativo)
        resumo['metricas'][metrica] = dict(
            n_validos=len(absolutos), n_iguais=iguais, n_ausentes=ausentes, n_base_zero=base_zero,
            mediana_diferenca=median(absolutos) if absolutos else None,
            n_relativos=len(relativos),
            mediana_diferenca_relativa_pct=median(relativos) if relativos else None,
            mediana_erro_relativo_absoluto_pct=median(map(abs, relativos)) if relativos else None,
            max_erro_relativo_absoluto_pct=max(map(abs, relativos), default=None),
        )
    for coluna in CLASSES:
        validos = [(publicado[k][coluna], replicado[k][coluna]) for k in comuns
                   if publicado[k][coluna].strip() and replicado[k][coluna].strip()]
        iguais = sum(a == b for a, b in validos)
        resumo['classes'][coluna] = dict(n_validos=len(validos), n_iguais=iguais,
                                        percentual=100 * iguais / len(validos) if validos else None)
    with (PASTA / 'diferencas_por_repositorio.csv').open('w', encoding='utf-8', newline='') as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(pares[0]))
        escritor.writeheader()
        escritor.writerows(pares)
    (PASTA / 'resumo.json').write_text(json.dumps(resumo, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(resumo, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
