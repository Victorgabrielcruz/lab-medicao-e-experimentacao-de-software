"""Regras de integridade e qualidade do dataset oficial (Seção 13)."""

from .dataset_validator import (
    CRITICAL,
    INFO,
    WARNING,
    Finding,
    PairSummary,
    ValidationResult,
    load_dataset_csv,
    validate_dataset,
)
from .report import render_report_markdown

__all__ = [
    "CRITICAL",
    "INFO",
    "WARNING",
    "Finding",
    "PairSummary",
    "ValidationResult",
    "load_dataset_csv",
    "validate_dataset",
    "render_report_markdown",
]
