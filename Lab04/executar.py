"""Prepara o ambiente do Lab04 e inicia o dashboard em um comando (#277)."""

import argparse
import os
from pathlib import Path
import subprocess
import sys
import venv


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--porta", type=int, default=8501, help="porta local do dashboard")
    parser.add_argument(
        "--reproduzir", action="store_true",
        help="recria os dados a partir do snapshot e a simulação com a semente fixa antes de abrir",
    )
    args = parser.parse_args()
    if sys.version_info < (3, 12):
        parser.error("o Lab04 requer Python 3.12 ou superior")

    pasta = Path(__file__).resolve().parent
    ambiente = pasta / ".venv"
    python = ambiente / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

    def rodar(*argumentos: str) -> None:
        subprocess.run([str(python), *argumentos], cwd=pasta, check=True)

    try:
        if not python.is_file():
            venv.EnvBuilder(with_pip=True).create(ambiente)
        rodar("-m", "pip", "install", "--disable-pip-version-check", "-r", "requirements.txt")
        if args.reproduzir:
            rodar("-m", "hipotese.dados_reais")
            rodar("-m", "hipotese.simulacao")
        rodar(
            "-m", "streamlit", "run", "app.py",
            "--server.address=127.0.0.1", f"--server.port={args.porta}",
            "--server.headless=true", "--browser.gatherUsageStats=false",
        )
    except subprocess.CalledProcessError as erro:
        return erro.returncode
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
