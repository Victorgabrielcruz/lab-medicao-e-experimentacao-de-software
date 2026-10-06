import datetime as dt
from pathlib import Path

import pytest

from pipeline.__main__ import main
from pipeline.config import TOKEN_ENV, ConfigError, janela_utc, load_config, read_token

CONFIG = Path(__file__).resolve().parents[1] / "config.yaml"


def test_config_do_repositorio_e_valida():
    config = load_config(CONFIG)
    assert config["api"]["base_url"] == "https://api.github.com"


def test_arquivo_inexistente(tmp_path):
    with pytest.raises(ConfigError, match="não encontrado"):
        load_config(tmp_path / "nao-existe.yaml")


def test_raiz_que_nao_e_mapeamento(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("- item\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="mapeamento"):
        load_config(path)


def test_secao_obrigatoria_ausente(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("api: {}\njanela: {}\ninclusao: {}\nruns: {}\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="caminhos"):
        load_config(path)


def _config_com(tmp_path, janela="inicio: 2025-10-01\n  fim: 2026-09-30", inclusao="min_releases: 5\n  min_runs_validos: 50"):
    path = tmp_path / "config.yaml"
    path.write_text(
        f"api: {{}}\njanela:\n  {janela}\ninclusao:\n  {inclusao}\nruns: {{}}\ncaminhos: {{}}\n",
        encoding="utf-8",
    )
    return path


def test_janela_e_criterios_do_repositorio():
    config = load_config(CONFIG)
    assert config["janela"] == {"inicio": dt.date(2025, 10, 1), "fim": dt.date(2026, 9, 30)}
    assert config["inclusao"] == {"min_releases": 5, "min_runs_validos": 50}
    assert config["runs"]["conclusoes_falha"] == ["failure", "timed_out", "startup_failure"]


def test_janela_utc_e_semiaberta():
    inicio, fim = janela_utc(load_config(CONFIG))
    assert inicio == dt.datetime(2025, 10, 1, tzinfo=dt.timezone.utc)
    assert fim == dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc)


@pytest.mark.parametrize("janela", [
    "inicio: 2025-10-01\n  fim: 2026-10-31",
    "inicio: 2025-10-01\n  fim: 2026-10-01",
    "inicio: 2026-09-30\n  fim: 2025-10-01",
])
def test_janela_diferente_de_12_meses(tmp_path, janela):
    with pytest.raises(ConfigError, match="12 meses"):
        load_config(_config_com(tmp_path, janela=janela))


def test_janela_sem_datas(tmp_path):
    with pytest.raises(ConfigError, match="AAAA-MM-DD"):
        load_config(_config_com(tmp_path, janela="inicio: outubro\n  fim: null"))


def test_janela_iniciando_em_29_de_fevereiro(tmp_path):
    load_config(_config_com(tmp_path, janela="inicio: 2028-02-29\n  fim: 2029-02-27"))


@pytest.mark.parametrize("inclusao", [
    "min_releases: 0\n  min_runs_validos: 50",
    "min_releases: 5\n  min_runs_validos: cinquenta",
    "min_releases: true\n  min_runs_validos: 50",
])
def test_criterio_de_inclusao_invalido(tmp_path, inclusao):
    with pytest.raises(ConfigError, match="inteiro positivo"):
        load_config(_config_com(tmp_path, inclusao=inclusao))


def test_token_lido_do_ambiente():
    assert read_token({TOKEN_ENV: " abc "}) == "abc"


@pytest.mark.parametrize("env", [{}, {TOKEN_ENV: "  "}])
def test_token_ausente(env):
    with pytest.raises(ConfigError, match=TOKEN_ENV):
        read_token(env)


def test_entry_point_executa(monkeypatch, capsys):
    monkeypatch.setenv(TOKEN_ENV, "token-falso")
    chamadas = []

    def executar_falso(config, client):
        chamadas.append(client)
        return Path("candidatos.json"), [{"truncada": False}], [{"id": 1}]

    monkeypatch.setattr("pipeline.candidatos.executar", executar_falso)
    assert main(["--config", str(CONFIG)]) == 0
    assert len(chamadas) == 1
    assert "Candidatos: 1 repositórios em 1 fatias (0 truncadas)" in capsys.readouterr().out


def test_entry_point_sem_token(monkeypatch, capsys):
    monkeypatch.delenv(TOKEN_ENV, raising=False)
    assert main(["--config", str(CONFIG)]) == 2
    assert TOKEN_ENV in capsys.readouterr().err
