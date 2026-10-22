import csv
import hashlib
import json

import pytest

from pipeline.rq07 import COMBINACOES, DATASET, classificar_linhas, executar


def linha(**mudancas):
    return {"id": "1", "full_name": "org/projeto", "janela_inicio": "2025-10-01T00:00:00Z",
            "janela_fim_exclusivo": "2026-10-01T00:00:00Z", "deployment_frequency": "1",
            "lead_time_a": "800", "lead_time_b": "1", "cfr_a": "0.9", "cfr_b": "0.1",
            "tempo_recuperacao": "0.5", "classe_deployment_frequency": "High",
            "classe_lead_time_a": "Low", "classe_lead_time_b": "Elite", "classe_cfr_a": "Low",
            "classe_cfr_b": "Elite", "classe_tempo_recuperacao": "Elite",
            "coleta_incompleta": "false", "calculo_parcial": "false", **mudancas}


def test_tres_combinacoes_alteram_as_fontes_e_a_mediana():
    c1, c2, c3 = classificar_linhas([linha()])
    assert [r["geral"] for r in (c1, c2, c3)] == ["High", "Medium", "Elite"]
    assert all(r["completa"] for r in (c1, c2, c3))
    assert c2["lead_time"] == 800 and c1["lead_time"] == c3["lead_time"] == 1
    assert c1["change_failure_rate"] == c2["change_failure_rate"] == .9
    assert c3["change_failure_rate"] == .1


def test_c1_coincide_com_referencia_main_e_com_as_500_classes_gerais():
    import pandas as pd
    from pipeline.classes_dora import REFERENCIA_GERAL, classe_geral
    assert {m: f"classe_{c}" for m, c in COMBINACOES["C1"].items()} == REFERENCIA_GERAL
    with DATASET.open(encoding="utf-8-sig", newline="") as f:
        linhas = list(csv.DictReader(f))
    esperado = classe_geral(pd.read_csv(DATASET), list(REFERENCIA_GERAL.values()))
    classes = {r["id"]: r["geral"] for r in classificar_linhas(linhas) if r["combinacao"] == "C1"}
    assert [classes[int(r["id"])] for r in linhas] == esperado.tolist()


def test_ausencia_nao_vira_zero_e_zero_observado_e_preservado():
    registros = classificar_linhas([linha(cfr_b="", classe_cfr_b="", cfr_a="0", classe_cfr_a="Elite")])
    assert registros[2]["change_failure_rate"] is None
    assert registros[2]["classe_change_failure_rate"] is None
    assert registros[2]["metricas_disponiveis"] == 3
    assert not registros[2]["completa"]
    assert registros[0]["change_failure_rate"] == 0


@pytest.mark.parametrize("alteracao", [
    {"lead_time_a": "nan"}, {"cfr_b": "1.1"}, {"lead_time_b": "-1"},
    {"coleta_incompleta": ""}, {"classe_lead_time_a": "Elite"},
    {"janela_fim_exclusivo": "2025-01-01T00:00:00Z"},
])
def test_rejeita_entrada_invalida(alteracao):
    with pytest.raises(ValueError):
        classificar_linhas([linha(**alteracao)])


def test_rejeita_ids_duplicados_e_janelas_misturadas():
    with pytest.raises(ValueError, match="duplicado"):
        classificar_linhas([linha(), linha()])
    with pytest.raises(ValueError, match="Janelas divergentes"):
        classificar_linhas([linha(), linha(id="2", janela_inicio="2025-09-30T00:00:00Z")])


def test_corte_mensal_considera_ano_bissexto():
    dados = linha(janela_inicio="2023-10-01T00:00:00Z", janela_fim_exclusivo="2024-10-01T00:00:00Z",
                  deployment_frequency=str(12 * 7 / 366), classe_deployment_frequency="Medium")
    assert all(r["classe_deployment_frequency"] == "Medium" for r in classificar_linhas([dados]))


def test_exportacao_reproduzivel_e_hash_obrigatorio(tmp_path):
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    dataset = entrada / "dataset.csv"
    with dataset.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=linha().keys())
        writer.writeheader()
        writer.writerow(linha())
    manifesto = {"contrato": "lab03-dataset-v1", "total_repositorios": 1,
                 "csv_sha256": hashlib.sha256(dataset.read_bytes()).hexdigest(),
                 "janela": {"inicio": linha()["janela_inicio"], "fim_exclusivo": linha()["janela_fim_exclusivo"]}}
    (entrada / "manifesto.csv.json").write_text(json.dumps(manifesto), encoding="utf-8")
    a, b = tmp_path / "a", tmp_path / "b"
    executar(dataset, a)
    executar(dataset, b)
    for nome in ("combinacoes.json", "classificacoes.csv"):
        assert (a / nome).read_bytes() == (b / nome).read_bytes()
    dataset.write_text(dataset.read_text() + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256"):
        executar(dataset, a)
