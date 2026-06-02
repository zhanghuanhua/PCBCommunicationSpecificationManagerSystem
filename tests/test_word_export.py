from pathlib import Path

from docx import Document

from app.models import ApiInterface, InterfaceDirection
from app.services.word_export import export_word_document


def test_word_export_creates_docx_with_watermark(tmp_path: Path):
    interface = ApiInterface(
        id=1,
        code="EQP-EAP-037",
        name="测试接口",
        direction=InterfaceDirection.EQP_TO_EAP,
        api_name="EQP_Test",
        caller="EQP",
        provider="EAP",
        requirement="测试需求",
        scenario="测试场景",
        service_description="测试服务",
    )
    output = tmp_path / "spec.docx"

    export_word_document(
        output,
        [interface],
        {1: {"From": "EQP", "Message": "EQP_Test", "Content": {}}},
        {1: {"Code": "0000", "Success": True, "Content": {}}},
        watermark_text="厂商查看",
    )

    assert output.exists()
    document = Document(output)
    body_text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    header_text = "\n".join(
        paragraph.text
        for section in document.sections
        for paragraph in section.header.paragraphs
    )
    assert "珠海超毅 EAP-EQP API 接口通讯规格书" in body_text
    assert "EQP-EAP-037 测试接口" in body_text
    assert "厂商查看" in header_text
