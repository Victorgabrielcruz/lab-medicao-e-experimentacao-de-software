"""Estatística descritiva e inferencial das RQ1-RQ3 (Seção 14)."""

from .data_loading import DatasetNotAuthorizedError, load_validated_dataset
from .paired_stats import (
    DescriptiveStats,
    Pair,
    WilcoxonResult,
    build_pairs,
    describe_treatment,
    holm_correction,
    wilcoxon_signed_rank,
)

__all__ = [
    "DatasetNotAuthorizedError",
    "DescriptiveStats",
    "Pair",
    "WilcoxonResult",
    "build_pairs",
    "describe_treatment",
    "holm_correction",
    "load_validated_dataset",
    "wilcoxon_signed_rank",
]
