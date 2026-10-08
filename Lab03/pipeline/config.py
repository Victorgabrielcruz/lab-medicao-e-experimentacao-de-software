"""Carregamento e validação da configuração do pipeline."""

import datetime as dt
import os
from pathlib import Path

import yaml

TOKEN_ENV = "GITHUB_TOKEN"
REQUIRED_SECTIONS = ("api", "janela", "inclusao", "runs", "caminhos")


class ConfigError(ValueError):
    """Configuração ausente ou inválida."""


def load_config(path):
    """Lê o arquivo YAML e confere as seções obrigatórias e a janela de observação."""
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

    validate_janela(data["janela"])
    validate_inclusao(data["inclusao"])
    return data


def _um_ano_depois(date):
    try:
        return date.replace(year=date.year + 1)
    except ValueError:  # 29 de fevereiro
        return date.replace(year=date.year + 1, day=28)


def validate_janela(janela):
    """Exige datas inclusivas que cubram exatamente 12 meses."""
    inicio, fim = janela.get("inicio"), janela.get("fim")
    if not isinstance(inicio, dt.date) or not isinstance(fim, dt.date):
        raise ConfigError("janela.inicio e janela.fim devem ser datas no formato AAAA-MM-DD.")
    if fim != _um_ano_depois(inicio) - dt.timedelta(days=1):
        raise ConfigError(f"A janela deve cobrir 12 meses: {inicio} a {fim} não confere.")


def validate_inclusao(inclusao):
    for key in ("min_releases", "min_runs_validos"):
        value = inclusao.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise ConfigError(f"inclusao.{key} deve ser um inteiro positivo.")
    if "incluir_prereleases" in inclusao and not isinstance(inclusao["incluir_prereleases"], bool):
        raise ConfigError("inclusao.incluir_prereleases deve ser booleano.")


def janela_utc(config):
    """Retorna a janela como intervalo [início, fim) em datetimes UTC."""
    janela = config["janela"]
    inicio = dt.datetime.combine(janela["inicio"], dt.time.min, tzinfo=dt.timezone.utc)
    fim = dt.datetime.combine(janela["fim"] + dt.timedelta(days=1), dt.time.min, tzinfo=dt.timezone.utc)
    return inicio, fim


def read_token(env=None):
    """Retorna o token do GitHub lido da variável de ambiente."""
    env = os.environ if env is None else env
    token = env.get(TOKEN_ENV, "").strip()
    if not token:
        raise ConfigError(f"Defina a variável de ambiente {TOKEN_ENV} com um token do GitHub.")
    return token
