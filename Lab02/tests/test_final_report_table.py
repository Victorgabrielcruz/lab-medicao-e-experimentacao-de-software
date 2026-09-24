"""Cobertura da tabela reproduzível incluída no relatório final."""
from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from scripts.generate_final_report_table import build_summary, write_artifacts  # noqa: E402


class FinalReportTableTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = ROOT / "data/processed/statistical-results.csv"

    def test_summary_preserves_values_and_missingness(self) -> None:
        rows = build_summary(self.source)

        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[0]["RQ"], "RQ1")
        self.assertIn("Δ Manual−IA=+310 s", rows[0]["Comparação pareada / ressalva"])
        self.assertIn("p=0,0098", rows[0]["Comparação pareada / ressalva"])
        self.assertIn("9/9 empates", rows[1]["Comparação pareada / ressalva"])
        self.assertIn("5 ausente(s)", rows[2]["Comparação pareada / ressalva"])
        self.assertIn("4/9 pares estruturais completos", rows[4]["Comparação pareada / ressalva"])

    def test_written_artifacts_are_readable_and_traceable(self) -> None:
        rows = build_summary(self.source)
        with tempfile.TemporaryDirectory() as temporary:
            csv_path, markdown_path = write_artifacts(rows, Path(temporary))
            with csv_path.open(encoding="utf-8", newline="") as handle:
                exported = list(csv.DictReader(handle))
            self.assertEqual(exported, rows)
            markdown = markdown_path.read_text(encoding="utf-8")
            self.assertIn("scripts/generate_final_report_table.py", markdown)
            self.assertIn("Valores ausentes permanecem ausentes", markdown)


if __name__ == "__main__":
    unittest.main()
