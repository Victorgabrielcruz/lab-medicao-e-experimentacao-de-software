from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
TRAINING = ROOT / "training-kata"


REFERENCE = '''
def expandir_mensagem(blocos):
    partes = []
    for texto, repeticoes in blocos:
        if not isinstance(texto, str) or not texto:
            raise ValueError("texto inválido")
        if isinstance(repeticoes, bool) or not isinstance(repeticoes, int):
            raise ValueError("repetições inválidas")
        if not 0 <= repeticoes <= 20:
            raise ValueError("repetições fora do limite")
        partes.append(texto * repeticoes)
    return "".join(partes)
'''.lstrip()


def _run_training(source: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["KATA_SRC_DIR"] = str(source)
    return subprocess.run(
        [sys.executable, "-m", "pytest", str(TRAINING / "tests"), "-q"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_esqueleto_de_treinamento_falha_e_referencia_passa(tmp_path: Path):
    assert _run_training(TRAINING / "src").returncode != 0
    reference_dir = tmp_path / "reference"
    reference_dir.mkdir()
    (reference_dir / "solution.py").write_text(REFERENCE, encoding="utf-8")
    result = _run_training(reference_dir)
    assert result.returncode == 0, result.stdout + result.stderr


def test_treinamento_nao_reutiliza_os_dominios_experimentais():
    statement = (TRAINING / "README.md").read_text(encoding="utf-8").lower()
    title_and_problem = statement.split("o problema exercita", 1)[0]
    for experimental_domain in (
        "doca",
        "compartimento",
        "remessa",
        "credencial",
        "sensor",
        "roteiro",
    ):
        assert experimental_domain not in title_and_problem
