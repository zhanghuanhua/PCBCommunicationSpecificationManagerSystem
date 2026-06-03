import json
from pathlib import Path

from docx import Document

from app.models import ApiInterface, InterfaceDirection
from app.services.watermark import add_text_watermark


def export_word_document(
    output_path: Path,
    interfaces: list[ApiInterface],
    request_examples: dict[int, dict],
    response_examples: dict[int, dict],
    watermark_text: str = "",
    template_path: Path | None = None,
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
    )
    _append_direction(
        document,
        interfaces,
        InterfaceDirection.EAP_TO_EQP,
        "EAP -> EQP 接口",
        request_examples,
        response_examples,
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

        document.add_paragraph("请求示例")
        document.add_paragraph(
            json.dumps(request_examples.get(key, {}), ensure_ascii=False, indent=2)
        )
        document.add_paragraph("响应示例")
        document.add_paragraph(
            json.dumps(response_examples.get(key, {}), ensure_ascii=False, indent=2)
        )


def _add_row(table, *values: str) -> None:
    row = table.add_row()
    for index, value in enumerate(values):
        row.cells[index].text = value
