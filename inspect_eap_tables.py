from docx import Document

d = Document(r"E:\MulTek\02设计文档\EAP通讯规格书\WebAPI\超毅项目Web API通讯规格书 v3.8.docx")
for i, t in enumerate(d.tables):
    text = "\n".join(c.text for r in t.rows for c in r.cells)
    if "EAP_InitialDataRequest" in text or "EAP_ DateTimeSyncCommand" in text or "EAP_DateTimeSyncCommand" in text:
        print(i, text[:300].replace("\n", " | "))
