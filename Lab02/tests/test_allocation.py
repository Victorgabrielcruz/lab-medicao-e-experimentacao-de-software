from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from src.collection.allocation import (
    BLOCKS,
    DEFAULT_SEED,
    KATAS,
    PARTICIPANTS,
    TREATMENT_SEQUENCES,
    AllocationError,
    freeze_allocation,
    generate_allocation,
    read_allocation,
    validate_allocation,
)


def test_mesma_semente_reproduz_exatamente_a_mesma_alocacao():
    assert generate_allocation(DEFAULT_SEED) == generate_allocation(DEFAULT_SEED)
    assert generate_allocation(DEFAULT_SEED + 1) != generate_allocation(DEFAULT_SEED)


def test_cada_participante_possui_seis_posicoes_katas_e_tres_por_tratamento():
    rows = generate_allocation()

    for participant in PARTICIPANTS:
        participant_rows = sorted(
            (row for row in rows if row.participant_id == participant),
            key=lambda row: row.order_position,
        )
        assert [row.order_position for row in participant_rows] == list(range(1, 7))
        assert {row.kata_id for row in participant_rows} == set(KATAS)
        assert tuple(row.treatment for row in participant_rows) == TREATMENT_SEQUENCES[participant]
        assert Counter(row.treatment for row in participant_rows) == {"ai": 3, "manual": 3}


def test_cada_bloco_tem_dois_tratamentos_e_nao_e_consecutivo():
    rows = generate_allocation()

    for participant in PARTICIPANTS:
        participant_rows = [row for row in rows if row.participant_id == participant]
        for block, pair in BLOCKS.items():
            block_rows = [row for row in participant_rows if row.difficulty_block == block]
            assert {row.kata_id for row in block_rows} == set(pair)
            assert {row.treatment for row in block_rows} == {"ai", "manual"}
            assert abs(block_rows[0].order_position - block_rows[1].order_position) > 1


def test_cada_kata_aparece_nos_dois_tratamentos_e_desigualdade_e_invertida():
    rows = generate_allocation()

    for block, pair in BLOCKS.items():
        first_ai = sum(
            row.kata_id == pair[0] and row.treatment == "ai" for row in rows
        )
        second_ai = sum(
            row.kata_id == pair[1] and row.treatment == "ai" for row in rows
        )
        assert sorted((first_ai, second_ai)) == [1, 2], block
        for kata in pair:
            assert {row.treatment for row in rows if row.kata_id == kata} == {
                "ai",
                "manual",
            }


def test_ordens_sao_diferentes_e_trial_ids_sao_unicos():
    rows = generate_allocation()
    orders = {
        participant: tuple(
            row.kata_id
            for row in sorted(
                (item for item in rows if item.participant_id == participant),
                key=lambda item: item.order_position,
            )
        )
        for participant in PARTICIPANTS
    }

    assert len(set(orders.values())) == 3
    assert len({row.trial_id for row in rows}) == 18


def test_validador_rejeita_bloco_incorreto_e_trial_id_inconsistente():
    rows = generate_allocation()
    rows[0] = replace(rows[0], difficulty_block="B2", trial_id="invalido")

    with pytest.raises(AllocationError, match="bloco incorreto"):
        validate_allocation(rows)


def test_arquivo_congelado_corresponde_a_semente_e_ao_hash():
    path = ROOT / "data/metadata/allocation.csv"
    metadata = json.loads(
        (ROOT / "data/metadata/allocation-metadata.json").read_text(encoding="utf-8")
    )

    assert read_allocation(path) == generate_allocation(metadata["seed"])
    assert metadata["seed"] == DEFAULT_SEED
    assert metadata["status"] == "frozen"
    assert metadata["trial_count"] == 18
    canonical = path.read_text(encoding="utf-8").encode("utf-8")
    assert hashlib.sha256(canonical).hexdigest() == metadata["canonical_csv_sha256"]


def test_congelamento_confirma_conteudo_identico_e_recusa_substituicao(tmp_path: Path):
    output = tmp_path / "allocation.csv"
    metadata = tmp_path / "allocation-metadata.json"
    rows = generate_allocation(DEFAULT_SEED)

    assert freeze_allocation(rows, output, metadata, DEFAULT_SEED) is True
    assert freeze_allocation(rows, output, metadata, DEFAULT_SEED) is False

    with pytest.raises(AllocationError, match="não será sobrescrita"):
        freeze_allocation(
            generate_allocation(DEFAULT_SEED + 1),
            output,
            metadata,
            DEFAULT_SEED + 1,
        )
