from pathlib import Path
from zipfile import ZipFile

from lxml import etree


DOCX = Path(r"E:\MulTek\02设计文档\EAP通讯规格书\WebAPI\超毅项目Web API通讯规格书 v4.0.docx")
TMP = DOCX.with_suffix(".method-font.tmp.docx")
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def qn(name: str) -> str:
    prefix, tag = name.split(":")
    return f"{{{NS[prefix]}}}{tag}"


def set_run(run, font: str, size_half_pt: str) -> None:
    r_pr = run.find("w:rPr", namespaces=NS)
    if r_pr is None:
        r_pr = etree.Element(qn("w:rPr"))
        run.insert(0, r_pr)
    r_fonts = r_pr.find("w:rFonts", namespaces=NS)
    if r_fonts is None:
        r_fonts = etree.Element(qn("w:rFonts"))
        r_pr.insert(0, r_fonts)
    for key in ("ascii", "hAnsi", "eastAsia", "cs"):
        r_fonts.set(qn(f"w:{key}"), font)
    sz = r_pr.find("w:sz", namespaces=NS)
    if sz is None:
        sz = etree.Element(qn("w:sz"))
        r_pr.append(sz)
    sz.set(qn("w:val"), size_half_pt)
    sz_cs = r_pr.find("w:szCs", namespaces=NS)
    if sz_cs is None:
        sz_cs = etree.Element(qn("w:szCs"))
        r_pr.append(sz_cs)
    sz_cs.set(qn("w:val"), size_half_pt)


def patch_document_xml(data: bytes) -> bytes:
    root = etree.fromstring(data)
    for tr in root.xpath(".//w:tbl/w:tr", namespaces=NS):
        cells = tr.xpath("./w:tc", namespaces=NS)
        texts = ["".join(tc.xpath(".//w:t/text()", namespaces=NS)).strip() for tc in cells]
        is_method_header = "接口调用方" in texts and "接口提供方" in texts
        is_method_value = len(texts) >= 4 and texts[0] == "Web API"
        if not (is_method_header or is_method_value):
            continue
        for idx, tc in enumerate(cells):
            font, size = ("Cambria", "14") if idx <= 2 else ("Microsoft YaHei", "16")
            for run in tc.xpath(".//w:r", namespaces=NS):
                set_run(run, font, size)
    return etree.tostring(root, encoding="UTF-8", xml_declaration=True, standalone="yes")


def main() -> None:
    with ZipFile(DOCX, "r") as zin, ZipFile(TMP, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                data = patch_document_xml(data)
            zout.writestr(item, data)
    TMP.replace(DOCX)
    print(DOCX)


if __name__ == "__main__":
    main()
