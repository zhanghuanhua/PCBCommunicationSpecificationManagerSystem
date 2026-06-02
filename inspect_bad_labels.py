from docx import Document

d = Document(r"E:\MulTek\02设计文档\EAP通讯规格书\WebAPI\超毅项目Web API通讯规格书 v4.0.docx")
for ti, t in enumerate(d.tables):
    for ri, r in enumerate(t.rows):
        for ci, c in enumerate(r.cells):
            if "返回值列表表" in c.text:
                print(ti, ri, ci, repr(c.text))
                raise SystemExit
print("not found")
