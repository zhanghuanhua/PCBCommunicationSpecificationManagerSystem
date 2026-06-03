from pathlib import Path

from docx import Document

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
