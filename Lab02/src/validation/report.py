"""Renderiza o relatório de validação do dataset em Markdown."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from .dataset_validator import CRITICAL, INFO, WARNING, Finding, ValidationResult

_SEVERITY_LABEL = {CRITICAL: "Crítico", WARNING: "Aviso", INFO: "Informativo"}


def _findings_table(findings: list[Finding]) -> str:
    if not findings:
        return "_Nenhum achado nesta categoria._\n"
    lines = ["| Regra | Trial | Mensagem |", "|---|---|---|"]
    for item in findings:
        trial = item.trial_id or "—"
        message = item.message.replace("|", "\\|")
        lines.append(f"| `{item.rule}` | {trial} | {message} |")
    return "\n".join(lines) + "\n"


def _pairs_table(result: ValidationResult) -> str:
    lines = ["| Participante | Bloco | Trial IA | Trial Manual | Válido |", "|---|---|---|---|---|"]
    for pair in result.pairs:
        status = "Sim" if pair.valid else f"Não ({'; '.join(pair.reasons)})"
        lines.append(
            f"| {pair.participant_id} | {pair.difficulty_block} | {pair.ai_trial_id or '—'} | {pair.manual_trial_id or '—'} | {status} |"
        )
    return "\n".join(lines) + "\n"


def render_report_markdown(
    result: ValidationResult,
    *,
    dataset_path: Any,
    generated_at: datetime | None = None,
) -> str:
    generated_at = generated_at or datetime.now().astimezone()
    valid_pairs = sum(1 for pair in result.pairs if pair.valid)
    verdict = "AUTORIZADO para as análises de RQ1-RQ3" if result.authorized else "NÃO AUTORIZADO — erros críticos pendentes"

    sections = [
        "# Relatório de validação do dataset — S03-01",
        "",
        f"Gerado em {generated_at.isoformat(timespec='seconds')} a partir de `{dataset_path}`.",
        "",
        f"## Veredito: {verdict}",
        "",
        f"- Linhas no dataset: {result.row_count}",
        f"- Pares participante × bloco válidos: {valid_pairs}/{len(result.pairs)}",
        f"- Achados críticos: {len(result.critical)}",
        f"- Avisos (lacunas conhecidas e toleradas): {len(result.warnings)}",
        f"- Observações (outliers preservados): {len(result.infos)}",
        "",
        "## 1. Erros críticos",
        "",
        "Qualquer achado nesta seção interrompe a autorização do dataset para a análise das RQs.",
        "",
        _findings_table(result.critical),
        "## 2. Dados ausentes e avisos",
        "",
        "Lacunas previstas e toleradas pela metodologia (Seção 12): campos não aplicáveis "
        "permanecem vazios e nunca são preenchidos artificialmente com zero.",
        "",
        _findings_table(result.warnings),
        "## 3. Outliers identificados",
        "",
        "Valores extremos são reportados e mantidos; nenhum é removido automaticamente.",
        "",
        _findings_table(result.infos),
        "## 4. Pares válidos por participante e bloco de dificuldade",
        "",
        _pairs_table(result),
    ]
    return "\n".join(sections).rstrip() + "\n"
