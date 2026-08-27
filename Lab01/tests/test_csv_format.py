"""Valida o formato dos CSV gerados, conforme docs/dataset/raw-dataset.md.

Roda sobre os arquivos presentes em data/. Se nao houver nenhum, os testes sao
pulados em vez de falhar, para nao quebrar quem clonou o repositorio sem ter
rodado a coleta.

    python3 -m unittest discover -s tests
"""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

# Contrato entre a coleta em C# e a analise em Python. Mudar aqui exige mudar
# RawCsvWriter.cs, docs/dataset/raw-dataset.md e quem le o arquivo.
RAW_HEADER = [
    "id",
    "name_with_owner",
    "url",
    "owner",
    "stargazer_count",
    "is_archived",
    "collected_at",
    "created_at",
    "merged_pull_requests",
    "total_pull_requests",
    "releases_count",
    "updated_at",
    "pushed_at",
    "default_branch",
    "total_commits",
    "last_commit_date",
    "primary_language",
    "open_issues",
    "closed_issues",
]

RAW_INTEGERS = [
    "stargazer_count",
    "merged_pull_requests",
    "total_pull_requests",
    "releases_count",
    "total_commits",
    "open_issues",
    "closed_issues",
]

RAW_DATES = ["collected_at", "created_at", "updated_at", "pushed_at", "last_commit_date"]

ISO_8601_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def csv_files(directory: Path, pattern: str) -> list[Path]:
    return sorted(directory.glob(pattern)) if directory.exists() else []


def read_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class FormatoComumTest(unittest.TestCase):
    """Regras que valem para todo CSV do projeto."""

    def arquivos(self) -> list[Path]:
        return csv_files(RAW_DIR, "*.csv") + csv_files(PROCESSED_DIR, "*.csv")

    def test_codificacao_utf8_sem_bom(self):
        arquivos = self.arquivos()
        if not arquivos:
            self.skipTest("nenhum CSV em data/")

        for path in arquivos:
            with self.subTest(arquivo=path.name):
                conteudo = path.read_bytes()
                self.assertFalse(conteudo.startswith(b"\xef\xbb\xbf"), "arquivo com BOM")
                conteudo.decode("utf-8")

    def test_separador_virgula_e_linhas_completas(self):
        arquivos = self.arquivos()
        if not arquivos:
            self.skipTest("nenhum CSV em data/")

        for path in arquivos:
            with self.subTest(arquivo=path.name):
                with path.open(newline="", encoding="utf-8") as handle:
                    linhas = list(csv.reader(handle))

                self.assertGreater(len(linhas), 1, "arquivo sem dados")

                larguras = {len(linha) for linha in linhas}
                self.assertEqual(
                    len(larguras),
                    1,
                    f"linhas com quantidade de campos diferente: {sorted(larguras)}",
                )


class CsvBrutoTest(unittest.TestCase):
    """Regras especificas do CSV bruto do coletor."""

    def arquivos(self) -> list[Path]:
        return csv_files(RAW_DIR, "repos_raw_*.csv")

    def test_cabecalho_bate_com_o_contrato(self):
        arquivos = self.arquivos()
        if not arquivos:
            self.skipTest("nenhum repos_raw_*.csv em data/raw")

        for path in arquivos:
            with self.subTest(arquivo=path.name):
                with path.open(newline="", encoding="utf-8") as handle:
                    cabecalho = next(csv.reader(handle))

                self.assertEqual(cabecalho, RAW_HEADER)

    def test_id_unico(self):
        arquivos = self.arquivos()
        if not arquivos:
            self.skipTest("nenhum repos_raw_*.csv em data/raw")

        for path in arquivos:
            with self.subTest(arquivo=path.name):
                ids = [linha["id"] for linha in read_rows(path)]
                self.assertEqual(len(ids), len(set(ids)), "id repetido no arquivo")

    def test_inteiros_sao_inteiros(self):
        arquivos = self.arquivos()
        if not arquivos:
            self.skipTest("nenhum repos_raw_*.csv em data/raw")

        for path in arquivos:
            for linha in read_rows(path):
                for coluna in RAW_INTEGERS:
                    valor = linha[coluna]

                    if valor == "":
                        continue

                    with self.subTest(arquivo=path.name, coluna=coluna, valor=valor):
                        self.assertRegex(valor, r"^\d+$")

    def test_datas_em_iso_8601_utc(self):
        arquivos = self.arquivos()
        if not arquivos:
            self.skipTest("nenhum repos_raw_*.csv em data/raw")

        for path in arquivos:
            for linha in read_rows(path):
                for coluna in RAW_DATES:
                    valor = linha[coluna]

                    if valor == "":
                        continue

                    with self.subTest(arquivo=path.name, coluna=coluna, valor=valor):
                        self.assertRegex(valor, ISO_8601_UTC)

    def test_booleano_em_minusculas(self):
        arquivos = self.arquivos()
        if not arquivos:
            self.skipTest("nenhum repos_raw_*.csv em data/raw")

        for path in arquivos:
            valores = {linha["is_archived"] for linha in read_rows(path)}

            with self.subTest(arquivo=path.name):
                self.assertTrue(valores <= {"true", "false"}, f"valores inesperados: {valores}")

    def test_data_de_referencia_unica_por_arquivo(self):
        arquivos = self.arquivos()
        if not arquivos:
            self.skipTest("nenhum repos_raw_*.csv em data/raw")

        for path in arquivos:
            referencias = {linha["collected_at"] for linha in read_rows(path)}

            with self.subTest(arquivo=path.name):
                self.assertEqual(len(referencias), 1, f"mais de uma referencia: {referencias}")

    def test_ausente_fica_vazio_e_nao_zero(self):
        arquivos = self.arquivos()
        if not arquivos:
            self.skipTest("nenhum repos_raw_*.csv em data/raw")

        # Repositorio sem branch padrao nao tem commits: os tres campos ficam
        # vazios juntos. Zero ali significaria "nenhum commit", que e diferente.
        for path in arquivos:
            for linha in read_rows(path):
                if linha["default_branch"] == "":
                    with self.subTest(arquivo=path.name, repo=linha["name_with_owner"]):
                        self.assertEqual(linha["total_commits"], "")
                        self.assertEqual(linha["last_commit_date"], "")


if __name__ == "__main__":
    unittest.main()
