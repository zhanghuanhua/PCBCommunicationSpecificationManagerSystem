from pathlib import Path

from docx import Document

from app.models import ParameterKind
from app.services.spec_parser import parse_interface_basics_from_docx


def test_parse_interface_basics_from_docx_extracts_codes_names_and_api(tmp_path: Path):
    docx_path = tmp_path / "spec.docx"
    document = Document()
    document.add_heading("EQP-EAP-001 连线检查", level=2)
    document.add_paragraph("接口名称 EQP_AliveCheck")
    document.add_heading("EAP-EQP-002 启动设备", level=2)
    document.add_paragraph("API 名称 EAP_StartMachine")
    document.save(docx_path)

    result = parse_interface_basics_from_docx(docx_path)

    assert len(result) == 2
    assert result[0].code == "EQP-EAP-001"
    assert result[0].name == "连线检查"
    assert result[0].api_name == "EQP_AliveCheck"
    assert result[0].caller == "EQP"
    assert result[0].provider == "EAP"
    assert result[1].code == "EAP-EQP-002"
    assert result[1].name == "启动设备"
    assert result[1].api_name == "EAP_StartMachine"
    assert result[1].caller == "EAP"
    assert result[1].provider == "EQP"


def test_parse_interface_basics_from_docx_extracts_request_and_response_parameters(tmp_path: Path):
    docx_path = tmp_path / "spec.docx"
    document = Document()
    document.add_heading("EQP-EAP-001 连线检查", level=2)
    document.add_paragraph("接口名称 EQP_AliveCheck")
    document.add_paragraph("请求参数")
    request_table = document.add_table(rows=1, cols=5)
    headers = ["字段名", "类型", "必填", "示例值", "说明"]
    for index, header in enumerate(headers):
        request_table.rows[0].cells[index].text = header
    request_row = request_table.add_row()
    request_values = ["LotId", "string", "是", "L001", "批次号"]
    for index, value in enumerate(request_values):
        request_row.cells[index].text = value
    document.add_paragraph("响应参数")
    response_table = document.add_table(rows=1, cols=5)
    for index, header in enumerate(headers):
        response_table.rows[0].cells[index].text = header
    response_row = response_table.add_row()
    response_values = ["Result", "bool", "是", "true", "处理结果"]
    for index, value in enumerate(response_values):
        response_row.cells[index].text = value
    document.save(docx_path)

    result = parse_interface_basics_from_docx(docx_path)

    assert len(result) == 1
    assert len(result[0].parameters) == 2
    assert result[0].parameters[0].kind == ParameterKind.REQUEST
    assert result[0].parameters[0].field_name == "LotId"
    assert result[0].parameters[0].data_type == "string"
    assert result[0].parameters[0].required is True
    assert result[0].parameters[0].example_value == "L001"
    assert result[0].parameters[0].description == "批次号"
    assert result[0].parameters[1].kind == ParameterKind.RESPONSE
    assert result[0].parameters[1].field_name == "Result"
