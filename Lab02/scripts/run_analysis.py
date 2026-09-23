"""Executa toda a análise do Lab02 em um único comando."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis.consolidated import run  # noqa: E402


if __name__ == "__main__":
    count, warnings = run(ROOT)
    print(f"Geradas {count} linhas em data/processed/statistical-results.csv")
    print("Gerado reports/drafts/rq-answers.md")
    print(f"Ressalvas de origem: {warnings} (detalhadas no relatório)")
