"""Carregamento e validação da configuração do pipeline."""

import os
from pathlib import Path

import yaml

TOKEN_ENV = "GITHUB_TOKEN"
REQUIRED_SECTIONS = ("api", "caminhos")


class ConfigError(ValueError):
    """Configuração ausente ou inválida."""


def load_config(path):
    """Lê o arquivo YAML e confere se as seções obrigatórias existem."""
    path = Path(path)
    if not path.is_file():
        raise ConfigError(f"Arquivo de configuração não encontrado: {path}")

    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"{path} deve conter um mapeamento YAML no nível raiz.")

    missing = [section for section in REQUIRED_SECTIONS if section not in data]
    if missing:
        raise ConfigError(f"Seções ausentes em {path}: {', '.join(missing)}")
    return data


def read_token(env=None):
    """Retorna o token do GitHub lido da variável de ambiente."""
    env = os.environ if env is None else env
    token = env.get(TOKEN_ENV, "").strip()
    if not token:
        raise ConfigError(f"Defina a variável de ambiente {TOKEN_ENV} com um token do GitHub.")
    return token
