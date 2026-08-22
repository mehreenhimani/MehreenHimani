"""
Post-process pandoc's .docx output.

Two things pandoc cannot do well, both fixed here rather than by hand:

1. Header-row shading. The reference document defines it as conditional table
   formatting (`tblStylePr firstRow`), which Word honours and LibreOffice often
   ignores. These documents will be opened in both, so the shading is written
   directly onto the first row's cells.

2. Column widths. Pandoc sizes columns from the character widths in the *markdown
   source*, which bears no relation to how the text sets in Word — you get a
   narrow column carrying the most prose and rows ten lines tall. Columns are
   re-proportioned to the actual text they contain, damped by a square root so a
   long column widens without crushing its neighbours.

3. Row banding. A twelve-row table of dense prose is hard to track across; a very
   faint tint on alternate rows fixes that for the cost of one shading element
   per cell. Word's own banding lives in conditional table formatting, which
   LibreOffice ignores, so it goes on directly like the header shading.
"""
from __future__ import annotations

import re
import shutil
import sys
import zipfile
from math import sqrt
from pathlib import Path

HDR_FILL = "F1F4F8"
BAND_FILL = "FAFBFD"   # every other body row, barely there but it holds the eye
RULE = "C8102E"
MIN_SHARE = 0.11          # no column narrower than this
MAX_SHARE = 0.58          # no column wider than this


def text_width(doc: str) -> int:
    pg = re.search(r'<w:pgSz[^>]*w:w="(\d+)"', doc)
    left = re.search(r'<w:pgMar[^>]*w:left="(\d+)"', doc)
    right = re.search(r'<w:pgMar[^>]*w:right="(\d+)"', doc)
    return ((int(pg.group(1)) if pg else 11906)
            - (int(left.group(1)) if left else 1440)
            - (int(right.group(1)) if right else 1440))


def rows(table: str) -> list[str]:
    return re.findall(r"<w:tr(?:\s[^>]*)?>.*?</w:tr>", table, re.S)


def cells(row: str) -> list[str]:
    return re.findall(r"<w:tc>.*?</w:tc>", row, re.S)


def cell_chars(cell: str) -> int:
    return sum(len(t) for t in re.findall(r"<w:t[^>]*>([^<]*)</w:t>", cell))


def column_shares(table: str, ncols: int) -> list[float]:
    """Share of width per column, from the text each column actually carries."""
    totals = [0] * ncols
    for r in rows(table):
        for i, c in enumerate(cells(r)[:ncols]):
            totals[i] += cell_chars(c)
    if not any(totals):
        return [1 / ncols] * ncols

    # sqrt damping: a column with 4x the text gets 2x the width, not 4x.
    weights = [sqrt(max(t, 1)) for t in totals]
    shares = [w / sum(weights) for w in weights]

    # Clamp, then renormalise so the shares still sum to 1.
    for _ in range(4):
        shares = [min(MAX_SHARE, max(MIN_SHARE, s)) for s in shares]
        total = sum(shares)
        shares = [s / total for s in shares]
    return shares


def process(path: Path) -> tuple[int, int]:
    zin = zipfile.ZipFile(path)
    doc = zin.read("word/document.xml").decode("utf-8")
    target = text_width(doc)

    out, pos, n_tables, n_hdr = [], 0, 0, 0

    for tbl in re.finditer(r"<w:tbl>.*?</w:tbl>", doc, re.S):
        body = tbl.group(0)
        grid = re.findall(r'<w:gridCol w:w="(\d+)"', body)
        if not grid:
            continue
        ncols = len(grid)

        shares = column_shares(body, ncols)
        widths = [max(500, round(s * target)) for s in shares]
        widths[-1] += target - sum(widths)

        body = re.sub(
            r"<w:tblGrid>.*?</w:tblGrid>",
            "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths) + "</w:tblGrid>",
            body, flags=re.S)

        if re.search(r"<w:tblW[^>]*/>", body):
            body = re.sub(r"<w:tblW[^>]*/>", f'<w:tblW w:w="{target}" w:type="dxa"/>',
                          body, count=1)
        else:
            body = body.replace("<w:tblPr>",
                                f'<w:tblPr><w:tblW w:w="{target}" w:type="dxa"/>', 1)

        all_rows = rows(body)
        for ri, row in enumerate(all_rows):
            idx = [0]

            def fix_cell(cm, _ri=ri):
                i = min(idx[0], ncols - 1)
                idx[0] += 1
                inner = re.sub(r"</?w:tcPr>", "", cm.group(1) or "")
                inner = re.sub(r"<w:tcW[^>]*/>", "", inner)
                inner = re.sub(r"<w:shd[^>]*/>", "", inner)
                prefix = f'<w:tcW w:w="{widths[i]}" w:type="dxa"/>'
                if _ri == 0:
                    nonlocal n_hdr
                    n_hdr += 1
                    prefix += (f'<w:shd w:val="clear" w:color="auto" w:fill="{HDR_FILL}"/>'
                               f'<w:tcBorders><w:bottom w:val="single" w:sz="8" '
                               f'w:space="0" w:color="{RULE}"/></w:tcBorders>')
                elif _ri % 2 == 0:
                    prefix += (f'<w:shd w:val="clear" w:color="auto" '
                               f'w:fill="{BAND_FILL}"/>')
                return f"<w:tc><w:tcPr>{prefix}{inner}</w:tcPr>"

            new_row = re.sub(r"<w:tc>\s*(<w:tcPr>.*?</w:tcPr>)?", fix_cell, row, flags=re.S)
            # A header row that repeats across a page break keeps long tables readable.
            if ri == 0 and "<w:tblHeader" not in new_row:
                if "<w:trPr>" in new_row:
                    new_row = new_row.replace("<w:trPr>", "<w:trPr><w:tblHeader/>", 1)
                else:
                    new_row = re.sub(r"(<w:tr(?:\s[^>]*)?>)", r"\1<w:trPr><w:tblHeader/></w:trPr>",
                                     new_row, count=1)
            body = body.replace(row, new_row, 1)

        out.append(doc[pos:tbl.start()] + body)
        pos = tbl.end()
        n_tables += 1

    out.append(doc[pos:])
    doc = "".join(out)

    tmp = path.with_suffix(".tmp.docx")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = doc.encode("utf-8") if item.filename == "word/document.xml" \
                else zin.read(item.filename)
            zout.writestr(item, data)
    zin.close()
    shutil.move(tmp, path)
    return n_tables, n_hdr


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        p = Path(arg)
        t, h = process(p)
        print(f"  {p.name}: {t} tables re-proportioned, {h} header cells shaded")
