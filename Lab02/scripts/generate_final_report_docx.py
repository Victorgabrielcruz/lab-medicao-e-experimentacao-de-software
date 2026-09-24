"""Monta o DOCX do relatório final a partir do Markdown e do template versionado.

O script preserva a geometria, as fontes e as tabelas do template. O texto
publicável permanece em ``reports/final/relatorio-final.md``; esta etapa apenas
o leva ao formato solicitado para entrega, sem reescrever números ou figuras.
"""
from __future__ import annotations

import argparse
import csv
import re
import shutil
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = ROOT / "Docs/templates/Template_Relatorio_Laboratorio.docx"
DEFAULT_MARKDOWN = ROOT / "reports/final/relatorio-final.md"
DEFAULT_OUTPUT = ROOT / "reports/final/relatorio-final.docx"

BLACK = RGBColor(0, 0, 0)
GREEN = "1F6E63"
LIGHT_GREY = "F0F0EC"
CODE_GREY = "F3F5F7"
WHITE = RGBColor(255, 255, 255)
INLINE_TOKEN = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]*\)|\*[^*]+\*)")
IMAGE = re.compile(r"!\[([^]]*)\]\(([^)]+)\)")
GENERATED_TABLE = re.compile(r"<!--\s*GENERATED TABLE:\s*([^>]+?)\s*-->")


def _shade(cell, fill: str) -> None:
    properties = cell._tc.get_or_add_tcPr()
    shading = properties.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        properties.append(shading)
    shading.set(qn("w:fill"), fill)


def _remove_paragraph_border(paragraph) -> None:
    properties = paragraph._p.get_or_add_pPr()
    border = properties.find(qn("w:pBdr"))
    if border is not None:
        properties.remove(border)
    # O estilo de título do template traz uma regra inferior. A versão final
    # usa a mesma escala tipográfica, mas suprime a decoração com uma
    # substituição local em vez de alterar o estilo global do modelo.
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "nil")
    borders.append(bottom)
    properties.append(borders)


def _set_run(run, *, color: RGBColor = BLACK, size: float | None = None,
             bold: bool | None = None, italic: bool | None = None,
             font_name: str | None = None) -> None:
    run.font.color.rgb = color
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if font_name:
        run.font.name = font_name
        run._element.rPr.rFonts.set(qn("w:eastAsia"), font_name)


def _add_inline(paragraph, text: str, *, color: RGBColor = BLACK,
                size: float | None = None) -> None:
    """Adiciona um subconjunto previsível de Markdown sem depender de pandoc."""
    position = 0
    for match in INLINE_TOKEN.finditer(text):
        if match.start() > position:
            run = paragraph.add_run(text[position:match.start()])
            _set_run(run, color=color, size=size)
        token = match.group(0)
        if token.startswith("**"):
            run = paragraph.add_run(token[2:-2])
            _set_run(run, color=color, size=size, bold=True)
        elif token.startswith("`"):
            run = paragraph.add_run(token[1:-1])
            _set_run(run, color=color, size=size, font_name="Consolas")
        elif token.startswith("["):
            label, url = token[1:].split("](", 1)
            run = paragraph.add_run(f"{label} ({url[:-1]})")
            _set_run(run, color=color, size=size)
        else:
            run = paragraph.add_run(token[1:-1])
            _set_run(run, color=color, size=size, italic=True)
        position = match.end()
    if position < len(text):
        run = paragraph.add_run(text[position:])
        _set_run(run, color=color, size=size)


def _parse_markdown_table(lines: list[str]) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in lines:
        values = [value.strip() for value in line.strip().strip("|").split("|")]
        if values and all(re.fullmatch(r":?-{3,}:?", value.replace(" ", "")) for value in values):
            continue
        rows.append(values)
    return rows


def _add_table(doc: Document, rows: list[list[str]], *, header: bool = True) -> None:
    if not rows:
        return
    columns = max(len(row) for row in rows)
    table = doc.add_table(rows=0, cols=columns)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    for row_index, values in enumerate(rows):
        cells = table.add_row().cells
        for column_index in range(columns):
            value = values[column_index] if column_index < len(values) else ""
            cell = cells[column_index]
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.paragraph_format.space_before = Pt(0)
            if header and row_index == 0:
                _shade(cell, GREEN)
                _add_inline(paragraph, value, color=WHITE, size=8.5)
                for run in paragraph.runs:
                    run.bold = True
            else:
                _add_inline(paragraph, value, color=BLACK, size=8.5)


def _add_csv_table(doc: Document, path: Path) -> None:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"Tabela sem cabeçalho: {path}")
        rows = [reader.fieldnames]
        rows.extend([[record.get(field, "") for field in reader.fieldnames] for record in reader])
    _add_table(doc, rows)


def _cover_data(markdown_path: Path) -> tuple[str, str, list[list[str]], int]:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    title = next((line[2:].strip() for line in lines if line.startswith("# ")), "Relatório de Laboratório")
    title_index = next(index for index, line in enumerate(lines) if line.startswith("# "))
    subtitle = ""
    for line in lines[title_index + 1:]:
        if not line.strip():
            continue
        if line.lstrip().startswith("|"):
            break
        subtitle = line.strip().strip("_")
        break
    table_start = next(index for index, line in enumerate(lines) if line.lstrip().startswith("|"))
    table_end = table_start
    while table_end < len(lines) and lines[table_end].lstrip().startswith("|"):
        table_end += 1
    metadata = _parse_markdown_table(lines[table_start:table_end])
    if metadata and metadata[0][0].lower() in {"campo", "item"}:
        metadata = metadata[1:]
    body_start = next((index for index in range(table_end, len(lines))
                       if lines[index].startswith("## ")), len(lines))
    return title, subtitle, metadata, body_start


def _add_cover(doc: Document, title: str, subtitle: str, metadata: list[list[str]]) -> None:
    title_paragraph = doc.add_paragraph(style="Title")
    title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_paragraph.paragraph_format.space_after = Pt(12)
    _remove_paragraph_border(title_paragraph)
    title_run = title_paragraph.add_run(title)
    _set_run(title_run, color=BLACK, size=26)

    subtitle_paragraph = doc.add_paragraph()
    subtitle_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle_paragraph.paragraph_format.space_after = Pt(18)
    subtitle_run = subtitle_paragraph.add_run(subtitle)
    _set_run(subtitle_run, color=RGBColor(31, 110, 99), size=12, italic=True)

    table = doc.add_table(rows=0, cols=2)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for values in metadata:
        cells = table.add_row().cells
        label = values[0] if values else ""
        value = values[1] if len(values) > 1 else ""
        left, right = cells
        left.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        right.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        _shade(left, LIGHT_GREY)
        left.paragraphs[0].paragraph_format.space_after = Pt(0)
        right.paragraphs[0].paragraph_format.space_after = Pt(0)
        _add_inline(left.paragraphs[0], label, color=BLACK, size=10)
        for run in left.paragraphs[0].runs:
            run.bold = True
        _add_inline(right.paragraphs[0], value, color=BLACK, size=9.5)
    doc.add_page_break()


def _add_heading(doc: Document, text: str, level: int) -> None:
    style = "Heading 1" if level == 2 else "Heading 2" if level == 3 else "Heading 3"
    paragraph = doc.add_paragraph(style=style)
    _remove_paragraph_border(paragraph)
    _add_inline(paragraph, text, color=BLACK)


def _add_body_paragraph(doc: Document, text: str, *, style: str = "Normal",
                        italic: bool = False, bullet: bool = False) -> None:
    paragraph = doc.add_paragraph(style=style)
    if bullet:
        # Um marcador literal evita que o renderizador converta itens adjacentes
        # em uma lista contínua na mesma linha ao atravessar páginas.
        paragraph.paragraph_format.left_indent = Inches(0.28)
        paragraph.paragraph_format.first_line_indent = Inches(-0.16)
        paragraph.paragraph_format.space_before = Pt(2)
        paragraph.paragraph_format.space_after = Pt(3)
        paragraph.paragraph_format.line_spacing = 1
    _add_inline(paragraph, f"• {text}" if bullet else text, color=BLACK)
    if italic:
        for run in paragraph.runs:
            run.italic = True


def _add_code_block(doc: Document, lines: list[str]) -> None:
    for line in lines:
        paragraph = doc.add_paragraph(style="Normal")
        paragraph.paragraph_format.left_indent = Inches(0.22)
        paragraph.paragraph_format.space_after = Pt(0)
        properties = paragraph._p.get_or_add_pPr()
        shading = OxmlElement("w:shd")
        shading.set(qn("w:fill"), CODE_GREY)
        properties.append(shading)
        run = paragraph.add_run(line)
        _set_run(run, color=BLACK, size=8.5, font_name="Consolas")


def _add_figure(doc: Document, caption: str, path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Figura referenciada não encontrada: {path}")
    picture = doc.add_paragraph()
    picture.alignment = WD_ALIGN_PARAGRAPH.CENTER
    picture.add_run().add_picture(str(path), width=Inches(6.15))
    caption_paragraph = doc.add_paragraph(style="Caption")
    caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_inline(caption_paragraph, caption, color=BLACK, size=9)


def _add_body(doc: Document, markdown_path: Path, body_start: int) -> None:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph_lines:
            _add_body_paragraph(doc, " ".join(line.strip() for line in paragraph_lines))
            paragraph_lines.clear()

    index = body_start
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            index += 1
            continue
        if stripped == "---":
            flush_paragraph()
            index += 1
            continue
        if stripped.startswith("```"):
            flush_paragraph()
            index += 1
            code: list[str] = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code.append(lines[index])
                index += 1
            _add_code_block(doc, code)
            index += 1
            continue
        generated = GENERATED_TABLE.fullmatch(stripped)
        if generated:
            flush_paragraph()
            _add_csv_table(doc, markdown_path.parent / generated.group(1).strip())
            index += 1
            continue
        image = IMAGE.fullmatch(stripped)
        if image:
            flush_paragraph()
            _add_figure(doc, image.group(1), markdown_path.parent / image.group(2))
            index += 1
            continue
        heading = re.fullmatch(r"(#{2,4})\s+(.+)", stripped)
        if heading:
            flush_paragraph()
            _add_heading(doc, heading.group(2), len(heading.group(1)))
            index += 1
            continue
        if stripped.startswith("|"):
            flush_paragraph()
            table_lines: list[str] = []
            while index < len(lines) and lines[index].lstrip().startswith("|"):
                table_lines.append(lines[index])
                index += 1
            _add_table(doc, _parse_markdown_table(table_lines))
            continue
        if stripped.startswith("- ") or stripped.startswith("* "):
            flush_paragraph()
            _add_body_paragraph(doc, stripped[2:], bullet=True)
            index += 1
            continue
        if stripped.startswith("> "):
            flush_paragraph()
            _add_body_paragraph(doc, stripped[2:], italic=True)
            index += 1
            continue
        paragraph_lines.append(line)
        index += 1
    flush_paragraph()


def build(template_path: Path, markdown_path: Path, output_path: Path) -> Path:
    """Cria o documento em um novo caminho sem modificar o arquivo-base."""
    template_path = Path(template_path)
    markdown_path = Path(markdown_path)
    output_path = Path(output_path)
    if not template_path.is_file():
        raise FileNotFoundError(f"Template não encontrado: {template_path}")
    if not markdown_path.is_file():
        raise FileNotFoundError(f"Markdown do relatório não encontrado: {markdown_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(template_path, output_path)

    document = Document(output_path)
    body = document._element.body
    for element in list(body):
        if element.tag != qn("w:sectPr"):
            body.remove(element)

    title, subtitle, metadata, body_start = _cover_data(markdown_path)
    _add_cover(document, title, subtitle, metadata)
    _add_body(document, markdown_path, body_start)
    properties = document.core_properties
    properties.title = title
    properties.subject = "Lab02 — assistentes de IA versus codificação manual"
    properties.author = "Víctor Gabriel Cruz Pereira; Jonathan Sena da Silva; Matheus Fernandes de Oliveira"
    properties.keywords = "Lab02, experimento, IA generativa, katas, replicação"
    document.save(output_path)
    return output_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    output = build(args.template, args.markdown, args.output)
    print(f"Relatório DOCX gerado em {output}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
