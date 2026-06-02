from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from lxml import etree


DOCX = Path(r"E:\MulTek\02设计文档\EAP通讯规格书\WebAPI\超毅项目Web API通讯规格书 v4.0_接口列字体修正版.docx")
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def cell_text(tc) -> str:
    return "".join(tc.xpath(".//w:t/text()", namespaces=NS)).strip()


def first_font_size(tc) -> tuple[str, str]:
    runs = tc.xpath(".//w:r[.//w:t]", namespaces=NS)
    if not runs:
        return "", ""
    r = runs[0]
    font = r.xpath("./w:rPr/w:rFonts/@w:eastAsia", namespaces=NS)
    size = r.xpath("./w:rPr/w:sz/@w:val", namespaces=NS)
    return (font[0] if font else "", size[0] if size else "")


def is_example(tbl) -> bool:
    return "日志范例" in "".join(tbl.xpath(".//w:t/text()", namespaces=NS))


def is_interface(tbl) -> bool:
    text = "".join(tbl.xpath(".//w:t/text()", namespaces=NS))
    return "接口方式" in text and "接口调用方" in text and "接口提供方" in text


def main() -> None:
    with ZipFile(DOCX) as z:
        root = etree.fromstring(z.read("word/document.xml"))
    bad = []
    task_rows = []
    checked_tables = 0
    for ti, tbl in enumerate(root.xpath(".//w:tbl", namespaces=NS)):
        if is_example(tbl) or not is_interface(tbl):
            continue
        checked_tables += 1
        table_text = "".join(tbl.xpath(".//w:t/text()", namespaces=NS))
        in_area = False
        for ri, tr in enumerate(tbl.xpath("./w:tr", namespaces=NS)):
            cells = tr.xpath("./w:tc", namespaces=NS)
            texts = [cell_text(tc) for tc in cells]
            joined = "|".join(texts)
            if "接口方式" in texts or "接口调用方" in texts or "接口提供方" in texts:
                in_area = True
            if "参数列表" in joined or "请求参数列表" in joined or "返回值列表" in joined:
                in_area = True
            if "序号" in texts and "字段" in texts and "类型" in texts:
                in_area = True
            if not in_area or len(cells) < 2:
                continue
            non_empty = [t for t in texts if t]
            if non_empty and len(set(non_empty)) <= 1:
                continue
            for ci, tc in enumerate(cells):
                txt = cell_text(tc)
                if not txt:
                    continue
                font, size = first_font_size(tc)
                expected = ("Cambria", "14") if ci < len(cells) - 1 else ("Microsoft YaHei", "16")
                if (font, size) != expected:
                    bad.append((ti, ri, ci, txt[:30], font, size, expected))
            if "EAP_TaskDownload" in table_text and ("接口调用方" in joined or "From" in joined or "TaskInfo" in joined):
                task_rows.append((ri, texts, [first_font_size(tc) for tc in cells]))

    print("checked_interface_tables", checked_tables)
    print("bad_count", len(bad))
    for item in bad[:20]:
        print("BAD", item)
    print("EAP-EQP-011 samples")
    for row in task_rows[:8]:
        print(row)


if __name__ == "__main__":
    main()
