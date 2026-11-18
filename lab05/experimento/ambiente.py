"""Registro do ambiente em que o experimento foi executado.

Desempenho depende da máquina: o registro acompanha os dados para que a
análise e as ameaças à validade possam citá-lo.
"""

import json
import os
import platform
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from experimento.config import DIR_DADOS


def registrar_ambiente(diretorio_banco: Path = DIR_DADOS) -> dict:
    """Coleta versões de software, hardware e disco usados na execução."""
    diretorio_banco = Path(diretorio_banco)
    diretorio_banco.mkdir(parents=True, exist_ok=True)
    disco = shutil.disk_usage(diretorio_banco)
    return {
        "data_hora_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sqlite_version": sqlite3.sqlite_version,
        "python_version": platform.python_version(),
        "python_implementacao": platform.python_implementation(),
        "sistema": platform.system(),
        "sistema_versao": platform.version(),
        "maquina": platform.machine(),
        "processador": platform.processor() or "desconhecido",
        "n_cpus": os.cpu_count(),
        "disco_total_gb": round(disco.total / 1024**3, 1),
        "disco_livre_gb": round(disco.free / 1024**3, 1),
        "diretorio_banco": str(diretorio_banco.resolve()),
        "executavel_python": sys.executable,
    }


def salvar_ambiente(caminho: Path, ambiente: dict | None = None) -> dict:
    """Grava o registro do ambiente em JSON e o retorna."""
    caminho = Path(caminho)
    ambiente = ambiente or registrar_ambiente(caminho.parent)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(ambiente, indent=2, ensure_ascii=False), encoding="utf-8")
    return ambiente
