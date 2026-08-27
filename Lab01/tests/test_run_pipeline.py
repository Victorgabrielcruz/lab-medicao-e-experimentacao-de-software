"""Testes do pipeline único de execução pós-coleta (task S03-06)."""

import glob
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from run_pipeline import (  # noqa: E402
    PipelineError,
    _collect_artifact_lines,
    _extract_path,
    _validate_raw_csv,
    run,
)

RAW_DIR = ROOT / "data" / "raw"
SUFFIX = "pipeline_test"
RAW_PATH = RAW_DIR / f"repos_raw_{SUFFIX}.csv"


def raw_row(**overrides):
    row = {
        "id": "repo-1", "name_with_owner": "owner/repo-1", "url": "https://github.com/owner/repo-1",
        "owner": "owner", "stargazer_count": "1000", "is_archived": "false",
        "collected_at": "2026-08-18T12:00:00Z", "created_at": "2020-08-18T12:00:00Z",
        "merged_pull_requests": "20", "total_pull_requests": "25", "releases_count": "5",
        "updated_at": "2026-08-18T12:00:00Z", "pushed_at": "2026-08-16T12:00:00Z",
        "default_branch": "main", "total_commits": "100", "last_commit_date": "2026-08-17T12:00:00Z",
        "primary_language": "Python", "open_issues": "20", "closed_issues": "80",
    }
    row.update(overrides)
    return row


def sample_raw_dataframe() -> pd.DataFrame:
    """Amostra piloto pequena, com linguagens populares e não populares, sem
    linhas idênticas, para permitir estatísticas/IQR da RQ07 sem degenerar."""
    return pd.DataFrame([
        raw_row(),
        raw_row(id="repo-2", name_with_owner="owner/repo-2", stargazer_count="500",
                merged_pull_requests="5", total_pull_requests="10", releases_count="1",
                primary_language="Ruby", open_issues="5", closed_issues="5"),
        raw_row(id="repo-3", name_with_owner="owner/repo-3", stargazer_count="2000",
                merged_pull_requests="80", total_pull_requests="90", releases_count="30",
                primary_language="Go", open_issues="2", closed_issues="98"),
        raw_row(id="repo-4", name_with_owner="owner/repo-4", stargazer_count="300",
                merged_pull_requests="0", total_pull_requests="0", releases_count="0",
                primary_language="", open_issues="0", closed_issues="0",
                default_branch="", total_commits="", last_commit_date=""),
        raw_row(id="repo-5", name_with_owner="owner/repo-5", stargazer_count="750",
                merged_pull_requests="12", total_pull_requests="15", releases_count="3",
                primary_language="JavaScript", open_issues="8", closed_issues="42"),
    ])


class PipelineHelpersTests(unittest.TestCase):
    def test_validate_raw_csv_rejects_missing_file(self):
        with self.assertRaises(PipelineError) as ctx:
            _validate_raw_csv(RAW_DIR / "arquivo_que_nao_existe.csv")
        self.assertEqual(ctx.exception.step, "entrada")
        self.assertIn("não encontrado", ctx.exception.reason)

    def test_validate_raw_csv_rejects_empty_file(self):
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        empty = RAW_DIR / f"repos_raw_{SUFFIX}_empty.csv"
        empty.write_text("", encoding="utf-8")
        try:
            with self.assertRaises(PipelineError) as ctx:
                _validate_raw_csv(empty)
            self.assertIn("vazio", ctx.exception.reason)
        finally:
            empty.unlink(missing_ok=True)

    def test_extract_path_raises_clear_error_when_label_missing(self):
        with self.assertRaises(PipelineError) as ctx:
            _extract_path("etapa-x", "Entrada: foo.csv\n", "Saída")
        self.assertEqual(ctx.exception.step, "etapa-x")

    def test_extract_path_finds_labelled_line(self):
        result = _extract_path("etapa-x", "Entrada: foo.csv\nSaída: bar.csv\n", "Saída")
        self.assertEqual(result, Path("bar.csv"))

    def test_collect_artifact_lines_filters_paths_only(self):
        stdout = "Repositórios validados: 5\nEvidências: data/processed/x.csv\nRelatório: reports/drafts/x.md\n"
        lines = _collect_artifact_lines(stdout)
        self.assertEqual(lines, [
            "Evidências: data/processed/x.csv",
            "Relatório: reports/drafts/x.md",
        ])


class PipelineEndToEndTests(unittest.TestCase):
    """Executa o pipeline real (subprocessos) sobre uma amostra piloto pequena.

    Os artefatos gerados usam um sufixo exclusivo de teste (`pipeline_test`)
    e são removidos em `tearDown`, para não poluir `data/` nem `reports/`.
    """

    def setUp(self):
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        sample_raw_dataframe().to_csv(RAW_PATH, index=False)

    def tearDown(self):
        patterns = [
            RAW_DIR / f"repos_raw_{SUFFIX}.csv",
            ROOT / "data" / "processed" / f"repos_processed_{SUFFIX}.csv",
            ROOT / "data" / "processed" / f"repos_rq07_consolidated_{SUFFIX}.csv",
        ]
        for path in patterns:
            path.unlink(missing_ok=True)
        for pattern in [
            f"data/processed/validation_*_{SUFFIX}.csv",
            f"data/processed/rq07_statistics_{SUFFIX}*.csv",
            f"data/processed/rq07_analysis_outliers_{SUFFIX}*.csv",
            f"data/processed/consolidation_rq07_{SUFFIX}.md",
            f"reports/drafts/validation_*_{SUFFIX}.md",
            f"reports/drafts/consolidation_rq07_{SUFFIX}.md",
            f"reports/drafts/rq07_analysis_{SUFFIX}*.md",
            f"reports/figures/rq07_*_{SUFFIX}*.svg",
        ]:
            for match in glob.glob(str(ROOT / pattern)):
                Path(match).unlink(missing_ok=True)

    def test_runs_full_pipeline_over_pilot_sample_without_errors(self):
        artifacts = run(RAW_PATH)

        self.assertTrue(any("processed" in line and line.endswith(".csv") for line in artifacts))
        self.assertTrue(any("validation_rq01_rq02" in line for line in artifacts))
        self.assertTrue(any("validation_rq03_rq04" in line for line in artifacts))
        self.assertTrue(any("validation_rq05_rq06" in line for line in artifacts))
        self.assertTrue(any("rq07_consolidated" in line for line in artifacts))
        self.assertTrue(any("rq07_statistics" in line or "rq07_analysis" in line for line in artifacts))
        self.assertTrue(any("validation_rq07" in line for line in artifacts))

        processed = ROOT / "data" / "processed" / f"repos_processed_{SUFFIX}.csv"
        self.assertTrue(processed.exists())
        self.assertEqual(len(pd.read_csv(processed)), 5)

    def test_stops_with_clear_message_when_raw_csv_is_missing(self):
        missing = RAW_DIR / f"repos_raw_{SUFFIX}_nao_existe.csv"
        with self.assertRaises(PipelineError) as ctx:
            run(missing)
        self.assertEqual(ctx.exception.step, "entrada")


if __name__ == "__main__":
    unittest.main()
