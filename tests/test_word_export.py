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


def test_word_export_appends_interfaces_to_imported_template(tmp_path: Path):
    template_path = tmp_path / "template.docx"
    template = Document()
    template.add_heading("原规格书标题", level=0)
    template.add_paragraph("这是原规格书已有内容。")
    template.save(template_path)

    interface = ApiInterface(
        id=1,
        code="EAP-EQP-009",
        name="启动设备",
        direction=InterfaceDirection.EAP_TO_EQP,
        api_name="EAP_StartMachine",
        caller="EAP",
        provider="EQP",
        requirement="启动设备需求",
        scenario="EAP 下发启动指令",
        service_description="启动设备服务",
    )
    output = tmp_path / "spec_from_template.docx"

    export_word_document(
        output,
        [interface],
        {1: {"From": "EAP", "Message": "EAP_StartMachine", "Content": {}}},
        {1: {"Code": "0000", "Success": True, "Content": {}}},
        template_path=template_path,
    )

    document = Document(output)
    body_text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    assert "原规格书标题" in body_text
    assert "这是原规格书已有内容。" in body_text
    assert "系统新增接口内容" in body_text
    assert "EAP-EQP-009 启动设备" in body_text
