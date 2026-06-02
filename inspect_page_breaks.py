from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from lxml import etree

DOCX = Path(r"E:\MulTek\02设计文档\EAP通讯规格书\WebAPI\超毅项目Web API通讯规格书 v4.0.docx")
ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
with ZipFile(DOCX) as z:
    root = etree.fromstring(z.read("word/document.xml"))

body = root.find("w:body", namespaces=ns)
blocks = list(body)
for i, block in enumerate(blocks):
    if block.xpath(".//w:br[@w:type='page']", namespaces=ns):
        before = "".join(blocks[i - 1].xpath(".//w:t/text()", namespaces=ns)) if i > 0 else ""
        cur = "".join(block.xpath(".//w:t/text()", namespaces=ns))
        after = "".join(blocks[i + 1].xpath(".//w:t/text()", namespaces=ns)) if i + 1 < len(blocks) else ""
        print("block", i, "before=", repr(before[:100]), "cur=", repr(cur[:100]), "after=", repr(after[:100]))
