"""Preparação reproduzível de diretórios limpos para os trials."""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from .allocation import AllocationRow, read_allocation

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ALLOCATION = ROOT / "data/metadata/allocation.csv"
DEFAULT_KATAS_ROOT = ROOT / "katas"
DEFAULT_TRIALS_ROOT = ROOT / "trials"
DEFAULT_RAW_ROOT = ROOT / "data/raw/trials"


class TrialPreparationError(RuntimeError):
    """Erro controlado de validação ou preparação de um trial."""


def _source_digest(source_dir: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in source_dir.rglob("*") if item.is_file()):
        digest.update(path.relative_to(source_dir).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def find_allocation(
    participant_id: str,
    kata_id: str,
    treatment: str,
    allocation_path: Path = DEFAULT_ALLOCATION,
) -> AllocationRow:
    """Localiza a combinação exata no plano congelado."""
    matches = [
        row
        for row in read_allocation(Path(allocation_path))
        if row.participant_id == participant_id
        and row.kata_id == kata_id
        and row.treatment == treatment
    ]
    if len(matches) != 1:
        raise TrialPreparationError(
            f"Combinação ausente da alocação congelada: {participant_id}/{kata_id}/{treatment}"
        )
    return matches[0]


def prepare_trial(
    participant_id: str,
    kata_id: str,
    treatment: str,
    *,
    allocation_path: Path = DEFAULT_ALLOCATION,
    katas_root: Path = DEFAULT_KATAS_ROOT,
    trials_root: Path = DEFAULT_TRIALS_ROOT,
    raw_root: Path = DEFAULT_RAW_ROOT,
    restore: bool = False,
) -> Path:
    """Cria ou restaura atomicamente o diretório limpo de um trial.

    A restauração exige ``restore=True`` e nunca é permitida após a existência
    de evidência bruta, evitando apagar o código associado a uma coleta.
    """
    row = find_allocation(participant_id, kata_id, treatment, allocation_path)
    katas_root = Path(katas_root).resolve()
    trials_root = Path(trials_root).resolve()
    raw_root = Path(raw_root).resolve()
    source_dir = (katas_root / kata_id / "src").resolve()
    statement = (katas_root / kata_id / "README.md").resolve()
    if not source_dir.is_dir() or not statement.is_file():
        raise TrialPreparationError(f"Esqueleto incompleto para {kata_id}")

    trials_root.mkdir(parents=True, exist_ok=True)
    target = (trials_root / row.trial_id).resolve()
    if target.parent != trials_root:
        raise TrialPreparationError(f"Destino inseguro fora de trials/: {target}")
    if (raw_root / row.trial_id).exists():
        raise TrialPreparationError(
            f"O trial {row.trial_id} já possui evidência bruta e não pode ser restaurado"
        )
    if target.exists() and not restore:
        raise TrialPreparationError(
            f"Diretório já existe: {target}; use --restore antes do início oficial"
        )

    stage = Path(tempfile.mkdtemp(prefix=f".{row.trial_id}-", dir=trials_root))
    try:
        shutil.copytree(source_dir, stage / "src")
        shutil.copy2(statement, stage / "README.md")
        config = {
            "schema_version": 1,
            "trial_id": row.trial_id,
            "participant_id": row.participant_id,
            "kata_id": row.kata_id,
            "difficulty_block": row.difficulty_block,
            "order_position": row.order_position,
            "treatment": row.treatment,
            "prepared_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "source_sha256": _source_digest(source_dir),
            "source": f"katas/{kata_id}/src",
            "treatment_verification_required": True,
        }
        (stage / "trial-config.json").write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if target.exists():
            shutil.rmtree(target)
        stage.replace(target)
    except Exception:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    return target
