"""Resume o piloto da #304 sem executar testes de hipótese ou alterar os dados brutos."""

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from experimento import config


def resumir(diretorio: Path) -> dict:
    diretorio = Path(diretorio)
    ambiente = json.loads((diretorio / "ambiente.json").read_text(encoding="utf-8"))
    execucao = json.loads((diretorio / "execucao.json").read_text(encoding="utf-8"))
    parametros = ambiente["experimento"]
    repeticoes = parametros["repeticoes"]
    if repeticoes < 2 or execucao["codigo_saida"] != 0:
        raise ValueError("O resumo exige piloto concluído com ao menos duas repetições.")
    with (diretorio / "resultados.csv").open(encoding="utf-8", newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo))
    esperado = Counter(
        (cfg.nome, carga.nome, r)
        for cfg, carga in config.combinacoes() for r in range(1, repeticoes + 1)
    )
    observado = Counter((l["configuracao"], l["carga"], int(l["repeticao"])) for l in linhas)
    if observado != esperado:
        raise ValueError("Combinações/repetições incompletas, duplicadas ou inesperadas.")
    combinacoes = len(config.combinacoes())
    aquecimentos = parametros["aquecimentos"]
    ordem = [int(l["ordem_execucao"]) for l in linhas]
    if ordem != list(range(combinacoes * aquecimentos + 1, combinacoes * (aquecimentos + repeticoes) + 1)):
        raise ValueError("Ordem inválida ou aquecimentos presentes no CSV.")
    grupos = defaultdict(list)
    for linha in linhas:
        tempo, vazao = float(linha["tempo_total_s"]), float(linha["vazao_ops_s"])
        carga = next(c for c in config.CARGAS if c.nome == linha["carga"])
        n = int(linha["n_operacoes"])
        if not (math.isfinite(tempo) and math.isfinite(vazao) and tempo > 0 and vazao > 0):
            raise ValueError("Tempo/vazão ausente, não finito ou não positivo.")
        if n != carga.n_operacoes or int(linha["n_leituras"]) != round(n * carga.fracao_leitura):
            raise ValueError("Contagens diferentes do protocolo.")
        if int(linha["n_escritas"]) != n - int(linha["n_leituras"]) or not math.isclose(vazao, n / tempo):
            raise ValueError("Contagem de escritas ou cálculo de vazão inconsistente.")
        if any(linha[k] != str(v) for k, v in ambiente.items() if k != "experimento"):
            raise ValueError("O ambiente do CSV difere do JSON.")
        grupos[(linha["configuracao"], linha["carga"])].append((tempo, vazao))
    resumos = []
    for (cfg, carga), valores in sorted(grupos.items()):
        tempos, vazoes = zip(*valores)
        q1, _, q3 = statistics.quantiles(tempos, n=4, method="inclusive")
        mediana = statistics.median(tempos)
        resumos.append({
            "configuracao": cfg, "carga": carga, "n": len(valores),
            "tempo_mediana_s": mediana,
            "tempo_q1_s": q1, "tempo_q3_s": q3, "tempo_iqr_s": q3 - q1,
            "tempo_iqr_relativo_pct": (q3 - q1) / mediana * 100,
            "tempo_media_s": statistics.mean(tempos),
            "tempo_desvio_padrao_s": statistics.stdev(tempos),
            "tempo_cv_pct": statistics.stdev(tempos) / statistics.mean(tempos) * 100,
            "tempo_min_s": min(tempos), "tempo_max_s": max(tempos),
            "vazao_mediana_ops_s": statistics.median(vazoes),
        })
    total_piloto = combinacoes * (repeticoes + aquecimentos)
    total_completa = config.total_execucoes()
    duracao = float(execucao["duracao_parede_s"])
    estimativa = duracao * total_completa / total_piloto
    return {
        "validacao": "aprovada", "medicoes": len(linhas),
        "execucoes_piloto_com_aquecimento": total_piloto,
        "execucoes_coleta_completa": total_completa,
        "duracao_parede_piloto_s": duracao,
        "soma_tempos_medidos_s": sum(float(l["tempo_total_s"]) for l in linhas),
        "estimativa_coleta_completa_s": estimativa,
        "reserva_operacional_s": estimativa * 2,
        "metodo_estimativa": "duração de parede do piloto × execuções completas / execuções do piloto; reserva de 2× não é intervalo de confiança",
        "quartis": "statistics.quantiles(method='inclusive')",
        "desvio_padrao": "amostral (n-1)",
        "sha256_entradas": {
            nome: hashlib.sha256((diretorio / nome).read_bytes()).hexdigest()
            for nome in ("resultados.csv", "ambiente.json", "execucao.json")
        },
        "grupos": resumos,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diretorio", type=Path, default=config.DIR_DADOS / "piloto")
    args = parser.parse_args()
    resumo = resumir(args.diretorio)
    (args.diretorio / "resumo.json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    with (args.diretorio / "resumo.csv").open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(resumo["grupos"][0]))
        escritor.writeheader()
        escritor.writerows(resumo["grupos"])
    print(json.dumps({k: v for k, v in resumo.items() if k != "grupos"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
