"""Consolidação descritiva e inferencial das três questões de pesquisa.

Usa apenas a biblioteca padrão. Os valores de p são exatos por enumeração
dos sinais dos postos não nulos; os intervalos são bootstrap exploratório
por participante, para não reamostrar blocos como indivíduos independentes.
"""

from __future__ import annotations

import csv
import itertools
import json
import math
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from xml.etree import ElementTree


@dataclass(frozen=True)
class Metric:
    rq: str
    name: str
    unit: str
    direction: str
    primary: bool = False
    inferential: bool = False


METRICS = (
    Metric("RQ1", "duration_seconds", "s", "manual-ai", True, True),
    Metric("RQ1", "completed", "0/1", "ai-manual"),
    Metric("RQ2", "success_rate", "%", "ai-manual", True, True),
    Metric("RQ2", "failed_tests", "tests", "manual-ai"),
    Metric("RQ3", "mean_cyclomatic_complexity", "points", "ai-manual", True, True),
    Metric("RQ3", "duplication_percentage", "%", "ai-manual", True, True),
    Metric("RQ3", "loc", "lines", "ai-manual"),
    Metric("RQ3", "maintainability_index", "points", "ai-manual"),
)

FIELDNAMES = (
    "rq", "metric", "unit", "row_type", "participant_id", "difficulty_block",
    "treatment", "manual_trial_id", "ai_trial_id", "n_expected", "n_valid",
    "n_missing", "n_pairs", "n_ties", "n_nonzero", "n_participants",
    "median", "q1", "q3", "iqr", "minimum", "maximum", "manual_value",
    "ai_value", "difference", "p_value", "p_holm", "rank_biserial",
    "ci_low", "ci_high", "ci_method", "note",
)


def number(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = float(value)
    except (ValueError, TypeError):
        return None
    return result if math.isfinite(result) else None


def percentile(values: list[float], percent: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * percent
    lower = math.floor(position)
    upper = math.ceil(position)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def describe(values: list[float]) -> dict[str, float | None]:
    q1, q3 = percentile(values, 0.25), percentile(values, 0.75)
    return {
        "median": percentile(values, 0.5), "q1": q1, "q3": q3,
        "iqr": q3 - q1 if q1 is not None and q3 is not None else None,
        "minimum": min(values) if values else None,
        "maximum": max(values) if values else None,
    }


def wilcoxon_exact(differences: list[float], alternative: str) -> dict[str, float | int | None]:
    """Postos médios para empates; zeros excluídos; enumeração exata condicional."""
    nonzero = [(abs(value), value > 0) for value in differences if not math.isclose(value, 0, abs_tol=1e-12)]
    ties = len(differences) - len(nonzero)
    if not nonzero:
        return {"n_ties": ties, "n_nonzero": 0, "p_value": None, "rank_biserial": None}
    ordered = sorted(nonzero, key=lambda item: item[0])
    ranks: list[float] = []
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and math.isclose(ordered[end][0], ordered[index][0], abs_tol=1e-12):
            end += 1
        ranks.extend([(index + 1 + end) / 2] * (end - index))
        index = end
    observed_plus = sum(rank for rank, (_, positive) in zip(ranks, ordered) if positive)
    total = sum(ranks)
    distribution = [sum(rank for rank, positive in zip(ranks, signs) if positive)
                    for signs in itertools.product((False, True), repeat=len(ranks))]
    epsilon = 1e-10
    if alternative == "greater":
        extreme = sum(value >= observed_plus - epsilon for value in distribution)
    else:
        extreme = sum(abs(value - total / 2) >= abs(observed_plus - total / 2) - epsilon
                      for value in distribution)
    return {
        "n_ties": ties, "n_nonzero": len(nonzero),
        "p_value": extreme / len(distribution),
        "rank_biserial": (2 * observed_plus - total) / total,
    }


def bootstrap_interval(pairs: list[dict]) -> tuple[float | None, float | None]:
    """IC exploratório dos pares, consistente com os relatórios RQ1-RQ3."""
    differences = [pair["difference"] for pair in pairs]
    if len(differences) < 2:
        return None, None
    rng = random.Random(20260910)
    count = 10_000
    sample_size = len(differences)
    samples = sorted(median(differences[rng.randrange(sample_size)]
                            for _ in range(sample_size)) for _ in range(count))
    return samples[int(0.025 * count)], samples[int(0.975 * count)]


def read_json(path: Path) -> dict | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ValueError(f"JSON inválido em {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Objeto JSON esperado em {path}")
    return value


def junit_counts(path: Path) -> tuple[int, int, int] | None:
    """Retorna (total, passando, falhando), sem confundir testes ignorados com sucesso."""
    if not path.exists():
        return None
    try:
        root = ElementTree.parse(path).getroot()
        suites = [root] if root.tag == "testsuite" else root.findall(".//testsuite")
        if not suites:
            return None
        total = sum(int(suite.attrib["tests"]) for suite in suites)
        failed = sum(int(suite.attrib.get("failures", 0)) + int(suite.attrib.get("errors", 0))
                     for suite in suites)
        skipped = sum(int(suite.attrib.get("skipped", 0)) for suite in suites)
        if min(total, failed, skipped) < 0 or failed + skipped > total:
            return None
        return total, total - failed - skipped, failed
    except (ElementTree.ParseError, KeyError, ValueError):
        return None


def corrected_trial(raw: dict, note: dict | None, trial_id: str) -> tuple[dict | None, str]:
    """Só aceita retificação auditada que corresponde a uma medição registrada."""
    trial = dict(raw)
    annotation = ""
    if note and "corrected_interpretation" in note:
        if note.get("trial_id") != trial_id:
            return None, "nota de qualidade com trial_id divergente"
        correction = note["corrected_interpretation"]
        expected = {"completed", "censored", "duration_seconds", "total_tests",
                    "passed_tests", "failed_tests", "success_rate"}
        if not expected <= correction.keys():
            return None, "nota de qualidade incompleta"
        matching_attempts = [attempt for attempt in raw.get("attempts", [])
                             if attempt.get("note") != "final_check"
                             and all(attempt.get(field) == correction[field]
                                     for field in ("total_tests", "passed_tests", "failed_tests"))]
        if not matching_attempts:
            return None, "correção sem medição registrada nos attempts"
        trial.update({field: correction[field] for field in expected})
        annotation = "correção auditada por data-quality-note.json e poll registrado"
    return trial, annotation


def load_trials(root: Path) -> tuple[list[dict], list[str]]:
    allocation_path = root / "data/metadata/allocation.csv"
    with allocation_path.open(encoding="utf-8-sig", newline="") as handle:
        allocation = list(csv.DictReader(handle))
    if len({row["trial_id"] for row in allocation}) != len(allocation):
        raise ValueError("trial_id duplicado na alocação")
    trials: list[dict] = []
    warnings: list[str] = []
    for row in allocation:
        trial_id = row["trial_id"]
        raw_dir = root / "data/raw/trials" / trial_id
        raw = read_json(raw_dir / "trial.json")
        note = read_json(raw_dir / "data-quality-note.json")
        item = {**row, "values": {}, "source_note": ""}
        if raw is None:
            warnings.append(f"{trial_id}: trial.json ausente ou vazio")
            trials.append(item)
            continue
        if any(raw.get(key) != row[key] for key in ("trial_id", "participant_id", "kata_id", "treatment")):
            warnings.append(f"{trial_id}: identidade divergente da alocação; trial excluído")
            trials.append(item)
            continue
        junit = junit_counts(raw_dir / "final_junit.xml")
        if junit is None:
            warnings.append(f"{trial_id}: JUnit final ausente ou inválido; trial excluído")
            trials.append(item)
            continue
        raw_counts = tuple(raw.get(field) for field in ("total_tests", "passed_tests", "failed_tests"))
        if raw_counts != junit:
            warnings.append(f"{trial_id}: contagens brutas divergem do JUnit final; trial excluído")
            trials.append(item)
            continue
        trial, annotation = corrected_trial(raw, note, trial_id)
        if trial is None:
            warnings.append(f"{trial_id}: {annotation}; trial excluído")
            trials.append(item)
            continue
        duration = number(trial.get("duration_seconds"))
        total, passed, failed = (number(trial.get(key)) for key in
                                 ("total_tests", "passed_tests", "failed_tests"))
        completed, censored = trial.get("completed"), trial.get("censored")
        valid = (duration is not None and 0 <= duration <= 2100
                 and all(value is not None and value.is_integer() and value >= 0
                         for value in (total, passed, failed))
                 and total > 0 and passed + failed == total
                 and isinstance(completed, bool) and isinstance(censored, bool)
                 and not (completed and censored)
                 and (not completed or failed == 0)
                 and (not censored or duration == 2100))
        if not valid:
            warnings.append(f"{trial_id}: tempo, conclusão ou contagens incoerentes; trial excluído")
            trials.append(item)
            continue
        recorded_rate = number(trial.get("success_rate"))
        calculated_rate = passed / total * 100
        if recorded_rate is not None and abs(recorded_rate - calculated_rate) > 0.02:
            warnings.append(f"{trial_id}: taxa de sucesso incoerente; trial excluído")
            trials.append(item)
            continue
        item["values"].update(duration_seconds=duration, completed=float(completed),
                              success_rate=calculated_rate, failed_tests=failed)
        item["censored"] = censored
        item["source_note"] = annotation
        if annotation:
            warnings.append(f"{trial_id}: {annotation}; bruto preservado")
            corrected_counts = tuple(trial[field] for field in
                                     ("total_tests", "passed_tests", "failed_tests"))
            if corrected_counts != junit:
                warnings.append(f"{trial_id}: JUnit final registra {junit[1]}/{junit[0]} "
                                f"passando; análise usa {corrected_counts[1]}/{corrected_counts[0]} "
                                "do poll documentado")
        metrics = read_json(root / "data/raw/metrics" / trial_id / "metrics.json")
        if metrics is None:
            warnings.append(f"{trial_id}: métricas estáticas ausentes")
        elif metrics.get("trial_id") != trial_id:
            warnings.append(f"{trial_id}: identidade divergente nas métricas estáticas")
        else:
            complexity = metrics.get("complexity", {})
            duplication = metrics.get("duplication", {})
            maintainability = metrics.get("maintainability", {})
            mapping = {
                "mean_cyclomatic_complexity": complexity.get("mean_cyclomatic_complexity")
                    if not complexity.get("missing") else None,
                "duplication_percentage": duplication.get("duplication_percentage"),
                "loc": metrics.get("loc", {}).get("loc"),
                "maintainability_index": maintainability.get("maintainability_index")
                    if not maintainability.get("missing") else None,
            }
            for name, raw_value in mapping.items():
                value = number(raw_value)
                if value is not None and value >= 0:
                    item["values"][name] = value
                else:
                    warnings.append(f"{trial_id}: {name} ausente ou inválida")
        trials.append(item)
    return trials, warnings


def pair_rows(trials: list[dict], metric: Metric) -> tuple[list[dict], list[dict]]:
    grouped: dict[tuple[str, str], dict[str, dict]] = defaultdict(dict)
    for trial in trials:
        key = (trial["participant_id"], trial["difficulty_block"])
        if trial["treatment"] in grouped[key]:
            raise ValueError(f"Tratamento duplicado no par {key}")
        grouped[key][trial["treatment"]] = trial
    pairs = []
    export = []
    for (participant, block), group in sorted(grouped.items()):
        manual, ai = group.get("manual"), group.get("ai")
        manual_value = manual["values"].get(metric.name) if manual else None
        ai_value = ai["values"].get(metric.name) if ai else None
        difference = None
        if manual_value is not None and ai_value is not None:
            difference = (manual_value - ai_value if metric.direction == "manual-ai"
                          else ai_value - manual_value)
            pairs.append({"participant_id": participant, "difficulty_block": block,
                          "difference": difference})
        export.append({"row_type": "pair", "participant_id": participant,
                       "difficulty_block": block,
                       "manual_trial_id": manual["trial_id"] if manual else "",
                       "ai_trial_id": ai["trial_id"] if ai else "",
                       "n_expected": 1, "n_valid": int(difference is not None),
                       "n_missing": int(difference is None), "n_pairs": int(difference is not None),
                       "manual_value": manual_value, "ai_value": ai_value,
                       "difference": difference,
                       "note": "; ".join(filter(None, (manual.get("source_note", "") if manual else "",
                                                          ai.get("source_note", "") if ai else "")))})
    return pairs, export


def clean_row(metric: Metric, values: dict) -> dict:
    row = dict.fromkeys(FIELDNAMES, "")
    row.update(rq=metric.rq, metric=metric.name, unit=metric.unit,
               note="", ci_method="")
    for key, value in values.items():
        if isinstance(value, float):
            row[key] = f"{value:.4f}" if math.isfinite(value) else ""
        elif value is not None:
            row[key] = value
    return row


def analyze(trials: list[dict]) -> tuple[list[dict], dict[str, dict]]:
    participants = sorted({trial["participant_id"] for trial in trials})
    output: list[dict] = []
    comparisons: dict[str, dict] = {}
    for metric in METRICS:
        selected = [trial for trial in trials if metric.name in trial["values"]]
        for treatment in ("manual", "ai"):
            expected = [trial for trial in trials if trial["treatment"] == treatment]
            observed = [trial["values"][metric.name] for trial in selected
                        if trial["treatment"] == treatment]
            output.append(clean_row(metric, {"row_type": "treatment", "treatment": treatment,
                                             "n_expected": len(expected), "n_valid": len(observed),
                                             "n_missing": len(expected) - len(observed),
                                             **describe(observed)}))
            for participant in participants:
                subset = [trial for trial in expected if trial["participant_id"] == participant]
                values = [trial["values"][metric.name] for trial in subset
                          if metric.name in trial["values"]]
                output.append(clean_row(metric, {"row_type": "participant_treatment",
                                                 "participant_id": participant,
                                                 "treatment": treatment,
                                                 "n_expected": len(subset), "n_valid": len(values),
                                                 "n_missing": len(subset) - len(values),
                                                 **describe(values)}))
        pairs, pair_export = pair_rows(trials, metric)
        output.extend(clean_row(metric, row) for row in pair_export)
        differences = [pair["difference"] for pair in pairs]
        alternative = "greater" if metric.rq in ("RQ1", "RQ2") else "two-sided"
        inferential = wilcoxon_exact(differences, alternative) if metric.inferential else {}
        low, high = bootstrap_interval(pairs) if metric.inferential else (None, None)
        summary = {"row_type": "comparison", "n_expected": len(pair_export),
                   "n_valid": len(pairs), "n_missing": len(pair_export) - len(pairs),
                   "n_pairs": len(pairs), "n_participants": len({p["participant_id"] for p in pairs}),
                   "difference": median(differences) if differences else None,
                   "ci_low": low, "ci_high": high,
                   "ci_method": "pair_bootstrap_95_exploratory" if low is not None else "",
                   "note": "Wilcoxon exploratório: pares do mesmo participante não são independentes",
                   **inferential}
        output.append(clean_row(metric, summary))
        comparisons[metric.name] = summary
        participant_differences = [median([pair["difference"] for pair in pairs
                                           if pair["participant_id"] == participant])
                                   for participant in participants
                                   if any(pair["participant_id"] == participant for pair in pairs)]
        sensitivity = (wilcoxon_exact(participant_differences, alternative)
                       if metric.inferential and len(participant_differences) >= 2 else {})
        output.append(clean_row(metric, {"row_type": "participant_level_comparison",
                                         "n_expected": len(participants),
                                         "n_valid": len(participant_differences),
                                         "n_missing": len(participants) - len(participant_differences),
                                         "n_participants": len(participant_differences),
                                         "difference": median(participant_differences)
                                         if participant_differences else None,
                                         "note": "sensibilidade: uma mediana por participante",
                                         **sensitivity}))
        for participant in participants:
            participant_pairs = [pair for pair in pairs if pair["participant_id"] == participant]
            values = [pair["difference"] for pair in participant_pairs]
            result = wilcoxon_exact(values, alternative) if metric.inferential else {}
            output.append(clean_row(metric, {"row_type": "participant_comparison",
                                             "participant_id": participant,
                                             "n_expected": sum(row["participant_id"] == participant
                                                               for row in pair_export),
                                             "n_valid": len(values),
                                             "n_missing": sum(row["participant_id"] == participant
                                                              for row in pair_export) - len(values),
                                             "n_pairs": len(values),
                                             "difference": median(values) if values else None,
                                             **result}))
    # A família pré-registrada contém dois testes. Um p indefinido por empates
    # totais conta como 1 apenas no ajuste; permanece vazio no resultado bruto.
    names = ("mean_cyclomatic_complexity", "duplication_percentage")
    ordered = sorted(names, key=lambda name: comparisons[name].get("p_value")
                     if comparisons[name].get("p_value") is not None else 1.0)
    running = 0.0
    for index, name in enumerate(ordered):
        raw_p = comparisons[name].get("p_value")
        running = max(running, min(1.0, (len(names) - index) *
                                   (raw_p if raw_p is not None else 1.0)))
        if raw_p is not None:
            comparisons[name]["p_holm"] = running
            for row in output:
                if row["metric"] == name and row["row_type"] == "comparison":
                    row["p_holm"] = f"{running:.4f}"
    return output, comparisons


def fmt(value: float | int | None, digits: int = 2) -> str:
    return "—" if value is None else f"{value:.{digits}f}"


def report(trials: list[dict], warnings: list[str], rows: list[dict], comparisons: dict[str, dict]) -> str:
    lines = ["# Respostas preliminares às RQs", "",
             "Gerado por `python scripts/run_analysis.py` a partir da alocação e dos dados brutos. "
             "Os resultados refletem somente os registros disponíveis neste checkout.", "",
             "## Cobertura e qualidade", "",
             f"- Trials planejados: {len(trials)}; trials válidos para RQ1/RQ2: "
             f"{sum('duration_seconds' in item['values'] for item in trials)}.",
             "- Pares definidos por participante e bloco de dificuldade; valores ausentes não foram imputados.",
             "- Intervalos de 95% reamostram pares de forma exploratória, como nos relatórios "
             "individuais. Eles não corrigem a dependência entre blocos do mesmo participante.",
             "- Os valores de p são Wilcoxon exato por permutação de sinais dos postos não nulos "
             "(empates em magnitude recebem postos médios). Com apenas três participantes, "
             "os pares do mesmo indivíduo não são independentes: os testes são exploratórios "
             "e podem sofrer pseudorreplicação.", ""]
    if warnings:
        lines.extend(["### Ausências e ressalvas de origem", ""])
        lines.extend(f"- {warning}" for warning in warnings)
        lines.append("")
    lines.extend(["## Resultados consolidados", "",
                  "Diferenças: RQ1 = Manual − IA; RQ2 = IA − Manual; RQ3 = IA − Manual. "
                  "Valor positivo em RQ1/RQ2 favorece IA. Em RQ3 indica aumento com IA.", "",
                  "| RQ | Métrica | Manual: mediana [Q1; Q3] | IA: mediana [Q1; Q3] | "
                  "Pares / empates / ausentes | Δ mediano | p | p Holm | r bisserial | IC 95% exploratório |",
                  "|---|---|---|---|---|---:|---:|---:|---:|---|"])
    for metric in METRICS:
        if not metric.primary:
            continue
        item = comparisons[metric.name]
        treatment_rows = {row["treatment"]: row for row in rows
                          if row["metric"] == metric.name and row["row_type"] == "treatment"}
        def summary(treatment: str) -> str:
            row = treatment_rows[treatment]
            return f"{fmt(float(row['median']) if row['median'] != '' else None)} " \
                   f"[{fmt(float(row['q1']) if row['q1'] != '' else None)}; " \
                   f"{fmt(float(row['q3']) if row['q3'] != '' else None)}] " \
                   f"(n={row['n_valid']})"
        interval = (f"[{fmt(item['ci_low'])}; {fmt(item['ci_high'])}]"
                    if item["ci_low"] is not None else "—")
        lines.append(f"| {metric.rq} | `{metric.name}` ({metric.unit}) | {summary('manual')} | "
                     f"{summary('ai')} | {item['n_pairs']} / {item.get('n_ties', '—')} / "
                     f"{item['n_missing']} | {fmt(item['difference'])} | "
                     f"{fmt(item.get('p_value'), 4)} | {fmt(item.get('p_holm'), 4)} | "
                     f"{fmt(item.get('rank_biserial'))} | {interval} |")
    lines.extend(["", "## Resultados por participante", "",
                  "A tabela mostra a mediana das diferenças dos pares disponíveis em cada participante.", "",
                  "| Participante | RQ1: tempo (s) | RQ2: sucesso (p.p.) | "
                  "RQ3: complexidade | RQ3: duplicação (p.p.) |",
                  "|---|---:|---:|---:|---:|"])
    primary = [metric for metric in METRICS if metric.primary]
    for participant in sorted({item["participant_id"] for item in trials}):
        cells = []
        for metric in primary:
            row = next(row for row in rows if row["row_type"] == "participant_comparison"
                       and row["metric"] == metric.name and row["participant_id"] == participant)
            cells.append(f"{fmt(float(row['difference']) if row['difference'] != '' else None)} "
                         f"(n={row['n_pairs']})")
        lines.append(f"| {participant} | {' | '.join(cells)} |")
    lines.extend(["", "## Respostas objetivas", ""])
    for rq, title, names in (
        ("RQ1", "Tempo", ("duration_seconds",)),
        ("RQ2", "Defeitos", ("success_rate",)),
        ("RQ3", "Estrutura do código", ("mean_cyclomatic_complexity", "duplication_percentage")),
    ):
        parts = []
        for name in names:
            item = comparisons[name]
            if item["n_pairs"] == 0:
                parts.append(f"`{name}`: sem pares completos")
            else:
                parts.append(f"`{name}`: Δ mediano {fmt(item['difference'])}, "
                             f"{item['n_pairs']} pares, p={fmt(item.get('p_value'), 4)}" +
                             (f", p Holm={fmt(item['p_holm'], 4)}" if item.get("p_holm") is not None else ""))
        lines.extend([f"### {rq} — {title}", "", "; ".join(parts) + ".", ""])
        if rq == "RQ1":
            item = comparisons["duration_seconds"]
            if item["n_pairs"]:
                lines.append("Nos pares disponíveis, o tempo foi menor com IA."
                             if item["difference"] > 0 else
                             "Nos pares disponíveis, o tempo foi maior com IA."
                             if item["difference"] < 0 else
                             "Nos pares disponíveis, a diferença mediana de tempo foi zero.")
        elif rq == "RQ2":
            item = comparisons["success_rate"]
            lines.append("A taxa de sucesso observada foi maior com IA nos pares disponíveis."
                         if item["n_pairs"] and item["difference"] > 0 else
                         "A taxa de sucesso observada foi menor com IA nos pares disponíveis."
                         if item["n_pairs"] and item["difference"] < 0 else
                         "Não houve diferença mediana observada na taxa de sucesso dos pares disponíveis."
                         if item["n_pairs"] else "Ainda não há pares completos para RQ2.")
        else:
            cc = comparisons["mean_cyclomatic_complexity"]
            dup = comparisons["duplication_percentage"]
            if cc["n_pairs"] and dup["n_pairs"]:
                lines.append("A complexidade média apresentou diferença mediana "
                             f"de {fmt(cc['difference'])} ponto(s) e a duplicação de "
                             f"{fmt(dup['difference'])} ponto(s) percentual(is) com IA "
                             "nos pares disponíveis; não é possível estabelecer um efeito estrutural geral.")
            else:
                lines.append("Ainda não há pares suficientes para avaliar ambos os desfechos estruturais.")
        sensitivity = [row for row in rows if row["row_type"] == "participant_level_comparison"
                       and row["metric"] in names]
        lines.append("Sensibilidade por participante: " + "; ".join(
            f"`{row['metric']}`: n={row['n_participants']}, "
            f"p={fmt(float(row['p_value']) if row['p_value'] != '' else None, 4)}"
            for row in sensitivity) + ".")
        if rq == "RQ1":
            censored = {t: sum(item.get("censored", False) for item in trials
                               if item["treatment"] == t and "duration_seconds" in item["values"])
                        for t in ("manual", "ai")}
            completed = {t: sum(item["values"].get("completed") == 1 for item in trials
                                if item["treatment"] == t) for t in ("manual", "ai")}
            lines.append(f"Conclusão observada: Manual {completed['manual']}, IA {completed['ai']}; "
                         f"censura: Manual {censored['manual']}, IA {censored['ai']}. "
                         "O tempo de trials censurados é limitado a 2.100 s e não é o tempo real até conclusão.")
            conditional = {t: [item["values"]["duration_seconds"] for item in trials
                               if item["treatment"] == t and item["values"].get("completed") == 1]
                           for t in ("manual", "ai")}
            lines.append("Entre trials concluídos: mediana Manual "
                         f"{fmt(percentile(conditional['manual'], 0.5))} s "
                         f"(n={len(conditional['manual'])}), IA "
                         f"{fmt(percentile(conditional['ai'], 0.5))} s "
                         f"(n={len(conditional['ai'])}); análise condicionada ao sucesso, "
                         "sujeita a viés de seleção.")
        elif rq == "RQ2":
            lines.append("A taxa de testes passando é o desfecho principal; testes falhando são "
                         "complementares porque as katas têm quantidades diferentes de testes. "
                         "Passar nos testes não demonstra ausência de defeitos.")
        else:
            loc_rows = {row["treatment"]: row for row in rows
                        if row["row_type"] == "treatment" and row["metric"] == "loc"}
            lines.append("Complexidade e duplicação devem ser interpretadas junto com LOC. "
                         "O Índice de Manutenibilidade é apenas exploratório. "
                         "No ajuste de Holm dos dois testes pré-registrados, um p indefinido "
                         "por empates totais conta como 1 apenas no cálculo; seu p bruto fica vazio.")
            lines.append("LOC mediana: Manual "
                         f"{fmt(float(loc_rows['manual']['median']) if loc_rows['manual']['median'] != '' else None)} "
                         f"(n={loc_rows['manual']['n_valid']}), IA "
                         f"{fmt(float(loc_rows['ai']['median']) if loc_rows['ai']['median'] != '' else None)} "
                         f"(n={loc_rows['ai']['n_valid']}).")
        caveat = ("Há métricas estruturais ausentes em parte dos trials. "
                  if rq == "RQ3" and any(comparisons[name]["n_missing"] for name in names)
                  else "")
        lines.extend([caveat + "Com apenas três participantes, esta é uma resposta preliminar; "
                      "não há base para afirmar efeito causal geral nem equivalência entre tratamentos.", ""])
    lines.extend(["## Tabela para o dashboard", "",
                  "`data/processed/statistical-results.csv` contém linhas `treatment`, "
                  "`participant_treatment`, `pair`, `comparison`, `participant_comparison` "
                  "e `participant_level_comparison`. "
                  "Valores ausentes são células vazias. Valores numéricos usam ponto decimal e quatro casas.", ""])
    return "\n".join(lines)


def run(root: Path) -> tuple[int, int]:
    trials, warnings = load_trials(root)
    rows, comparisons = analyze(trials)
    destination = root / "data/processed/statistical-results.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    draft = root / "reports/drafts/rq-answers.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(report(trials, warnings, rows, comparisons), encoding="utf-8")
    return len(rows), len(warnings)
