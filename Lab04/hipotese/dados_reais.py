"""Prepara a amostra congelada de CI e suas estatísticas descritivas (#263).

Execute em Lab04: ``python -m hipotese.dados_reais``. Não acessa a rede.
"""

from collections import Counter
import csv
from datetime import datetime
import json
from pathlib import Path

from scipy.stats import binomtest

from hipotese.config import META_TAXA_FALHA

PASTA_DADOS = Path(__file__).resolve().parents[1] / "data"
COLUNAS = (
    "run_id", "workflow", "branch", "evento", "conclusao", "criado_em", "url", "falhou"
)
CONCLUSOES_VALIDAS = {"success", "failure"}


def selecionar_execucoes(snapshot: dict) -> tuple[list[dict], dict[str, int]]:
    """Valida a origem, remove descartes e ordena por criação e ID."""
    execucoes = snapshot["execucoes"]
    ids = [run["id"] for run in execucoes]
    if len(ids) != len(set(ids)):
        raise ValueError("O snapshot contém run_id duplicado.")
    if len(execucoes) != snapshot["limite_execucoes"]:
        raise ValueError("O snapshot não contém a janela de coleta completa.")
    if sum(pagina["quantidade"] for pagina in snapshot["paginas"]) != len(execucoes):
        raise ValueError("A contagem das páginas difere da quantidade de execuções.")

    corte = datetime.fromisoformat(snapshot["corte_criado_em_utc"])
    linhas = []
    descartes = Counter()
    for run in sorted(execucoes, key=lambda r: (r["created_at"], r["id"])):
        origem = (
            run["workflow_id"], run["name"], run["head_branch"],
            run["event"], run["head_repository"],
        )
        esperada = (
            snapshot["workflow_id"], snapshot["workflow"], snapshot["branch"],
            snapshot["evento"], snapshot["repositorio"],
        )
        if origem != esperada:
            raise ValueError(f"Execução {run['id']} fora do workflow/branch/evento/repositório.")
        if datetime.fromisoformat(run["created_at"]) > corte:
            raise ValueError(f"Execução {run['id']} posterior ao corte.")
        conclusao = run["conclusion"]
        if run["status"] != "completed" or conclusao not in CONCLUSOES_VALIDAS:
            descartes[conclusao or run["status"]] += 1
            continue
        linhas.append({
            "run_id": run["id"],
            "workflow": run["name"],
            "branch": run["head_branch"],
            "evento": run["event"],
            "conclusao": conclusao,
            "criado_em": run["created_at"],
            "url": run["html_url"],
            "falhou": int(conclusao == "failure"),
        })
    if not linhas:
        raise ValueError("Nenhuma execução com conclusão success/failure.")
    return linhas, dict(sorted(descartes.items()))


def resumir_amostra(linhas: list[dict]) -> dict:
    """IC de Wilson de 95% e ACF amostral de lag 1, sem ajuste por n-k."""
    if not linhas:
        raise ValueError("A amostra não pode ser vazia.")
    valores = [linha["falhou"] for linha in linhas]
    if any(valor not in (0, 1) for valor in valores):
        raise ValueError("Cada observação deve ser binária (0 ou 1).")
    n = len(valores)
    falhas = sum(valores)
    taxa = falhas / n
    intervalo = binomtest(falhas, n).proportion_ci(confidence_level=0.95, method="wilson")

    maior_sequencia = atual = 0
    for valor in valores:
        atual = atual + 1 if valor else 0
        maior_sequencia = max(maior_sequencia, atual)
    denominador = sum((valor - taxa) ** 2 for valor in valores)
    numerador = sum((a - taxa) * (b - taxa) for a, b in zip(valores, valores[1:]))
    lag1 = numerador / denominador if denominador else None
    transicoes = Counter(zip(valores, valores[1:]))
    pares = {f"{a}{b}": transicoes[a, b] for a in (0, 1) for b in (0, 1)}

    def probabilidade_apos(anterior: int) -> float | None:
        total = transicoes[anterior, 0] + transicoes[anterior, 1]
        return transicoes[anterior, 1] / total if total else None

    return {
        "n_execucoes": n,
        "n_sucessos": n - falhas,
        "n_falhas": falhas,
        "taxa_falha": taxa,
        "meta_taxa_falha": META_TAXA_FALHA,
        "ic_taxa_falha": {
            "metodo": "Wilson, sem correção de continuidade",
            "nivel": 0.95,
            "inferior": float(intervalo.low),
            "superior": float(intervalo.high),
        },
        "maior_sequencia_falhas": maior_sequencia,
        "autocorrelacao_lag1": lag1,
        "transicoes": pares,
        "p_falha_apos_sucesso": probabilidade_apos(0),
        "p_falha_apos_falha": probabilidade_apos(1),
    }


def gerar_artefatos(pasta: Path = PASTA_DADOS) -> dict:
    """Recria CSV e resumo usando somente o snapshot versionado."""
    snapshot = json.loads((pasta / "ci_pytest_snapshot.json").read_text(encoding="utf-8"))
    linhas, descartes = selecionar_execucoes(snapshot)
    # Aqui um descarte interrompe a sequência; na amostra filtrada ele é removido.
    maior_sem_descartes = atual = 0
    for run in sorted(snapshot["execucoes"], key=lambda r: (r["created_at"], r["id"])):
        falhou = run["status"] == "completed" and run["conclusion"] == "failure"
        atual = atual + 1 if falhou else 0
        maior_sem_descartes = max(maior_sem_descartes, atual)
    resumo = {
        "issue": 263,
        "repositorio": snapshot["repositorio"],
        "workflow": snapshot["workflow"],
        "workflow_id": snapshot["workflow_id"],
        "branch": snapshot["branch"],
        "evento": snapshot["evento"],
        "corte_criado_em_utc": snapshot["corte_criado_em_utc"],
        "coletado_em_utc": snapshot["coletado_em_utc"],
        "periodo_candidatas_utc": {
            "inicio": min(run["created_at"] for run in snapshot["execucoes"]),
            "fim": max(run["created_at"] for run in snapshot["execucoes"]),
        },
        "periodo_amostra_utc": {"inicio": linhas[0]["criado_em"], "fim": linhas[-1]["criado_em"]},
        "n_candidatas": len(snapshot["execucoes"]),
        "n_descartadas": sum(descartes.values()),
        "descartadas_por_motivo": descartes,
        "maior_sequencia_falhas_sem_descartes_intermediarios": maior_sem_descartes,
        "estatisticas": resumir_amostra(linhas),
    }
    with (pasta / "ci_pytest.csv").open("w", encoding="utf-8", newline="") as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=COLUNAS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(linhas)
    (pasta / "ci_pytest_resumo.json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    return resumo


if __name__ == "__main__":
    print(json.dumps(gerar_artefatos(), ensure_ascii=False, indent=2, allow_nan=False))
