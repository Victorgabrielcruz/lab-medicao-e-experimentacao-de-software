"""Dashboard Streamlit das três RQs. Execute: python -m streamlit run src/dashboard/app.py."""
from __future__ import annotations

import csv
import io
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import altair as alt  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from src.analysis.data_loading import (  # noqa: E402
    DEFAULT_DATASET_PATH, DatasetNotAuthorizedError, load_validated_dataset,
)
from src.dashboard.figures import COLORS, METRICS, _pairs, _ordered, render_dashboard  # noqa: E402

TRIAL_COLUMNS = (
    "trial_id", "participant_id", "difficulty_block", "kata_id", "treatment",
    "duration_seconds", "censored", "completed", "success_rate", "passed_tests",
    "total_tests", "mean_cyclomatic_complexity", "duplication_percentage", "loc",
)
STRUCTURAL = ("mean_cyclomatic_complexity", "duplication_percentage", "loc")
PAIR_COLORS = {"P01": "#7651a8", "P02": "#2a8a63", "P03": "#aa6531"}


def _csv_bytes(records: list[dict[str, Any]], columns: tuple[str, ...]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    writer.writerows({column: row.get(column) for column in columns} for row in records)
    return buffer.getvalue().encode("utf-8-sig")


def _trial_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame([
        {**{column: row.get(column) for column in TRIAL_COLUMNS},
         "treatment_label": "IA" if row["treatment"] == "ai" else "Manual",
         "censor_label": "Censurado" if row.get("censored") else "Observado",
         "completed_number": None if row.get("completed") is None else int(row["completed"])}
        for row in _ordered(rows)
    ])


def _point_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    records = []
    for treatment, center in (("ai", 0), ("manual", 1)):
        members = [row for row in _ordered(rows) if row["treatment"] == treatment]
        for index, row in enumerate(members):
            records.append({**row, "x_position": center + (index - (len(members) - 1) / 2) * 0.09,
                            "treatment_label": "IA" if treatment == "ai" else "Manual",
                            "censor_label": "Censurado" if row.get("censored") else "Observado",
                            "completed_number": None if row.get("completed") is None else int(row["completed"])})
    return pd.DataFrame(records)


def _pair_frame(rows: list[dict[str, Any]], metric: str) -> pd.DataFrame:
    records = []
    pairs = _pairs(rows)
    for index, pair in enumerate(pairs):
        offset = (index - (len(pairs) - 1) / 2) * 0.09
        for treatment, center in (("ai", 0), ("manual", 1)):
            row = pair[treatment]
            if row is None or row.get(metric) is None:
                continue
            records.append({"pair_id": f"{pair['participant_id']}/{pair['difficulty_block']}",
                            "participant_id": pair["participant_id"],
                            "trial_id": row["trial_id"],
                            "treatment_label": "IA" if treatment == "ai" else "Manual",
                            "x_position": center + offset, "value": float(row[metric]),
                            "censor_label": "Censurado" if row.get("censored") else "Observado"})
    return pd.DataFrame(records)


def _axis_x() -> alt.X:
    return alt.X("x_position:Q", title="Tratamento", scale=alt.Scale(domain=[-0.45, 1.45]),
                 axis=alt.Axis(values=[0, 1], labelExpr="datum.value == 0 ? 'IA' : 'Manual'"))


def _treatment_color() -> alt.Color:
    return alt.Color("treatment_label:N", title="Tratamento",
                     scale=alt.Scale(domain=["IA", "Manual"], range=[COLORS["ai"], COLORS["manual"]]))


def _participant_color() -> alt.Color:
    return alt.Color("participant_id:N", title="Participante",
                     scale=alt.Scale(domain=list(PAIR_COLORS), range=list(PAIR_COLORS.values())))


def _strip_chart(frame: pd.DataFrame, metric: str) -> alt.Chart:
    field = "completed_number" if metric == "completed" else metric
    tooltip = ["trial_id:N", "participant_id:N", "difficulty_block:N", "treatment_label:N",
               alt.Tooltip(f"{field}:Q", title=METRICS[metric][1])]
    if metric == "duration_seconds":
        tooltip.append("censor_label:N")
    return (alt.Chart(frame[frame[field].notna()]).mark_point(filled=True, size=100, opacity=0.88)
            .encode(x=_axis_x(), y=alt.Y(f"{field}:Q", title=METRICS[metric][1]),
                    color=_treatment_color(),
                    shape=alt.Shape("censor_label:N", title="Censura") if metric == "duration_seconds" else alt.value("circle"),
                    tooltip=tooltip)
            .properties(height=310, title=METRICS[metric][0]))


def _paired_chart(rows: list[dict[str, Any]], metric: str) -> alt.LayerChart | None:
    frame = _pair_frame(rows, metric)
    if frame.empty:
        return None
    complete = set(frame.groupby("pair_id").filter(lambda group: len(group) == 2)["pair_id"])
    lines = alt.Chart(frame[frame["pair_id"].isin(complete)]).mark_line(opacity=0.65).encode(
        x=_axis_x(), y=alt.Y("value:Q", title=METRICS[metric][1]),
        detail="pair_id:N", color=_participant_color())
    points = alt.Chart(frame).mark_point(filled=True, size=90).encode(
        x=_axis_x(), y=alt.Y("value:Q", title=METRICS[metric][1]),
        color=_participant_color(),
        shape=alt.Shape("censor_label:N", title="Censura") if metric == "duration_seconds" else alt.value("circle"),
        tooltip=["pair_id:N", "trial_id:N", "treatment_label:N",
                 alt.Tooltip("value:Q", title=METRICS[metric][1]), "censor_label:N"])
    return (lines + points).properties(height=330, title=f"Pares por participante/bloco · {METRICS[metric][0]}")


def _overview(frame: pd.DataFrame) -> alt.Chart:
    return (alt.Chart(frame[frame["duration_seconds"].notna()]).mark_point(filled=True, size=105)
            .encode(x=alt.X("duration_seconds:Q", title="Tempo observado (s)"),
                    y=alt.Y("trial_id:N", sort=frame["trial_id"].tolist(), title="Trial"),
                    color=_treatment_color(), shape=alt.Shape("censor_label:N", title="Censura"),
                    tooltip=["trial_id:N", "participant_id:N", "difficulty_block:N",
                             "treatment_label:N", "duration_seconds:Q", "censor_label:N"])
            .properties(height=max(400, len(frame) * 25), title=f"Visão geral · {len(frame)} trials"))


def _bundle(rows: list[dict[str, Any]]) -> bytes:
    """Recria as figuras do filtro atual sem reutilizar imagens antigas."""
    with tempfile.TemporaryDirectory(prefix="lab02-dashboard-") as directory:
        output = Path(directory)
        render_dashboard(rows, output)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(output.iterdir()):
                archive.write(path, arcname=path.name)
        return buffer.getvalue()


def main() -> None:
    st.set_page_config(page_title="Lab02 · Dashboard das RQs", layout="wide")
    st.title("Lab02 · Dashboard das RQs")
    try:
        rows = load_validated_dataset(DEFAULT_DATASET_PATH)
    except (DatasetNotAuthorizedError, OSError, ValueError) as error:
        st.error(f"Dataset oficial não autorizado: {error}")
        st.stop()

    participants = sorted({row["participant_id"] for row in rows})
    blocks = sorted({row["difficulty_block"] for row in rows})
    with st.sidebar:
        st.header("Filtros")
        selected_participants = st.multiselect("Participantes", participants, default=participants)
        selected_blocks = st.multiselect("Blocos", blocks, default=blocks)
        st.caption("Os filtros preservam os dois tratamentos de cada bloco selecionado.")
    filtered = [row for row in rows if row["participant_id"] in selected_participants
                and row["difficulty_block"] in selected_blocks]
    if not filtered:
        st.info("Selecione ao menos um participante e um bloco.")
        st.stop()

    frame, point_frame = _trial_frame(filtered), _point_frame(filtered)
    pairs = _pairs(filtered)
    structural_count = sum(row.get("mean_cyclomatic_complexity") is not None for row in filtered)
    structural_pairs = sum(bool(pair["ai"] and pair["manual"]
                                and pair["ai"].get("mean_cyclomatic_complexity") is not None
                                and pair["manual"].get("mean_cyclomatic_complexity") is not None)
                           for pair in pairs)
    for column, label, value in zip(
        st.columns(4), ("Trials", "Pares", "Censurados", "Métricas estruturais"),
        (len(filtered), len(pairs), sum(bool(row.get("censored")) for row in filtered),
         f"{structural_count}/{len(filtered)}"),
    ):
        column.metric(label, value)
    st.caption("Fonte: data/processed/trials.csv · validação oficial refeita nesta execução. "
               "Três participantes; pares do mesmo participante não são independentes.")

    overview, rq1, rq2, rq3, data = st.tabs(
        ("Visão geral", "RQ1 · tempo", "RQ2 · sucesso", "RQ3 · estrutura", "Dados e exportação"))
    with overview:
        st.altair_chart(_overview(frame))
        st.caption("Cada ponto é um trial. O marcador de censura identifica tempo limitado a 2.100 s.")
    with rq1:
        st.altair_chart(_strip_chart(point_frame, "duration_seconds"))
        chart = _paired_chart(filtered, "duration_seconds")
        if chart is not None:
            st.altair_chart(chart)
        st.caption("Linhas ligam IA e Manual do mesmo participante e bloco. Pontos coincidentes recebem deslocamento horizontal fixo.")
    with rq2:
        left, right = st.columns(2)
        with left:
            st.altair_chart(_strip_chart(point_frame, "success_rate"))
        with right:
            st.altair_chart(_strip_chart(point_frame, "completed"))
        st.caption("Conclusão: 1 = concluiu, 0 = não concluiu. Cada trial permanece visível.")
    with rq3:
        st.caption(f"{structural_count}/{len(filtered)} trials com métricas estruturais; "
                   f"{structural_pairs}/{len(pairs)} pares completos. Valores ausentes não viram zero.")
        for column, metric in zip(st.columns(2), STRUCTURAL[:2]):
            with column:
                st.altair_chart(_strip_chart(point_frame, metric))
        st.altair_chart(_strip_chart(point_frame, "loc"))
        selected_metric = st.selectbox("Comparação pareada", STRUCTURAL,
                                       format_func=lambda metric: METRICS[metric][0])
        chart = _paired_chart(filtered, selected_metric)
        if chart is not None:
            st.altair_chart(chart)
        st.caption("LOC acompanha a interpretação da complexidade e da duplicação; linhas exigem os dois lados medidos.")
    with data:
        st.dataframe(frame[list(TRIAL_COLUMNS)], hide_index=True)
        st.download_button("Baixar trials filtrados (CSV)", data=_csv_bytes(filtered, TRIAL_COLUMNS),
                           file_name="lab02-trials-filtrados.csv", mime="text/csv")
        pair_records = []
        for pair in pairs:
            for metric in METRICS:
                ai, manual = pair["ai"], pair["manual"]
                pair_records.append({"participant_id": pair["participant_id"],
                                     "difficulty_block": pair["difficulty_block"], "metric": metric,
                                     "unit": METRICS[metric][1],
                                     "ai_trial_id": ai["trial_id"] if ai else "",
                                     "manual_trial_id": manual["trial_id"] if manual else "",
                                     "ai_value": ai.get(metric) if ai else None,
                                     "manual_value": manual.get(metric) if manual else None})
        st.dataframe(pd.DataFrame(pair_records), hide_index=True)
        pair_columns = ("participant_id", "difficulty_block", "metric", "unit",
                        "ai_trial_id", "manual_trial_id", "ai_value", "manual_value")
        st.download_button("Baixar pares filtrados (CSV)", data=_csv_bytes(pair_records, pair_columns),
                           file_name="lab02-pares-filtrados.csv", mime="text/csv")
        filter_key = (tuple(selected_participants), tuple(selected_blocks))
        if st.session_state.get("bundle_filter") != filter_key:
            st.session_state.pop("bundle_bytes", None)
        if st.button("Preparar figuras PNG/SVG e CSVs"):
            with st.spinner("Gerando figuras a partir dos trials selecionados..."):
                st.session_state["bundle_bytes"] = _bundle(filtered)
                st.session_state["bundle_filter"] = filter_key
        if "bundle_bytes" in st.session_state:
            st.download_button("Baixar pacote de figuras e dados (ZIP)",
                               data=st.session_state["bundle_bytes"],
                               file_name="lab02-dashboard.zip", mime="application/zip")


if __name__ == "__main__":
    main()

