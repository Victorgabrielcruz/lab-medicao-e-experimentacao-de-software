"""Aponta a suíte para a implementação que deve ser testada.

Por padrão, os testes importam de `../src/solution.py` (o esqueleto ou o
código de produção que o participante está editando). Para validar a suíte
contra outra implementação — a solução de referência, por exemplo — defina
a variável de ambiente KATA_SRC_DIR com o caminho do diretório alternativo
antes de rodar o pytest. É isso que `scripts/run_tests.py --src` faz.
"""
import os
import sys
from pathlib import Path

_KATA_DIR = Path(__file__).resolve().parent.parent
_src_dir = Path(os.environ.get("KATA_SRC_DIR", _KATA_DIR / "src")).resolve()

if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))
