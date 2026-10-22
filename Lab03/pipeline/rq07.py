"""Combinações operacionais e classificação da RQ07, offline (#173)."""

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
from collections import Counter
from dataclasses import replace
from pathlib import Path

from pipeline.classificacao import CLASSES, REFERENCIA, VERSAO_REFERENCIA, classificar

RAIZ = Path(__file__).resolve().parents[1]
DATASET = RAIZ / "entregas/s02-03-dataset-500-final/dataset-500.csv"
SAIDA = RAIZ / "analise/rq07"
COMBINACOES = {
    "C1": {"deployment_frequency": "deployment_frequency", "lead_time": "lead_time_b",
           "change_failure_rate": "cfr_a", "tempo_recuperacao": "tempo_recuperacao"},
    "C2": {"deployment_frequency": "deployment_frequency", "lead_time": "lead_time_a",
           "change_failure_rate": "cfr_a", "tempo_recuperacao": "tempo_recuperacao"},
    "C3": {"deployment_frequency": "deployment_frequency", "lead_time": "lead_time_b",
           "change_failure_rate": "cfr_b", "tempo_recuperacao": "tempo_recuperacao"},
}
FONTES = tuple(dict.fromkeys(c for m in COMBINACOES.values() for c in m.values()))
METRICAS = tuple(REFERENCIA)
COLUNAS = ("id", "full_name", "combinacao", "coleta_incompleta", "calculo_parcial",
           "metricas_disponiveis", "completa", *METRICAS,
           *(f"classe_{m}" for m in METRICAS), "geral")


def numero(texto):
    if texto == "":
        return None
    valor = float(texto)
    if not math.isfinite(valor) or valor < 0:
        raise ValueError(f"Valor inválido: {texto!r}")
    return valor


def booleano(texto):
    if texto not in ("true", "false"):
        raise ValueError(f"Booleano inválido: {texto!r}")
    return texto == "true"


def referencia_janela(inicio, fim):
    datas = [dt.datetime.fromisoformat(t.replace("Z", "+00:00")) for t in (inicio, fim)]
    if any(d.tzinfo is None for d in datas):
        raise ValueError("Janela sem fuso horário")
    semanas = (datas[1] - datas[0]).total_seconds() / 604800
    if semanas <= 0:
        raise ValueError("Janela deve ter duração positiva")
    return REFERENCIA | {"deployment_frequency": replace(REFERENCIA["deployment_frequency"],
                                                         medium=12 / semanas)}


def classificar_linhas(linhas):
    """Recalcula as classes, preserva ausências e identifica notas parciais."""
    resultado, ids, janela = [], set(), None
    for linha in linhas:
        identificador = int(linha["id"])
        if identificador <= 0 or identificador in ids:
            raise ValueError(f"ID inválido ou duplicado: {identificador}")
        ids.add(identificador)
        atual = (linha["janela_inicio"], linha["janela_fim_exclusivo"])
        if janela is not None and atual != janela:
            raise ValueError("Janelas divergentes no dataset")
        janela = atual
        referencia = referencia_janela(*janela)
        valores = {c: numero(linha[c]) for c in FONTES}
        qualidade = {c: booleano(linha[c]) for c in ("coleta_incompleta", "calculo_parcial")}
        for nome, fontes in COMBINACOES.items():
            entradas = {m: valores[c] for m, c in fontes.items()}
            classes = classificar(entradas, referencia)
            # O contrato CSV inclui classes por variante; divergência exige revisão da fonte.
            for metrica, fonte in fontes.items():
                if (linha[f"classe_{fonte}"] or None) != classes[metrica]:
                    raise ValueError(f"Classe divergente do contrato: {identificador}, {fonte}")
            n = sum(v is not None for v in entradas.values())
            resultado.append({"id": identificador, "full_name": linha["full_name"],
                              "combinacao": nome, **qualidade, "metricas_disponiveis": n,
                              "completa": n == len(METRICAS), **entradas,
                              **{f"classe_{m}": classes[m] for m in METRICAS},
                              "geral": classes["geral"]})
    if not resultado:
        raise ValueError("Dataset vazio")
    return sorted(resultado, key=lambda r: (r["id"], r["combinacao"]))


def distribuicoes(linhas):
    saida = {}
    for c in COMBINACOES:
        grupo = [r for r in linhas if r["combinacao"] == c]
        saida[c] = {"repositorios": len(grupo), "completos": sum(r["completa"] for r in grupo)}
        for coluna in (*[f"classe_{m}" for m in METRICAS], "geral"):
            contagens = Counter(r[coluna] for r in grupo)
            saida[c][coluna] = {**{k: contagens[k] for k in CLASSES}, "ausentes": contagens[None]}
    return saida


def gravar_csv(caminho, linhas, colunas):
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=colunas, lineterminator="\n")
        writer.writeheader()
        for linha in linhas:
            writer.writerow({k: str(v).lower() if isinstance(v, bool) else v for k, v in linha.items()})


def executar(dataset=DATASET, saida=SAIDA):
    dataset, saida = Path(dataset), Path(saida)
    if dataset.resolve().is_relative_to(saida.resolve()):
        raise ValueError("A saída deve ser separada do dataset de entrada")
    conteudo = dataset.read_bytes()
    manifesto_caminho = dataset.with_name("manifesto.csv.json")
    manifesto = json.loads(manifesto_caminho.read_text(encoding="utf-8"))
    sha = hashlib.sha256(conteudo).hexdigest()
    if manifesto.get("contrato") != "lab03-dataset-v1" or manifesto.get("csv_sha256") != sha:
        raise ValueError("Contrato ou SHA-256 do dataset divergente do manifesto")
    fonte = list(csv.DictReader(io.StringIO(conteudo.decode("utf-8-sig"))))
    if len(fonte) != manifesto["total_repositorios"]:
        raise ValueError("Quantidade de repositórios divergente do manifesto")
    linhas = classificar_linhas(fonte)
    janela = {"inicio": fonte[0]["janela_inicio"], "fim_exclusivo": fonte[0]["janela_fim_exclusivo"]}
    if janela != manifesto["janela"]:
        raise ValueError("Janela divergente do manifesto")
    resumo = {"issue": 173, "contrato_classificacao": VERSAO_REFERENCIA,
              "dataset_sha256": sha, "manifesto_sha256": hashlib.sha256(manifesto_caminho.read_bytes()).hexdigest(),
              "janela": janela, "combinacoes": COMBINACOES, "distribuicoes": distribuicoes(linhas),
              "limites": ["#162 encerrada com avaliação publicada parcial (146/300); conferência final local: "
                          "296/300 e quatro previsões indeterminadas. C3 mantém essa limitação de validade.",
                          "Nota geral ignora métricas ausentes; completa distingue notas de quatro métricas.",
                          "DF estável e recuperação fixas; pré-releases e tags fora destas três combinações."]}
    saida.mkdir(parents=True, exist_ok=True)
    gravar_csv(saida / "classificacoes.csv", linhas, COLUNAS)
    (saida / "combinacoes.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2) + "\n",
                                          encoding="utf-8", newline="\n")
    return resumo


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", type=Path, default=DATASET)
    p.add_argument("--saida", type=Path, default=SAIDA)
    args = p.parse_args()
    print(json.dumps(executar(args.dataset, args.saida), ensure_ascii=True))


if __name__ == "__main__":
    main()
