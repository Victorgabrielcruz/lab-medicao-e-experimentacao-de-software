"""Aponta a suíte de treinamento para o diretório informado."""
import os
import sys
from pathlib import Path

_KATA_DIR = Path(__file__).resolve().parent.parent
_src_dir = Path(os.environ.get("KATA_SRC_DIR", _KATA_DIR / "src")).resolve()
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))
