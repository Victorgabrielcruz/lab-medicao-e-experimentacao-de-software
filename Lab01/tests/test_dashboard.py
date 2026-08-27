"""Testes do dashboard Streamlit (task S03-07).

Cobre apenas as funções puras do módulo (seleção de dataset, derivação de
caminhos e definição das RQs), sem depender de um runtime Streamlit ativo.
A subida real do servidor (`streamlit run src/dashboard/app.py`) foi
verificada manualmente contra a base processada oficial.
"""

import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_DIR = ROOT / "src" / "dashboard"
sys.path.insert(0, str(DASHBOARD_DIR))

from app import (  # noqa: E402
    RQ_DEFINITIONS,
    RQ07_METRICS,
    outliers_path_for,
    rq07_artifacts_for,
    stamp_for,
)

PROCESSED_DIR = ROOT / "data" / "processed"


class StampAndArtifactPathsTests(unittest.TestCase):
    def test_stamp_for_removes_prefix(self):
        path = Path("data/processed/repos_processed_2026-08-20T222207Z.csv")
        self.assertEqual(stamp_for(path), "2026-08-20T222207Z")

    def test_rq07_artifacts_for_derives_expected_paths(self):
        consolidated, statistics = rq07_artifacts_for("2026-08-20T222207Z")
        self.assertEqual(
            consolidated, PROCESSED_DIR / "repos_rq07_consolidated_2026-08-20T222207Z.csv"
        )
        self.assertEqual(statistics, PROCESSED_DIR / "rq07_statistics_2026-08-20T222207Z.csv")

    def test_outliers_path_for_derives_expected_path(self):
        self.assertEqual(
            outliers_path_for("2026-08-20T222207Z"),
            PROCESSED_DIR / "outliers_2026-08-20T222207Z.csv",
        )


class RQDefinitionsTests(unittest.TestCase):
    def test_rq_definitions_cover_rq01_to_rq06(self):
        rqs = [definition["rq"] for definition in RQ_DEFINITIONS]
        self.assertEqual(rqs, ["RQ01", "RQ02", "RQ03", "RQ04", "RQ05", "RQ06"])

    def test_rq_definitions_columns_exist_in_real_processed_dataset(self):
        """As colunas usadas pelo dashboard devem existir na base processada real.

        Garante que o dashboard não vai quebrar por divergência de schema com
        `src/analysis/build_processed_dataset.py` (docs/dataset/processed-dataset.md).
        """
        datasets = sorted(PROCESSED_DIR.glob("repos_processed_*.csv"))
        if not datasets:
            self.skipTest("Nenhum CSV processado disponível para checar o schema.")
        df = pd.read_csv(datasets[-1], nrows=1)
        for definition in RQ_DEFINITIONS:
            self.assertIn(
                definition["coluna"], df.columns,
                f"Coluna '{definition['coluna']}' ({definition['rq']}) ausente na base processada.",
            )

    def test_rq_definitions_have_histogram_or_categorical_type(self):
        for definition in RQ_DEFINITIONS:
            self.assertIn(definition["tipo"], {"histograma", "barras_categoria"})

    def test_rq07_metrics_columns_exist_in_rq07_statistics_when_available(self):
        """As métricas usadas na seção da RQ07 devem existir nas estatísticas geradas."""
        statistics_files = sorted(PROCESSED_DIR.glob("rq07_statistics_*.csv"))
        if not statistics_files:
            self.skipTest("Nenhum rq07_statistics_*.csv disponível para checar o schema.")
        statistics = pd.read_csv(statistics_files[-1])
        group_metrics = set(statistics.loc[statistics["tipo"] == "grupo", "metrica"].unique())
        for metric in RQ07_METRICS:
            self.assertIn(metric, group_metrics)

    def test_outliers_csv_schema_matches_dashboard_expectations_when_available(self):
        """As colunas lidas por `render_outliers` devem existir no CSV real de outliers."""
        outliers_files = sorted(PROCESSED_DIR.glob("outliers_*.csv"))
        if not outliers_files:
            self.skipTest("Nenhum outliers_*.csv disponível para checar o schema.")
        outliers = pd.read_csv(outliers_files[-1])
        expected_columns = {
            "name_with_owner", "descricao", "valor", "lado", "severidade",
            "mediana", "primary_language", "observacao",
        }
        self.assertTrue(expected_columns.issubset(outliers.columns))


class AppRunsWithoutExceptionsTests(unittest.TestCase):
    """Sobe o dashboard de ponta a ponta com o AppTest do Streamlit.

    Complementa os testes de schema acima: garante que a página inteira
    (visão geral, abas RQ01-RQ06, RQ07 e Outliers) renderiza sem lançar
    nenhuma exceção contra a base processada real do projeto.
    """

    def setUp(self):
        if not sorted(PROCESSED_DIR.glob("repos_processed_*.csv")):
            self.skipTest("Nenhum CSV processado disponível para subir o dashboard.")

    def test_app_runs_without_exceptions(self):
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_file(str(DASHBOARD_DIR / "app.py"), default_timeout=60)
        at.run()
        self.assertEqual(len(at.exception), 0, msg=[e.value for e in at.exception])
        # RQ01-06 + RQ07 + Outliers.
        self.assertEqual(len(at.tabs), len(RQ_DEFINITIONS) + 2)

    def test_outlier_metric_filter_does_not_raise(self):
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_file(str(DASHBOARD_DIR / "app.py"), default_timeout=60)
        at.run()
        filters = [box for box in at.selectbox if box.key == "outlier_metric_filter"]
        if not filters:
            self.skipTest("Filtro de métrica de outliers não renderizado (sem CSV de outliers).")
        options = filters[0].options
        if len(options) < 2:
            self.skipTest("Sem métricas suficientes para testar o filtro.")
        filters[0].select(options[1]).run()
        self.assertEqual(len(at.exception), 0, msg=[e.value for e in at.exception])


if __name__ == "__main__":
    unittest.main()
