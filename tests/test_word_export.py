from pathlib import Path

from docx import Document

from app.models import ApiInterface, ApiParameter, InterfaceDirection, ParameterKind
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


def test_word_export_includes_formal_parameter_tables_and_saved_log_examples(tmp_path: Path):
    interface = ApiInterface(
        id=1,
        code="EAP-EQP-001",
        name="初始化状态请求",
        direction=InterfaceDirection.EAP_TO_EQP,
        api_name="EAP_InitialDataRequest",
        caller="EAP",
        provider="EQP",
        request_log_example='REST:POST http://IP:Port/api/EAP_InitialDataRequest\n{"Content":{"IP":"127.0.0.1"}}',
        response_log_example='{"Code":"0000","Content":{"Result":true}}',
    )
    parameters = [
        ApiParameter(
            interface_id=1,
            kind=ParameterKind.REQUEST,
            sort_order=1,
            field_name="IP",
            data_type="string",
            required=True,
            is_array=False,
            example_value="127.0.0.1",
            description="IP地址",
        ),
        ApiParameter(
            interface_id=1,
            kind=ParameterKind.RESPONSE,
            sort_order=1,
            field_name="Result",
            data_type="bool",
            required=False,
            is_array=True,
            example_value="true",
            description="处理结果",
        ),
    ]
    output = tmp_path / "spec_with_tables.docx"

    export_word_document(
        output,
        [interface],
        {1: {"Content": {"IP": "127.0.0.1"}}},
        {1: {"Content": {"Result": True}}},
        parameters_by_interface={1: parameters},
    )

    document = Document(output)
    body_text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    table_text = "\n".join(
        cell.text
        for table in document.tables
        for row in table.rows
        for cell in row.cells
    )

    assert "请求参数" in body_text
    assert "响应参数" in body_text
    assert "日志范例" in body_text
    assert "请求日志范例" in body_text
    assert "响应日志范例" in body_text
    assert "REST:POST http://IP:Port/api/EAP_InitialDataRequest" in body_text
    assert '"IP":"127.0.0.1"' in body_text
    assert '"Result":true' in body_text
    assert "字段名" in table_text
    assert "IP" in table_text
    assert "string" in table_text
    assert "是" in table_text
    assert "否" in table_text
    assert "IP地址" in table_text
    assert "Result" in table_text
    assert "bool" in table_text
    assert "处理结果" in table_text
