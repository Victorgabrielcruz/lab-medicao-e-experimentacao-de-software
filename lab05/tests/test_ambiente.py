import json
import sqlite3

from experimento.ambiente import registrar_ambiente, salvar_ambiente

CAMPOS = {"data_hora_utc", "sqlite_version", "python_version", "sistema", "processador",
          "n_cpus", "disco_total_gb", "disco_livre_gb"}


def test_registro_contem_campos_essenciais(tmp_path):
    ambiente = registrar_ambiente(tmp_path)
    assert CAMPOS <= ambiente.keys()
    assert ambiente["sqlite_version"] == sqlite3.sqlite_version
    assert ambiente["disco_total_gb"] >= ambiente["disco_livre_gb"] > 0


def test_salvar_ambiente_gera_json(tmp_path):
    caminho = tmp_path / "sub" / "ambiente.json"
    ambiente = salvar_ambiente(caminho)
    assert json.loads(caminho.read_text(encoding="utf-8")) == ambiente
