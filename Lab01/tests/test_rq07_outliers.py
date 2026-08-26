"""Testes da identificação de outliers (S03-04).

    python3 -m unittest discover -s tests
"""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "analysis"))

import pandas as pd

from rq07_outliers import (
    EXTREME,
    METRICS,
    MODERATE,
    analyze,
    build_report,
    fences_for,
    outliers_for,
    overlap_for,
    profile_for,
)


def base(**overrides) -> pd.DataFrame:
    """Amostra mínima com todas as colunas que o módulo exige."""
    dados = {
        "name_with_owner": [f"org/repo{i}" for i in range(10)],
        "url": [f"https://github.com/org/repo{i}" for i in range(10)],
        "primary_language": ["Python"] * 10,
        # 1 a 9 mais um valor muito acima: distribuicao conhecida
        "age_years": [1, 2, 3, 4, 5, 6, 7, 8, 9, 100],
        "accepted_pull_requests": [10] * 10,
        "releases_count": [5] * 10,
        "days_since_push": [1] * 10,
        "closed_issues_percentage": [90.0] * 10,
        "stargazer_count": [1000] * 10,
        "releases_no_teto": [False] * 10,
    }
    dados.update(overrides)

    return pd.DataFrame(dados)


class FencesTest(unittest.TestCase):
    def test_quartis_e_limites(self):
        df = base()
        f = fences_for(df, "age_years", "idade")

        self.assertEqual(f.count, 10)
        self.assertEqual(f.missing, 0)
        self.assertAlmostEqual(f.q1, 3.25)
        self.assertAlmostEqual(f.q3, 7.75)
        self.assertAlmostEqual(f.iqr, 4.5)
        self.assertAlmostEqual(f.lower, 3.25 - MODERATE * 4.5)
        self.assertAlmostEqual(f.upper, 7.75 + MODERATE * 4.5)
        self.assertAlmostEqual(f.upper_extreme, 7.75 + EXTREME * 4.5)

    def test_conta_acima_e_abaixo(self):
        f = fences_for(base(), "age_years", "idade")

        self.assertEqual(f.above, 1)
        self.assertEqual(f.below, 0)

    def test_vazios_nao_entram_no_calculo(self):
        df = base(closed_issues_percentage=[90.0] * 9 + [None])
        f = fences_for(df, "closed_issues_percentage", "issues fechadas")

        self.assertEqual(f.count, 9)
        self.assertEqual(f.missing, 1)
        self.assertEqual(f.below + f.above, 0)

    def test_metrica_constante_nao_gera_outlier(self):
        f = fences_for(base(), "stargazer_count", "estrelas")

        self.assertEqual(f.iqr, 0)
        self.assertEqual(f.below + f.above, 0)
        self.assertEqual(f.zscore_flagged, 0)


class OutliersTest(unittest.TestCase):
    def setUp(self):
        self.df = base()
        self.fences = fences_for(self.df, "age_years", "idade")
        self.marcados = outliers_for(self.df, self.fences)

    def test_identifica_o_repositorio_pelo_nome(self):
        self.assertEqual(list(self.marcados["name_with_owner"]), ["org/repo9"])

    def test_registra_valor_lado_e_severidade(self):
        linha = self.marcados.iloc[0]

        self.assertEqual(linha["valor"], 100)
        self.assertEqual(linha["lado"], "acima")
        self.assertEqual(linha["severidade"], "extremo")

    def test_separa_moderado_de_extremo(self):
        # 20 fica acima da cerca de 14.5 e abaixo da de 21.25.
        df = base(age_years=[1, 2, 3, 4, 5, 6, 7, 8, 9, 20])
        marcados = outliers_for(df, fences_for(df, "age_years", "idade"))

        self.assertEqual(marcados.iloc[0]["severidade"], "moderado")

    def test_sem_outlier_devolve_tabela_vazia_com_as_colunas(self):
        df = base(age_years=[5] * 10)
        marcados = outliers_for(df, fences_for(df, "age_years", "idade"))

        self.assertTrue(marcados.empty)
        self.assertIn("severidade", marcados.columns)

    def test_marca_releases_truncadas_pela_api(self):
        df = base(
            releases_count=[1, 2, 3, 4, 5, 6, 7, 8, 9, 1000],
            releases_no_teto=[False] * 9 + [True],
        )
        marcados = outliers_for(df, fences_for(df, "releases_count", "releases"))

        self.assertEqual(marcados.iloc[0]["observacao"], "valor truncado pela API")


class AnalyzeTest(unittest.TestCase):
    def test_nao_altera_a_base_original(self):
        df = base()
        antes = df.copy(deep=True)

        analyze(df)

        pd.testing.assert_frame_equal(df, antes)

    def test_cobre_todas_as_metricas_pedidas(self):
        resultado = analyze(base())

        self.assertEqual([f.column for f in resultado.fences], list(METRICS))
        self.assertEqual(resultado.total_rows, 10)

    def test_relatorio_documenta_o_metodo_e_cita_o_repositorio(self):
        resultado = analyze(base())
        texto = build_report(resultado, Path("repos_rq07_consolidated_teste.csv"), Path("saida.csv"))

        self.assertIn("Q1 - 1.5 x IQR", texto)
        self.assertIn("org/repo9", texto)


class ProfileTest(unittest.TestCase):
    """Comparação do grupo sinalizado com o resto da amostra (S03-05)."""

    def test_compara_medianas_do_grupo_e_do_resto(self):
        df = base()
        fences = fences_for(df, "age_years", "idade")
        perfil = profile_for(df, fences, {"org/repo9"})

        self.assertEqual(perfil.flagged, 1)
        self.assertEqual(perfil.median_flagged, 100)
        self.assertEqual(perfil.median_rest, 5)

    def test_mede_ausencia_de_linguagem_no_grupo(self):
        df = base(primary_language=["Python"] * 9 + [None])
        fences = fences_for(df, "age_years", "idade")
        perfil = profile_for(df, fences, {"org/repo9"})

        self.assertEqual(perfil.without_language, 1.0)
        self.assertAlmostEqual(perfil.without_language_sample, 0.1)

    def test_conta_arquivados_e_sem_releases(self):
        df = base(
            is_archived=[False] * 9 + [True],
            releases_count=[5] * 9 + [0],
        )
        fences = fences_for(df, "age_years", "idade")
        perfil = profile_for(df, fences, {"org/repo9"})

        self.assertEqual(perfil.archived, 1)
        self.assertEqual(perfil.zero_releases, 1.0)

    def test_grupo_vazio_nao_quebra(self):
        df = base()
        fences = fences_for(df, "stargazer_count", "estrelas")
        perfil = profile_for(df, fences, set())

        self.assertEqual(perfil.flagged, 0)
        self.assertEqual(perfil.without_language, 0.0)


class OverlapTest(unittest.TestCase):
    """Repositórios sinalizados em mais de uma métrica."""

    def outliers(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "name_with_owner": ["a/a", "a/a", "a/a", "b/b", "b/b", "c/c"],
                "metrica": [
                    "age_years",
                    "releases_count",
                    "stargazer_count",
                    "age_years",
                    "releases_count",
                    "age_years",
                ],
            }
        )

    def test_conta_quantos_repositorios_por_numero_de_metricas(self):
        resumo, _ = overlap_for(self.outliers())

        self.assertEqual(resumo[1], 1)
        self.assertEqual(resumo[2], 1)
        self.assertEqual(resumo[3], 1)

    def test_lista_apenas_quem_repete(self):
        _, multi = overlap_for(self.outliers())

        self.assertEqual(list(multi["name_with_owner"]), ["a/a", "b/b"])
        self.assertEqual(multi.iloc[0]["metricas"], 3)
        self.assertIn("stargazer_count", multi.iloc[0]["quais"])

    def test_sem_outliers_devolve_estruturas_vazias(self):
        resumo, multi = overlap_for(pd.DataFrame(columns=["name_with_owner", "metrica"]))

        self.assertTrue(resumo.empty)
        self.assertTrue(multi.empty)


class RelatorioInterpretativoTest(unittest.TestCase):
    def test_relatorio_traz_comparacao_e_sobreposicao(self):
        resultado = analyze(base())
        texto = build_report(resultado, Path("origem.csv"), Path("saida.csv"))

        self.assertIn("Comparação com o comportamento geral da amostra", texto)
        self.assertIn("Repositórios sinalizados em mais de uma métrica", texto)


if __name__ == "__main__":
    unittest.main()
