from collections import Counter
from pathlib import Path
from zipfile import ZipFile

from docx import Document
from lxml import etree

DOCX = Path(r"E:\MulTek\02设计文档\EAP通讯规格书\WebAPI\超毅项目Web API通讯规格书 v4.0.docx")
TEXT = Path("review_output_v4_fmt/docx_extract.txt").read_text(encoding="utf-8")

print("bad_label_found", "返回值列表表" in TEXT or "请求参数列表表" in TEXT or "参数列表表" in TEXT)

doc = Document(str(DOCX))
example_idx = []
normal_idx = []
for i, table in enumerate(doc.tables):
    table_text = "\n".join(cell.text for row in table.rows for cell in row.cells)
    if "日志范例" in table_text:
        example_idx.append(i)
    else:
        normal_idx.append(i)
print("normal_tables", len(normal_idx), "example_tables", len(example_idx))

with ZipFile(DOCX) as z:
    root = etree.fromstring(z.read("word/document.xml"))

ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
tbls = root.xpath(".//w:tbl", namespaces=ns)


def font_counts(tbl):
    east = Counter()
    sizes = Counter()
    for r in tbl.xpath(".//w:r", namespaces=ns):
        rfonts = r.find("w:rPr/w:rFonts", namespaces=ns)
        sz = r.find("w:rPr/w:sz", namespaces=ns)
        if rfonts is not None:
            east[rfonts.get(qn("w:eastAsia"))] += 1
        if sz is not None:
            sizes[sz.get(qn("w:val"))] += 1
    return east, sizes


def qn(name):
    prefix, tag = name.split(":")
    return f"{{{ns[prefix]}}}{tag}"


if normal_idx:
    east, sizes = font_counts(tbls[normal_idx[0]])
    print("first_normal_fonts", east.most_common(3), "sizes", sizes.most_common(3))
if example_idx:
    east, sizes = font_counts(tbls[example_idx[0]])
    print("first_example_fonts", east.most_common(3), "sizes", sizes.most_common(3))
