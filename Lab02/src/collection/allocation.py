"""Geração e validação da alocação contrabalanceada dos 18 trials."""
from __future__ import annotations

import csv
import hashlib
import io
import itertools
import json
import random
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

DEFAULT_SEED = 20260910
ALGORITHM_VERSION = 1
PARTICIPANTS = ("P01", "P02", "P03")
BLOCKS = {
    "B1": ("K01", "K02"),
    "B2": ("K03", "K04"),
    "B3": ("K05", "K06"),
}
KATAS = tuple(kata for pair in BLOCKS.values() for kata in pair)
KATA_BLOCK = {kata: block for block, pair in BLOCKS.items() for kata in pair}
TREATMENT_SEQUENCES = {
    "P01": ("ai", "manual", "ai", "manual", "ai", "manual"),
    "P02": ("manual", "ai", "manual", "ai", "manual", "ai"),
    "P03": ("ai", "manual", "manual", "ai", "ai", "manual"),
}
CSV_FIELDS = (
    "trial_id",
    "participant_id",
    "order_position",
    "kata_id",
    "difficulty_block",
    "treatment",
)


class AllocationError(RuntimeError):
    """Erro de geração, validação ou congelamento da alocação."""


@dataclass(frozen=True)
class AllocationRow:
    trial_id: str
    participant_id: str
    order_position: int
    kata_id: str
    difficulty_block: str
    treatment: str


def _valid_orders(participant: str) -> list[tuple[str, ...]]:
    treatments = TREATMENT_SEQUENCES[participant]
    valid: list[tuple[str, ...]] = []
    for order in itertools.permutations(KATAS):
        positions = {kata: index for index, kata in enumerate(order)}
        if any(
            abs(positions[first] - positions[second]) == 1
            for first, second in BLOCKS.values()
        ):
            continue
        if any(
            {treatments[positions[first]], treatments[positions[second]]}
            != {"ai", "manual"}
            for first, second in BLOCKS.values()
        ):
            continue
        valid.append(order)
    return valid


def _has_group_balance(orders: dict[str, tuple[str, ...]]) -> bool:
    exposures = {kata: set() for kata in KATAS}
    for participant, order in orders.items():
        for position, kata in enumerate(order):
            exposures[kata].add(TREATMENT_SEQUENCES[participant][position])
    return all(exposures[kata] == {"ai", "manual"} for kata in KATAS)


def generate_allocation(seed: int = DEFAULT_SEED) -> list[AllocationRow]:
    """Sorteia uma solução válida usando somente a semente informada."""
    rng = random.Random(seed)
    candidates = {participant: _valid_orders(participant) for participant in PARTICIPANTS}
    for participant in PARTICIPANTS:
        rng.shuffle(candidates[participant])

    selected: dict[str, tuple[str, ...]] | None = None
    for p01_order in candidates["P01"]:
        for p02_order in candidates["P02"]:
            if p02_order == p01_order:
                continue
            for p03_order in candidates["P03"]:
                if p03_order in {p01_order, p02_order}:
                    continue
                proposal = {"P01": p01_order, "P02": p02_order, "P03": p03_order}
                if _has_group_balance(proposal):
                    selected = proposal
                    break
            if selected is not None:
                break
        if selected is not None:
            break

    if selected is None:
        raise AllocationError(f"Nenhuma alocação válida encontrada para a semente {seed}")

    rows = [
        AllocationRow(
            trial_id=f"{participant}-{kata}-{treatment}",
            participant_id=participant,
            order_position=position,
            kata_id=kata,
            difficulty_block=KATA_BLOCK[kata],
            treatment=treatment,
        )
        for participant in PARTICIPANTS
        for position, (kata, treatment) in enumerate(
            zip(selected[participant], TREATMENT_SEQUENCES[participant]), start=1
        )
    ]
    validate_allocation(rows)
    return rows


def validate_allocation(rows: Iterable[AllocationRow]) -> None:
    """Valida todas as restrições pré-registradas, acumulando os erros."""
    rows = list(rows)
    errors: list[str] = []
    if len(rows) != 18:
        errors.append("a alocação deve conter exatamente 18 trials")
    if len({row.trial_id for row in rows}) != len(rows):
        errors.append("trial_id deve ser único")

    orders: dict[str, tuple[str, ...]] = {}
    for participant in PARTICIPANTS:
        participant_rows = sorted(
            (row for row in rows if row.participant_id == participant),
            key=lambda row: row.order_position,
        )
        if len(participant_rows) != 6:
            errors.append(f"{participant} deve possuir seis posições")
            continue
        if [row.order_position for row in participant_rows] != list(range(1, 7)):
            errors.append(f"{participant} deve possuir posições de 1 a 6")
        if {row.kata_id for row in participant_rows} != set(KATAS):
            errors.append(f"{participant} deve executar cada kata exatamente uma vez")
        actual_treatments = tuple(row.treatment for row in participant_rows)
        if actual_treatments != TREATMENT_SEQUENCES[participant]:
            errors.append(f"{participant} não respeita a sequência de tratamentos")
        if actual_treatments.count("ai") != 3 or actual_treatments.count("manual") != 3:
            errors.append(f"{participant} deve possuir três trials por tratamento")

        for block, pair in BLOCKS.items():
            block_rows = [row for row in participant_rows if row.difficulty_block == block]
            if len(block_rows) != 2 or {row.kata_id for row in block_rows} != set(pair):
                errors.append(f"{participant} deve executar as duas katas de {block}")
                continue
            if {row.treatment for row in block_rows} != {"ai", "manual"}:
                errors.append(f"{participant} deve usar os dois tratamentos em {block}")
            if abs(block_rows[0].order_position - block_rows[1].order_position) == 1:
                errors.append(f"{participant} possui katas consecutivas do bloco {block}")
        orders[participant] = tuple(row.kata_id for row in participant_rows)

    if len(set(orders.values())) != len(orders):
        errors.append("a ordem das katas deve ser diferente entre participantes")

    for kata in KATAS:
        kata_rows = [row for row in rows if row.kata_id == kata]
        if len(kata_rows) != 3:
            errors.append(f"{kata} deve aparecer uma vez por participante")
        if {row.treatment for row in kata_rows} != {"ai", "manual"}:
            errors.append(f"{kata} deve aparecer nos dois tratamentos no grupo")

    for row in rows:
        if row.difficulty_block != KATA_BLOCK.get(row.kata_id):
            errors.append(f"bloco incorreto em {row.trial_id}")
        expected_id = f"{row.participant_id}-{row.kata_id}-{row.treatment}"
        if row.trial_id != expected_id:
            errors.append(f"trial_id inconsistente: {row.trial_id}")

    if errors:
        raise AllocationError("Alocação inválida:\n- " + "\n- ".join(dict.fromkeys(errors)))


def serialize_csv(rows: Iterable[AllocationRow]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(asdict(row))
    return stream.getvalue()


def read_allocation(path: Path) -> list[AllocationRow]:
    with path.open(encoding="utf-8", newline="") as file:
        rows = [
            AllocationRow(
                trial_id=row["trial_id"],
                participant_id=row["participant_id"],
                order_position=int(row["order_position"]),
                kata_id=row["kata_id"],
                difficulty_block=row["difficulty_block"],
                treatment=row["treatment"],
            )
            for row in csv.DictReader(file)
        ]
    validate_allocation(rows)
    return rows


def freeze_allocation(
    rows: list[AllocationRow],
    output: Path,
    metadata_path: Path,
    seed: int,
) -> bool:
    """Grava uma alocação nova ou confirma que a já congelada é idêntica."""
    validate_allocation(rows)
    content = serialize_csv(rows)
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    if output.exists():
        if output.read_text(encoding="utf-8") != content:
            raise AllocationError(
                f"A alocação congelada em {output} é diferente e não será sobrescrita"
            )
        if not metadata_path.exists():
            raise AllocationError(f"Metadados da alocação ausentes: {metadata_path}")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("seed") != seed or metadata.get("canonical_csv_sha256") != digest:
            raise AllocationError("Metadados não correspondem à alocação congelada")
        return False

    output.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    metadata = {
        "schema_version": 1,
        "algorithm_version": ALGORITHM_VERSION,
        "seed": seed,
        "frozen_at": date.today().isoformat(),
        "python_version": ".".join(map(str, sys.version_info[:3])),
        "canonical_csv_sha256": digest,
        "trial_count": len(rows),
        "participants": list(PARTICIPANTS),
        "status": "frozen",
    }
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return True
