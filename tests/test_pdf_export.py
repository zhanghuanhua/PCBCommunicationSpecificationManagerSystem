from pathlib import Path

import pytest

from app.models import ApiInterface, ApiParameter, InterfaceDirection, ParameterKind
from app.services.pdf_export import PdfConversionError, build_pdf_sections, export_basic_pdf, export_pdf_document


def test_basic_pdf_export_creates_file(tmp_path: Path):
    output = tmp_path / "spec.pdf"

    export_basic_pdf(output, "珠海超毅 EAP-EQP API 接口通讯规格书", watermark_text="厂商查看")

    assert output.exists()
    assert output.stat().st_size > 0


def test_pdf_export_sections_include_interface_parameters_and_logs():
    interface = ApiInterface(
        id=1,
        code="EAP-EQP-001",
        name="初始化状态请求",
        direction=InterfaceDirection.EAP_TO_EQP,
        api_name="EAP_InitialDataRequest",
        caller="EAP",
        provider="EQP",
        request_log_example='{"Content":{"IP":"127.0.0.1"}}',
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
            description="处理结果",
        ),
    ]

    sections = build_pdf_sections(
        [interface],
        {1: {"Content": {"IP": "127.0.0.1"}}},
        {1: {"Content": {"Result": True}}},
        {1: parameters},
    )

    content = "\n".join(sections)
    assert "EAP-EQP-001 初始化状态请求" in content
    assert "请求参数" in content
    assert "IP | string | 是 | 否 | IP地址" in content
    assert "响应参数" in content
    assert "Result | bool | 否 | 是 | 处理结果" in content
    assert "请求日志范例" in content
    assert '"IP":"127.0.0.1"' in content
    assert "响应日志范例" in content
    assert '"Result":true' in content


def test_full_pdf_export_requires_docx_conversion_source(tmp_path: Path):
    interface = ApiInterface(
        id=1,
        code="EQP-EAP-201",
        name="参数导出测试",
        direction=InterfaceDirection.EQP_TO_EAP,
        api_name="EQP_ParamExport",
        caller="EQP",
        provider="EAP",
    )
    parameter = ApiParameter(
        interface_id=1,
        kind=ParameterKind.REQUEST,
        sort_order=1,
        field_name="LotId",
        data_type="string",
        required=True,
        is_array=False,
        description="批次号",
    )
    output = tmp_path / "full_spec.pdf"

    with pytest.raises(PdfConversionError):
        export_pdf_document(
            output,
            [interface],
            {1: {"Content": {"LotId": "L001"}}},
            {1: {"Content": {}}},
            {1: [parameter]},
            watermark_text="厂商查看",
        )

    assert not output.exists()
