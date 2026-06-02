from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

from docx import Document
from lxml import etree


def iter_block_items(parent):
    from docx.document import Document as _Document
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    if isinstance(parent, _Document):
        parent_elm = parent.element.body
    else:
        parent_elm = parent._element

    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def paragraph_text_with_hyperlinks(paragraph):
    return paragraph.text.replace("\u00a0", " ").strip()


def table_to_rows(table):
    rows = []
    for row in table.rows:
        rows.append([cell.text.replace("\u00a0", " ").strip() for cell in row.cells])
    return rows


def extract_docx(path: Path) -> dict:
    doc = Document(str(path))
    blocks = []
    full_lines = []
    for idx, block in enumerate(iter_block_items(doc), 1):
        if block.__class__.__name__ == "Paragraph":
            text = paragraph_text_with_hyperlinks(block)
            style = block.style.name if block.style is not None else ""
            if text:
                blocks.append({"type": "p", "index": idx, "style": style, "text": text})
                full_lines.append(text)
        else:
            rows = table_to_rows(block)
            blocks.append({"type": "table", "index": idx, "rows": rows})
            full_lines.append(f"[TABLE {idx}]")
            for row in rows:
                full_lines.append(" | ".join(row))

    xml_info = {}
    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        xml_info["has_comments"] = "word/comments.xml" in names
        xml_info["has_footnotes"] = "word/footnotes.xml" in names
        xml_info["has_endnotes"] = "word/endnotes.xml" in names
        xml_info["has_tracked_changes"] = False
        doc_xml = zf.read("word/document.xml")
        root = etree.fromstring(doc_xml)
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        for tag in ("ins", "del", "moveFrom", "moveTo"):
            if root.xpath(f".//w:{tag}", namespaces=ns):
                xml_info["has_tracked_changes"] = True
                break

    all_text = "\n".join(full_lines)
    example_candidates = []
    patterns = [
        r"\{[\s\S]{20,4000}?\}",
        r"<\?xml[\s\S]{0,2000}",
    ]
    for pat in patterns:
        for m in re.finditer(pat, all_text):
            example_candidates.append(m.group(0)[:4000])

    return {
        "path": str(path),
        "xml_info": xml_info,
        "block_count": len(blocks),
        "blocks": blocks,
        "full_text": all_text,
        "example_candidates": example_candidates,
    }


def main() -> None:
    src = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    data = extract_docx(src)
    (out_dir / "docx_extract.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "docx_extract.txt").write_text(data["full_text"], encoding="utf-8")
    print(json.dumps({k: data[k] for k in ("path", "xml_info", "block_count")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
