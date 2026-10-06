from pathlib import Path

import pytest

from pipeline.__main__ import main
from pipeline.config import TOKEN_ENV, ConfigError, load_config, read_token

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
    path.write_text("api: {}\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="caminhos"):
        load_config(path)


def test_token_lido_do_ambiente():
    assert read_token({TOKEN_ENV: " abc "}) == "abc"


@pytest.mark.parametrize("env", [{}, {TOKEN_ENV: "  "}])
def test_token_ausente(env):
    with pytest.raises(ConfigError, match=TOKEN_ENV):
        read_token(env)


def test_entry_point_executa(monkeypatch, capsys):
    monkeypatch.setenv(TOKEN_ENV, "token-falso")
    assert main(["--config", str(CONFIG)]) == 0
    assert "Configuração carregada" in capsys.readouterr().out


def test_entry_point_sem_token(monkeypatch, capsys):
    monkeypatch.delenv(TOKEN_ENV, raising=False)
    assert main(["--config", str(CONFIG)]) == 2
    assert TOKEN_ENV in capsys.readouterr().err
