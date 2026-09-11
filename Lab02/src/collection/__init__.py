"""Cronometragem e coleta padronizada dos trials (RQ1/RQ2)."""

from .trial_collector import (
    TIME_LIMIT_SECONDS,
    SuiteResult,
    TrialCollectionError,
    build_trial_id,
    collect_trial,
    run_trial,
)
from .trial_preparation import TrialPreparationError, find_allocation, prepare_trial

__all__ = [
    "TIME_LIMIT_SECONDS",
    "SuiteResult",
    "TrialCollectionError",
    "build_trial_id",
    "collect_trial",
    "run_trial",
    "TrialPreparationError",
    "find_allocation",
    "prepare_trial",
]
