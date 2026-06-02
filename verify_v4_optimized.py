from pathlib import Path
from zipfile import ZipFile

from lxml import etree

DOCX = Path(r"E:\MulTek\02设计文档\EAP通讯规格书\WebAPI\超毅项目Web API通讯规格书 v4.0.docx")
TEXT = Path("review_output_v4_opt/docx_extract.txt").read_text(encoding="utf-8")

print("bad_repeated_labels", any(x in TEXT for x in ("返回值列表表", "请求参数列表表", "参数列表表")))

ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
with ZipFile(DOCX) as z:
    for name in z.namelist():
        if name.startswith("word/header") and name.endswith(".xml"):
            text = z.read(name).decode("utf-8", errors="ignore")
            if "Version:" in text:
                print(name, "has_3.8", "Version: 3.8" in text, "has_4.0", "Version: 4.0" in text)
    root = etree.fromstring(z.read("word/document.xml"))
    brs = root.xpath(".//w:br[@w:type='page']", namespaces=ns)
    print("page_breaks", len(brs))
    fonts = root.xpath(".//w:tbl[.//w:t[contains(., '日志范例')]][1]//w:rFonts/@w:eastAsia", namespaces=ns)
    sizes = root.xpath(".//w:tbl[.//w:t[contains(., '日志范例')]][1]//w:sz/@w:val", namespaces=ns)
    print("first_example_font_sample", fonts[:5], "size_sample", sizes[:5])
