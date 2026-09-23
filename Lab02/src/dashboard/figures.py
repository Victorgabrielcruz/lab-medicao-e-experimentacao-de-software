"""Gera figuras e dados do dashboard exclusivamente a partir do dataset validado."""
from __future__ import annotations

import csv
import html
from collections import defaultdict
from pathlib import Path
from typing import Any

from src.analysis.data_loading import DEFAULT_DATASET_PATH, load_validated_dataset

METRICS = {
    "duration_seconds": ("RQ1 · tempo", "Tempo (s)"),
    "success_rate": ("RQ2 · sucesso dos testes", "Testes aprovados (%)"),
    "completed": ("RQ2 · conclusão", "Concluído (0/1)"),
    "mean_cyclomatic_complexity": ("RQ3 · complexidade", "Complexidade ciclomática média (pontos)"),
    "duplication_percentage": ("RQ3 · duplicação", "Linhas duplicadas (%)"),
    "loc": ("RQ3 · tamanho", "LOC (linhas de código)"),
}
COLORS = {"ai": "#1769aa", "manual": "#d65f28"}
TREATMENTS = ("ai", "manual")
SOURCE = "Fonte: data/processed/trials.csv · dataset oficial validado"


def _ordered(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda r: (r["participant_id"], r["difficulty_block"], r["treatment"], r["trial_id"]))


def _pairs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        key = (row["participant_id"], row["difficulty_block"])
        if row["treatment"] in grouped[key]:
            raise ValueError(f"Tratamento duplicado no par {key}")
        grouped[key][row["treatment"]] = row
    pairs = []
    for (participant, block), treatments in sorted(grouped.items()):
        pairs.append({"participant_id": participant, "difficulty_block": block,
                      "ai": treatments.get("ai"), "manual": treatments.get("manual")})
    return pairs


def _value(row: dict[str, Any] | None, metric: str) -> float | None:
    if row is None or row.get(metric) is None:
        return None
    return float(row[metric])


def _save(fig, output: Path, name: str) -> None:
    import matplotlib.pyplot as plt

    fig.text(0.01, 0.015, SOURCE, fontsize=8, color="#555555")
    fig.savefig(output / f"{name}.png", dpi=170, bbox_inches="tight")
    fig.savefig(output / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


def _legend(ax, *, censored: bool = False, missing: bool = False) -> None:
    from matplotlib.lines import Line2D

    handles = [Line2D([], [], marker="o", linestyle="none", color=COLORS[t], label=("IA" if t == "ai" else "Manual"))
               for t in TREATMENTS]
    if censored:
        handles.append(Line2D([], [], marker="X", linestyle="none", color="#222222", label="Censurado"))
    if missing:
        handles.append(Line2D([], [], marker="x", linestyle="none", color="#888888", label="Métrica ausente"))
    ax.legend(handles=handles, loc="best", fontsize=8)


def _strip(ax, rows: list[dict[str, Any]], metric: str, *, censored: bool = False) -> None:
    """Deslocamento fixo por trial: pontos coincidentes continuam visíveis."""
    ordered = _ordered(rows)
    by_treatment = {t: [r for r in ordered if r["treatment"] == t] for t in TREATMENTS}
    for position, treatment in enumerate(TREATMENTS):
        members = by_treatment[treatment]
        for index, row in enumerate(members):
            value = _value(row, metric)
            x = position + (index - (len(members) - 1) / 2) * 0.045
            if value is None:
                continue
            marker = "X" if censored and row.get("censored") else "o"
            ax.scatter(x, value, color=COLORS[treatment], marker=marker,
                       edgecolors="white" if marker == "o" else "none", linewidths=0.5,
                       s=64, zorder=3)
        missing = sum(_value(row, metric) is None for row in members)
        if missing:
            ax.text(position, 0.97, f"{missing} ausente(s)", transform=ax.get_xaxis_transform(),
                    ha="center", va="top", fontsize=8, color="#555555")
    ax.set_xticks((0, 1), ("IA", "Manual"))
    ax.set_xlim(-0.48, 1.48)
    ax.set_ylabel(METRICS[metric][1])
    ax.grid(axis="y", alpha=0.25)
    _legend(ax, censored=censored)


def _paired(ax, pairs: list[dict[str, Any]], metric: str, *, censored: bool = False) -> None:
    colors = {"P01": "#7651a8", "P02": "#2a8a63", "P03": "#aa6531"}
    for index, pair in enumerate(pairs):
        ai, manual = pair["ai"], pair["manual"]
        ai_value, manual_value = _value(ai, metric), _value(manual, metric)
        offset = (index - (len(pairs) - 1) / 2) * 0.045
        color = colors.get(pair["participant_id"], "#555555")
        if ai_value is not None and manual_value is not None:
            ax.plot([0 + offset, 1 + offset], [ai_value, manual_value], color=color,
                    linewidth=1.2, alpha=0.72, zorder=1)
        for position, row, value in ((0, ai, ai_value), (1, manual, manual_value)):
            if value is not None:
                marker = "X" if censored and row.get("censored") else "o"
                ax.scatter(position + offset, value, marker=marker, color=color, s=48, zorder=2)
        if ai_value is not None or manual_value is not None:
            label_value = manual_value if manual_value is not None else ai_value
            label_x = 1.06 if manual_value is not None else -0.08
            ax.text(label_x, label_value, f"{pair['participant_id']}/{pair['difficulty_block']}",
                    color=color, fontsize=7, va="center")
    ax.set_xticks((0, 1), ("IA", "Manual"))
    ax.set_xlim(-0.4, 1.72)
    ax.set_ylabel(METRICS[metric][1])
    ax.grid(axis="y", alpha=0.25)
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], color=color, marker="o", label=participant)
               for participant, color in colors.items()]
    if censored:
        handles.append(Line2D([], [], color="#222222", marker="X", linestyle="none", label="Censurado"))
    ax.legend(handles=handles, fontsize=8)


def _export_data(rows: list[dict[str, Any]], pairs: list[dict[str, Any]], output: Path) -> None:
    trial_columns = ("trial_id", "participant_id", "difficulty_block", "kata_id", "treatment",
                     "duration_seconds", "censored", "completed", "success_rate", "passed_tests",
                     "total_tests", "mean_cyclomatic_complexity", "duplication_percentage", "loc")
    with (output / "trial-points.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=trial_columns)
        writer.writeheader()
        for row in _ordered(rows):
            writer.writerow({column: row.get(column) for column in trial_columns})
    pair_columns = ("participant_id", "difficulty_block", "metric", "unit", "ai_trial_id",
                    "manual_trial_id", "ai_value", "manual_value", "ai_censored", "manual_censored")
    with (output / "paired-points.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=pair_columns)
        writer.writeheader()
        for pair in pairs:
            for metric in METRICS:
                ai, manual = pair["ai"], pair["manual"]
                writer.writerow({"participant_id": pair["participant_id"], "difficulty_block": pair["difficulty_block"],
                                 "metric": metric, "unit": METRICS[metric][1],
                                 "ai_trial_id": ai["trial_id"] if ai else "",
                                 "manual_trial_id": manual["trial_id"] if manual else "",
                                 "ai_value": _value(ai, metric), "manual_value": _value(manual, metric),
                                 "ai_censored": bool(ai and ai.get("censored")),
                                 "manual_censored": bool(manual and manual.get("censored"))})


def _render_index(rows: list[dict[str, Any]], output: Path) -> None:
    structural = sum(row.get("mean_cyclomatic_complexity") is not None for row in rows)
    censored = sum(bool(row.get("censored")) for row in rows)
    cards = [
        (f"Visão geral · {len(rows)} trials", "overview_trials"),
        ("RQ1 · tempo por tratamento", "rq1_duration"),
        ("RQ1 · tempo pareado", "rq1_paired"),
        ("RQ2 · sucesso e conclusão", "rq2_outcomes"),
        ("RQ3 · complexidade, duplicação e LOC", "rq3_structure"),
        ("RQ3 · métricas pareadas", "rq3_paired"),
    ]
    figures = "\n".join(
        f'<figure><h2>{html.escape(title)}</h2><a href="{name}.svg"><img src="{name}.svg" alt="{html.escape(title)}"></a>'
        f'<figcaption>Fonte: dataset oficial validado · <a href="{name}.png">PNG</a> · '
        f'<a href="{name}.svg">SVG</a></figcaption></figure>' for title, name in cards
    )
    document = f'''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lab02 · dashboard das RQs</title><style>
body{{font:16px/1.5 system-ui,sans-serif;max-width:1200px;margin:auto;padding:24px;color:#203040;background:#f5f7fa}}
figure{{background:white;padding:18px;margin:18px 0;border:1px solid #dce3e9;border-radius:8px}}
img{{max-width:100%;height:auto}}a{{color:#1769aa}}small,figcaption{{color:#52606d}}
</style></head><body><h1>Lab02 · dashboard das RQs</h1>
<p>{len(rows)} trials validados · {censored} censurado(s) · {structural}/{len(rows)} com métricas estruturais.
Pontos ausentes são identificados; não entram como zero.</p>
<p>Os pontos pertencem a três participantes. Linhas pareadas conectam o mesmo participante e bloco;
os gráficos não estabelecem independência estatística entre os nove pares.</p>
<p>Dados: <a href="trial-points.csv">trials (CSV)</a> · <a href="paired-points.csv">pares (CSV)</a>.
Fonte: <code>data/processed/trials.csv</code>, aprovado por <code>validate_dataset</code>.</p>
{figures}</body></html>'''
    (output / "index.html").write_text(document, encoding="utf-8")


def render_dashboard(rows: list[dict[str, Any]], output: Path) -> list[Path]:
    """Renderiza dados e figuras; o chamador deve passar linhas já validadas."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    ordered, pairs = _ordered(rows), _pairs(rows)
    _export_data(ordered, pairs, output)

    fig, ax = plt.subplots(figsize=(10, 7))
    for index, row in enumerate(ordered):
        value = _value(row, "duration_seconds")
        if value is not None:
            ax.scatter(value, index, color=COLORS[row["treatment"]],
                       marker="X" if row.get("censored") else "o", s=72)
    ax.set_yticks(range(len(ordered)), [row["trial_id"] for row in ordered], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Tempo observado (s)")
    ax.set_title(f"Visão geral · {len(ordered)} trials")
    ax.grid(axis="x", alpha=0.25)
    _legend(ax, censored=True)
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    _save(fig, output, "overview_trials")

    fig, ax = plt.subplots(figsize=(7, 5))
    _strip(ax, ordered, "duration_seconds", censored=True)
    ax.set_title("RQ1 · tempo por tratamento · cada ponto é um trial")
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    _save(fig, output, "rq1_duration")

    fig, ax = plt.subplots(figsize=(8, 5))
    _paired(ax, pairs, "duration_seconds", censored=True)
    ax.set_title("RQ1 · tempo por participante e bloco")
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    _save(fig, output, "rq1_paired")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    for ax, metric in zip(axes, ("success_rate", "completed")):
        _strip(ax, ordered, metric)
        ax.set_title(METRICS[metric][0])
        if metric == "success_rate":
            ax.set_ylim(-5, 105)
        else:
            ax.set_ylim(-0.1, 1.1)
    fig.suptitle("RQ2 · resultados individuais dos 18 trials")
    fig.tight_layout(rect=(0, 0.035, 1, 0.94))
    _save(fig, output, "rq2_outcomes")

    structural_metrics = ("mean_cyclomatic_complexity", "duplication_percentage", "loc")
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for ax, metric in zip(axes, structural_metrics):
        _strip(ax, ordered, metric)
        ax.set_title(METRICS[metric][0])
        ax.set_ylim(bottom=min(0, ax.get_ylim()[0]))
    fig.suptitle("RQ3 · métricas disponíveis; ausência identificada por tratamento")
    fig.tight_layout(rect=(0, 0.035, 1, 0.94))
    _save(fig, output, "rq3_structure")

    fig, axes = plt.subplots(1, 3, figsize=(17, 5))
    for ax, metric in zip(axes, structural_metrics):
        _paired(ax, pairs, metric)
        valid = sum(_value(pair["ai"], metric) is not None and _value(pair["manual"], metric) is not None
                    for pair in pairs)
        ax.set_title(f"{METRICS[metric][0]} · {valid}/{len(pairs)} pares")
    fig.suptitle("RQ3 · pares participante/bloco; lados sem medição ficam sem linha")
    fig.tight_layout(rect=(0, 0.035, 1, 0.94))
    _save(fig, output, "rq3_paired")

    _render_index(ordered, output)
    return [output / f"{name}.{extension}" for name in
            ("overview_trials", "rq1_duration", "rq1_paired", "rq2_outcomes", "rq3_structure", "rq3_paired")
            for extension in ("png", "svg")]


def generate(dataset: Path = DEFAULT_DATASET_PATH, output: Path | None = None) -> list[Path]:
    """Valida novamente o CSV oficial antes de criar qualquer arquivo de saída."""
    rows = load_validated_dataset(Path(dataset))
    destination = output if output is not None else Path(__file__).resolve().parents[2] / "reports/figures/dashboard"
    return render_dashboard(rows, Path(destination))


