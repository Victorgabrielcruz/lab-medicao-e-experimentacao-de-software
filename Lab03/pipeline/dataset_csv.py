"""Exportação CSV local e determinística do contrato lab03-dataset-v1 (#153)."""
import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
from pathlib import Path
from pipeline.config import ConfigError
from pipeline.metricas import METRICAS

CONTRATO = "lab03-dataset-v1"
METADADOS = ("id", "full_name", "estrelas", "linguagem", "created_at", "idade_dias", "idade_anos",
             "default_branch", "contribuidores", "contribuidores_obs", "coletado_em")
COLUNAS = ("id", "full_name", "janela_inicio", "janela_fim_exclusivo", *METADADOS[2:],
           *(c for m in METRICAS for c in (m, f"classe_{m}")),
           "coleta_incompleta", "calculo_parcial", "metricas_ausentes")
CLASSES = {"Elite", "High", "Medium", "Low"}

def exigir(condicao, mensagem):
    if not condicao:
        raise ConfigError(mensagem)

def timestamp(valor):
    exigir(isinstance(valor, str), "Timestamp ausente/invalido")
    try:
        data = dt.datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ConfigError("Timestamp invalido") from exc
    exigir(data.tzinfo is not None, "Timestamp sem fuso")
    return data.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")

def indice(lista):
    saida = {}
    for r in lista:
        i = r.get("id")
        exigir(isinstance(i, int) and not isinstance(i, bool) and i > 0, "ID invalido")
        exigir(i not in saida, f"ID duplicado: {i}")
        exigir(isinstance(r.get("full_name"), str) and "/" in r["full_name"], "Nome invalido")
        saida[i] = r
    return saida

def numero(v):
    return isinstance(v, (float, int)) and not isinstance(v, bool) and math.isfinite(v)

def montar_linhas(populacao, metadados, metricas):
    """A frequência define a população; nenhuma junção pode criar/perder IDs."""
    janela = metricas.get("janela")
    exigir(janela == populacao.get("janela"), "Janela divergente")
    inicio, fim = (timestamp(janela[k]) for k in ("inicio", "fim_exclusivo"))
    exigir(inicio < fim, "Janela invalida")
    p, m, r = (indice(d[chave]) for d, chave in ((populacao, "repositorios"),
                      (metadados, "repositorios"), (metricas, "repositorios")))
    exigir(set(p) == set(r), "Populacao/metrica divergente")
    exigir(set(p) <= set(m), "Metadados ausentes")
    linhas = []
    for i in sorted(p):
        meta, valores = m[i], r[i]
        exigir(p[i]["full_name"].lower() == meta["full_name"].lower() == valores["full_name"].lower(),
               f"Identidade divergente: {i}")
        exigir(not meta.get("contribuidores_pendentes"), f"Contribuidores pendentes: {i}")
        exigir(all(k in meta for k in METADADOS), f"Colunas de metadados ausentes: {i}")
        for k in ("estrelas", "idade_dias", "contribuidores"):
            v = meta[k]
            exigir(v is None and k == "contribuidores" or isinstance(v, int) and not isinstance(v, bool)
                   and v >= 0, f"Tipo/unidade invalido: {k}")
        exigir(numero(meta["idade_anos"]) and meta["idade_anos"] >= 0, "Idade invalida")
        exigir(isinstance(meta["default_branch"], str) and bool(meta["default_branch"]), "Branch invalida")
        for k in ("linguagem", "contribuidores_obs"):
            exigir(meta[k] is None or isinstance(meta[k], str), f"Texto invalido: {k}")
        linha = {k: meta[k] for k in METADADOS}
        linha.update(janela_inicio=inicio, janela_fim_exclusivo=fim)
        for k in ("created_at", "coletado_em"):
            linha[k] = timestamp(linha[k])
        for nome in METRICAS:
            exigir(nome in valores and f"classe_{nome}" in valores, f"Metrica ausente no contrato: {nome}")
            v, classe = valores[nome], valores[f"classe_{nome}"]
            exigir(v is None or numero(v) and v >= 0, f"Valor invalido: {nome}")
            exigir(v is None or not nome.startswith("cfr_") or v <= 1, "CFR fora de [0,1]")
            exigir((v is None and classe is None) or (v is not None and classe in CLASSES), "Classe invalida")
            linha[nome], linha[f"classe_{nome}"] = v, classe
        exigir(linha["deployment_frequency"] == p[i]["deployment_frequency"] and
               linha["classe_deployment_frequency"] == p[i]["classe"], "Frequencia divergente")
        for k in ("coleta_incompleta", "calculo_parcial"):
            exigir(isinstance(valores.get(k), bool), f"Indicador invalido: {k}")
            linha[k] = valores[k]
        ausentes = [nome for nome in METRICAS if linha[nome] is None]
        exigir(valores.get("metricas_ausentes") == ausentes, "Lista de nulos divergente")
        linha["metricas_ausentes"] = ausentes
        linhas.append(linha)
    return linhas

def serializar(linhas):
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=COLUNAS, lineterminator="\n")
    writer.writeheader()
    for linha in linhas:
        writer.writerow({k: ("" if v is None else str(v).lower() if isinstance(v, bool)
                         else json.dumps(v, ensure_ascii=False, separators=(",", ":")) if isinstance(v, list)
                         else v) for k, v in linha.items()})
    return buffer.getvalue().encode("utf-8")

def exportar(raw, processed, saida, manifesto):
    raw, processed, saida, manifesto = map(Path, (raw, processed, saida, manifesto))
    exigir(saida.resolve() != manifesto.resolve(), "CSV e manifesto devem ser diferentes")
    entradas = {"metadados.json": raw / "metadados.json", "deployment_frequency.json": processed / "deployment_frequency.json",
                "metricas.json": processed / "metricas.json"}
    for destino in (saida, manifesto):
        exigir(not any(destino.resolve().is_relative_to(p.resolve()) for p in (raw, processed)),
               "Exportacao deve ficar fora das pastas de entrada")
    dados_bytes = {k: p.read_bytes() for k, p in entradas.items()}
    dados = {k: json.loads(b) for k, b in dados_bytes.items()}
    linhas = montar_linhas(dados["deployment_frequency.json"], dados["metadados.json"], dados["metricas.json"])
    csv_bytes = serializar(linhas)
    hashes = {k: hashlib.sha256(b).hexdigest() for k, b in dados_bytes.items()}
    exigir(all(p.read_bytes() == dados_bytes[k] for k, p in entradas.items()), "Entradas mudaram durante exportacao")
    resumo = {"contrato": CONTRATO, "colunas": list(COLUNAS), "total_repositorios": len(linhas),
              "janela": dados["metricas.json"]["janela"], "entradas_sha256": hashes,
              "csv_sha256": hashlib.sha256(csv_bytes).hexdigest(), "ordem": "id crescente",
              "nulos": "celula vazia; zero observado preservado", "listas": "JSON",
              "metricas_disponiveis": {m: sum(l[m] is not None for l in linhas) for m in METRICAS},
              "coleta_incompleta": sum(l["coleta_incompleta"] for l in linhas),
              "calculo_parcial": sum(l["calculo_parcial"] for l in linhas)}
    for destino, conteudo in ((saida, csv_bytes), (manifesto, (json.dumps(resumo, ensure_ascii=False, indent=2)+"\n").encode("utf-8"))):
        destino.parent.mkdir(parents=True, exist_ok=True)
        temporario = destino.with_suffix(destino.suffix + ".tmp")
        temporario.write_bytes(conteudo)
        temporario.replace(destino)
    return resumo

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for nome in ("raw", "processed", "saida", "manifesto"):
        p.add_argument("--" + nome, required=True)
    args = p.parse_args()
    print(json.dumps(exportar(args.raw, args.processed, args.saida, args.manifesto), ensure_ascii=True))

if __name__ == "__main__":
    main()
