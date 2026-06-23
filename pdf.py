"""PDF stage: extract text the way a generic ATS parser does, and flag the
layout features that break real parsers (Workday/Greenhouse/Lever/Taleo/iCIMS).

An ATS strips visual layout and reads text in raw document order. The gap
between what you see and what `extract()` returns is your parse risk.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import fitz  # PyMuPDF


@dataclass
class ParsedResume:
    text: str  # what the ATS actually reads
    page_count: int
    word_count: int
    image_count: int
    multi_column: bool
    has_tables: bool
    header_footer_text: list[str] = field(default_factory=list)
    fonts: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


_SAFE_FONTS = {
    "Arial", "Calibri", "Helvetica", "Times", "TimesNewRoman", "Georgia",
    "Garamond", "Cambria", "Verdana", "Tahoma", "Lato", "Roboto", "OpenSans",
}


def _multi_column(page: fitz.Page) -> bool:
    blocks = [b for b in page.get_text("blocks") if b[6] == 0 and b[4].strip()]
    if len(blocks) < 4:
        return False
    mid = page.rect.width / 2
    left = [b for b in blocks if (b[0] + b[2]) / 2 < mid]
    right = [b for b in blocks if (b[0] + b[2]) / 2 >= mid]
    if not left or not right:
        return False

    def span(bs):
        return max(b[3] for b in bs) - min(b[1] for b in bs)

    h = page.rect.height
    return span(left) > h * 0.4 and span(right) > h * 0.4


def _header_footer(page: fitz.Page) -> list[str]:
    h = page.rect.height
    out = []
    for b in page.get_text("blocks"):
        if b[6] != 0 or not b[4].strip():
            continue
        if b[3] < h * 0.08 or b[1] > h * 0.92:
            out.append(b[4].strip().replace("\n", " "))
    return out


def extract(data: bytes) -> ParsedResume:
    doc = fitz.open(stream=data, filetype="pdf")
    chunks, fonts, header_footer = [], set(), []
    image_count = multi = tables = 0
    multi_column = has_tables = False

    for page in doc:
        chunks.append(page.get_text("text"))
        image_count += len(page.get_images(full=True))
        if _multi_column(page):
            multi_column = True
        try:
            if page.find_tables().tables:
                has_tables = True
        except Exception:
            pass
        header_footer.extend(_header_footer(page))
        for f in page.get_fonts(full=True):
            fonts.add(f[3].split("+")[-1] if "+" in f[3] else f[3])

    text = "\n".join(chunks).strip()
    r = ParsedResume(
        text=text,
        page_count=doc.page_count,
        word_count=len(text.split()),
        image_count=image_count,
        multi_column=multi_column,
        has_tables=has_tables,
        header_footer_text=header_footer,
        fonts=sorted(fonts),
    )
    doc.close()
    _warn(r)
    return r


def extract_file(path: str) -> ParsedResume:
    with open(path, "rb") as fh:
        return extract(fh.read())


def _warn(r: ParsedResume) -> None:
    if r.word_count < 150:
        r.warnings.append(
            "Very little machine-readable text extracted — the resume may be "
            "image-based/scanned; most ATS parsers will read almost nothing."
        )
    if r.multi_column:
        r.warnings.append(
            "Multi-column layout detected — many parsers read across columns and "
            "interleave unrelated lines. Prefer a single-column layout."
        )
    if r.has_tables:
        r.warnings.append(
            "Tables detected — Workday and others mangle tabular data; use plain "
            "text lines instead of tables."
        )
    if r.image_count:
        r.warnings.append(
            f"{r.image_count} image(s) detected — any text rendered as an image is "
            "invisible to an ATS."
        )
    if r.header_footer_text:
        r.warnings.append(
            "Text found in header/footer zones — some parsers drop these; keep "
            "contact details in the main body."
        )
    risky = [f for f in r.fonts if not any(s.lower() in f.lower() for s in _SAFE_FONTS)]
    if risky:
        r.warnings.append(
            "Non-standard fonts (" + ", ".join(risky[:5]) + ") — stick to common "
            "fonts to avoid character-mapping issues."
        )
