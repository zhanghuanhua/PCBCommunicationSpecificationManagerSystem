import json
from pathlib import Path

from docx import Document

from app.models import ApiInterface, ApiParameter, InterfaceDirection, ParameterKind
from app.services.watermark import add_text_watermark


def export_word_document(
    output_path: Path,
    interfaces: list[ApiInterface],
    request_examples: dict[int, dict],
    response_examples: dict[int, dict],
    watermark_text: str = "",
    template_path: Path | None = None,
    parameters_by_interface: dict[int, list[ApiParameter]] | None = None,
) -> Path:
    document = Document(template_path) if template_path else Document()
    add_text_watermark(document, watermark_text)
    if template_path:
        document.add_page_break()
        document.add_heading("系统新增接口内容", level=1)
        document.add_paragraph("以下内容由接口管理系统自动追加。")
    else:
        document.add_heading("珠海超毅 EAP-EQP API 接口通讯规格书", level=0)
        document.add_paragraph("本文档由接口管理系统自动生成。")

    _append_direction(
        document,
        interfaces,
        InterfaceDirection.EQP_TO_EAP,
        "EQP -> EAP 接口",
        request_examples,
        response_examples,
        parameters_by_interface or {},
    )
    _append_direction(
        document,
        interfaces,
        InterfaceDirection.EAP_TO_EQP,
        "EAP -> EQP 接口",
        request_examples,
        response_examples,
        parameters_by_interface or {},
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(output_path)
    return output_path


def _append_direction(
    document: Document,
    interfaces: list[ApiInterface],
    direction: InterfaceDirection,
    heading: str,
    request_examples: dict[int, dict],
    response_examples: dict[int, dict],
    parameters_by_interface: dict[int, list[ApiParameter]],
) -> None:
    document.add_heading(heading, level=1)
    for item in interfaces:
        if item.direction != direction:
            continue

        key = item.id or 0
        document.add_heading(f"{item.code} {item.name}", level=2)

        table = document.add_table(rows=0, cols=4)
        _add_row(table, "需求说明", item.requirement, item.requirement, item.requirement)
        _add_row(table, "使用场景", item.scenario, item.scenario, item.scenario)
        _add_row(table, "接口名称", item.api_name, item.api_name, item.api_name)
        _add_row(table, "接口方式", "接口调用方", "接口提供方", "接口服务描述")
        _add_row(table, "Web API", item.caller, item.provider, item.service_description)

        parameters = parameters_by_interface.get(key, [])
        document.add_heading("请求参数", level=3)
        _append_parameter_table(document, parameters, ParameterKind.REQUEST)
        document.add_heading("响应参数", level=3)
        _append_parameter_table(document, parameters, ParameterKind.RESPONSE)

        document.add_heading("日志范例", level=3)
        document.add_paragraph("请求日志范例")
        document.add_paragraph(item.request_log_example or json.dumps(request_examples.get(key, {}), ensure_ascii=False, indent=2))
        document.add_paragraph("响应日志范例")
        document.add_paragraph(item.response_log_example or json.dumps(response_examples.get(key, {}), ensure_ascii=False, indent=2))


def _append_parameter_table(
    document: Document,
    parameters: list[ApiParameter],
    kind: ParameterKind,
) -> None:
    items = [
        parameter
        for parameter in sorted(parameters, key=lambda item: (item.sort_order, item.id or 0))
        if parameter.kind == kind
    ]
    table = document.add_table(rows=1, cols=5)
    headers = ["字段名", "类型", "必填", "数组", "说明"]
    for index, header in enumerate(headers):
        table.rows[0].cells[index].text = header
    if not items:
        _add_row(table, "无", "", "", "", "")
        return
    for parameter in items:
        _add_row(
            table,
            parameter.field_name,
            parameter.data_type,
            "是" if parameter.required else "否",
            "是" if parameter.is_array else "否",
            parameter.description,
        )


def _add_row(table, *values: str) -> None:
    row = table.add_row()
    for index, value in enumerate(values):
        row.cells[index].text = value
