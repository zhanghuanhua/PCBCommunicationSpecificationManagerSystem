from zipfile import ZipFile
from lxml import etree

p = r"E:\MulTek\02设计文档\EAP通讯规格书\WebAPI\超毅项目Web API通讯规格书 v4.0.docx"
ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
root = etree.fromstring(ZipFile(p).read("word/document.xml"))
tr = root.xpath(".//w:tbl/w:tr[.//w:t[contains(., '接口调用方')]][1]", namespaces=ns)[0]
for i, tc in enumerate(tr.xpath("./w:tc", namespaces=ns)):
    print("cell", i, "".join(tc.xpath(".//w:t/text()", namespaces=ns)))
    for r in tc.xpath(".//w:r", namespaces=ns):
        text = "".join(r.xpath(".//w:t/text()", namespaces=ns))
        rf = r.xpath("./w:rPr/w:rFonts/@w:eastAsia", namespaces=ns)
        sz = r.xpath("./w:rPr/w:sz/@w:val", namespaces=ns)
        print(" ", repr(text), rf, sz)
