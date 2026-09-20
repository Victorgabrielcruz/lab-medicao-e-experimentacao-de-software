"""Carrega o dataset oficial já validado, para uso pelas análises de RQ."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from src.validation import validate_dataset
from src.validation.dataset_validator import load_dataset_csv

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET_PATH = ROOT / "data" / "processed" / "trials.csv"


class DatasetNotAuthorizedError(RuntimeError):
    """O dataset reprovou a validação da Seção 13 e não pode ser analisado."""


def load_validated_dataset(dataset_path: Path = DEFAULT_DATASET_PATH) -> list[dict[str, Any]]:
    """Recarrega e valida o dataset (Seção 14.1, passo 1) antes de qualquer análise."""
    rows = load_dataset_csv(dataset_path)
    result = validate_dataset(rows, project_root=ROOT)
    if not result.authorized:
        details = "; ".join(f"{item.rule} ({item.trial_id})" for item in result.critical)
        raise DatasetNotAuthorizedError(f"Dataset reprovado na validação da Seção 13: {details}")
    return rows
