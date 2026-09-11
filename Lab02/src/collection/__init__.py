"""Cronometragem e coleta padronizada dos trials (RQ1/RQ2)."""

from .trial_collector import (
    TIME_LIMIT_SECONDS,
    SuiteResult,
    TrialCollectionError,
    build_trial_id,
    collect_trial,
    run_trial,
)

__all__ = [
    "TIME_LIMIT_SECONDS",
    "SuiteResult",
    "TrialCollectionError",
    "build_trial_id",
    "collect_trial",
    "run_trial",
]
