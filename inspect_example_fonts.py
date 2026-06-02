from pathlib import Path
from zipfile import ZipFile
from lxml import etree

DOCX = Path(r"E:\MulTek\02设计文档\EAP通讯规格书\WebAPI\超毅项目Web API通讯规格书 v4.0.docx")
ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
with ZipFile(DOCX) as z:
    root = etree.fromstring(z.read("word/document.xml"))
tbls = root.xpath(".//w:tbl[.//w:t[contains(., '日志范例')]]", namespaces=ns)
for ti, tbl in enumerate(tbls[:3]):
    for r in tbl.xpath(".//w:r", namespaces=ns):
        text = "".join(r.xpath(".//w:t/text()", namespaces=ns))
        rf = r.find("w:rPr/w:rFonts", namespaces=ns)
        sz = r.find("w:rPr/w:sz", namespaces=ns)
        east = rf.get(f"{{{ns['w']}}}eastAsia") if rf is not None else None
        val = sz.get(f"{{{ns['w']}}}val") if sz is not None else None
        if east != "Cambria" or val != "14":
            print("table", ti, "text", repr(text[:40]), "font", east, "size", val)
            break
