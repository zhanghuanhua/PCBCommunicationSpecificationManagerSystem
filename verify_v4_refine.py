from pathlib import Path
from zipfile import ZipFile

from lxml import etree

DOCX = Path(r"E:\MulTek\02设计文档\EAP通讯规格书\WebAPI\超毅项目Web API通讯规格书 v4.0.docx")
ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

with ZipFile(DOCX) as z:
    root = etree.fromstring(z.read("word/document.xml"))

example = root.xpath(".//w:tbl[.//w:t[contains(., '日志范例')]][1]", namespaces=ns)[0]
grid = [g.get(f"{{{ns['w']}}}w") for g in example.xpath("./w:tblGrid/w:gridCol", namespaces=ns)]
print("example_grid", grid)

method_tbl = None
for tbl in root.xpath(".//w:tbl", namespaces=ns):
    text = "".join(tbl.xpath(".//w:t/text()", namespaces=ns))
    if "接口调用方" in text and "接口提供方" in text:
        method_tbl = tbl
        break

if method_tbl is not None:
    for tr in method_tbl.xpath("./w:tr", namespaces=ns):
        row_text = ["".join(tc.xpath(".//w:t/text()", namespaces=ns)) for tc in tr.xpath("./w:tc", namespaces=ns)]
        if "接口调用方" in row_text or (row_text and row_text[0] == "Web API"):
            fonts = []
            sizes = []
            for tc in tr.xpath("./w:tc", namespaces=ns):
                rf = tc.xpath(".//w:rFonts/@w:eastAsia", namespaces=ns)
                sz = tc.xpath(".//w:sz/@w:val", namespaces=ns)
                fonts.append(rf[0] if rf else "")
                sizes.append(sz[0] if sz else "")
            print("method_row", row_text, fonts, sizes)
print("bad_labels", any(x in Path("review_output_v4_refine/docx_extract.txt").read_text(encoding="utf-8") for x in ["返回值列表表", "参数列表表"]))
