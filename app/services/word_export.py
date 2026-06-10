import copy
import json
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.shared import Pt
from docx.table import Table
from docx.text.paragraph import Paragraph

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
    document_version: str | None = None,
) -> Path:
    document = Document(template_path) if template_path else Document()
    add_text_watermark(document, watermark_text)
    templates = _find_interface_templates(document)
    version = document_version or _version_from_interfaces(interfaces)

    if template_path:
        _normalize_template_front_matter(document, version)
        _remove_existing_interface_content(document)
    else:
        _add_heading(document, "珠海超毅 EAP-EQP API 接口通讯规格书", level=0)
        document.add_paragraph(f"Version: {version}")
        document.add_paragraph("本文档由接口管理系统自动生成。")
        document.add_page_break()

    _ensure_toc_page(document, interfaces, version)
    _add_template_like_paragraph(document, templates.heading, "三、 接口内容")
    _append_direction(
        document,
        interfaces,
        InterfaceDirection.EQP_TO_EAP,
        "1. EQP -> EAP 接口",
        templates,
        request_examples,
        response_examples,
        parameters_by_interface or {},
        version,
    )
    _append_direction(
        document,
        interfaces,
        InterfaceDirection.EAP_TO_EQP,
        "2. EAP -> EQP 接口",
        templates,
        request_examples,
        response_examples,
        parameters_by_interface or {},
        version,
    )
    _replace_all_version_text(document, version)
    _remove_toc_fields_and_bookmarks(document)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(output_path)
    return output_path


class _InterfaceTemplates:
    def __init__(
        self,
        heading: CT_P | None,
        direction_heading: CT_P | None,
        title: CT_P | None,
        main_table: CT_Tbl | None,
        log_table: CT_Tbl | None,
    ) -> None:
        self.heading = heading
        self.direction_heading = direction_heading
        self.title = title
        self.main_table = main_table
        self.log_table = log_table


def _append_direction(
    document: Document,
    interfaces: list[ApiInterface],
    direction: InterfaceDirection,
    heading: str,
    templates: _InterfaceTemplates,
    request_examples: dict[int, dict],
    response_examples: dict[int, dict],
    parameters_by_interface: dict[int, list[ApiParameter]],
    document_version: str,
) -> None:
    _add_template_like_paragraph(document, templates.direction_heading, heading)
    for item in _interfaces_for_direction(interfaces, direction):
        key = item.id or 0
        item.version = document_version
        _add_template_like_paragraph(document, templates.title, f"{item.code} {item.name}")
        main_table = _append_template_table(document, templates.main_table, 4)
        _fill_interface_table(main_table, item, parameters_by_interface.get(key, []))
        document.add_paragraph("")
        log_table = _append_template_table(document, templates.log_table, 3)
        _fill_log_table(log_table, item, request_examples.get(key, {}), response_examples.get(key, {}))


def _interfaces_for_direction(
    interfaces: list[ApiInterface], direction: InterfaceDirection
) -> list[ApiInterface]:
    return [
        item
        for item in sorted(interfaces, key=_interface_sort_key)
        if _effective_direction(item) == direction
    ]


def _effective_direction(interface: ApiInterface) -> InterfaceDirection:
    code = interface.code.upper()
    if code.startswith("EQP-EAP-"):
        return InterfaceDirection.EQP_TO_EAP
    if code.startswith("EAP-EQP-"):
        return InterfaceDirection.EAP_TO_EQP
    return interface.direction


def _version_from_interfaces(interfaces: list[ApiInterface]) -> str:
    for item in interfaces:
        if item.version:
            return item.version
    return "4.0"


def _interface_sort_key(interface: ApiInterface) -> tuple[int, str]:
    code = interface.code.upper()
    if code.startswith("EQP-EAP-") or code.startswith("EAP-EQP-"):
        return (0, code)
    return (1, f"{interface.created_at.isoformat()}-{interface.id or 0}")


def _find_interface_templates(document: Document) -> _InterfaceTemplates:
    blocks = list(_iter_document_blocks(document))
    heading = None
    direction_heading = None
    title = None
    main_table = None
    log_table = None

    for index, block in enumerate(blocks):
        if isinstance(block, Paragraph) and block.text.strip() == "三、 接口内容":
            heading = block._p
        if isinstance(block, Paragraph) and "EQP -> EAP" in block.text and "接口" in block.text:
            direction_heading = block._p
        if isinstance(block, Paragraph) and "EQP-EAP-001" in block.text:
            title = block._p
            for next_block in blocks[index + 1 :]:
                if isinstance(next_block, Table) and _is_interface_table(next_block):
                    main_table = next_block._tbl
                    break
            continue
        if main_table is not None and isinstance(block, Table) and _is_log_table(block):
            log_table = block._tbl
            break

    return _InterfaceTemplates(heading, direction_heading, title, main_table, log_table)


def _iter_document_blocks(document: Document):
    for child in document.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, document)
        elif isinstance(child, CT_Tbl):
            yield Table(child, document)


def _remove_existing_interface_content(document: Document) -> None:
    body = document.element.body
    children = list(body)
    start_index = None
    for index, child in enumerate(children):
        if not child.tag.endswith("p"):
            continue
        text = Paragraph(child, document).text.strip()
        if "接口内容" in text:
            start_index = index
            break
    for index, child in enumerate(children):
        if start_index is not None:
            break
        if child.tag.endswith("tbl") and _is_interface_table(Table(child, document)):
            start_index = _previous_interface_heading_index(children, index, document)
            break
    if start_index is None:
        return
    for child in children[start_index:]:
        if child.tag.endswith("sectPr"):
            continue
        body.remove(child)


def _normalize_template_front_matter(document: Document, version: str) -> None:
    _replace_all_version_text(document, version)
    _remove_toc_fields_and_bookmarks(document)


def _ensure_toc_page(document: Document, interfaces: list[ApiInterface], version: str) -> None:
    body = document.element.body
    insert_index = _remove_existing_toc(document)
    if insert_index is None:
        return
    created = []
    before_break = document.add_paragraph()
    before_break.add_run().add_break()
    created.append(before_break._p)
    title = document.add_paragraph("目录")
    created.append(title._p)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if title.runs:
        title.runs[0].bold = True
        title.runs[0].font.size = Pt(18)
    _add_toc_line(document, created, "珠海超毅 EAP-EQP API 接口通讯规格书", "1", 0)
    _add_toc_line(document, created, "一、 文档概述", "", 0)
    _add_toc_line(document, created, "二、 约定", "", 0)
    _add_toc_line(document, created, "1.接口参数定义：", "", 1)
    _add_toc_line(document, created, "2.基础访问地址：", "", 1)
    _add_toc_line(document, created, "三、 接口内容", "", 0)
    _add_toc_line(document, created, "1.EQP -> EAP 接口", "", 0)
    for item in _interfaces_for_direction(interfaces, InterfaceDirection.EQP_TO_EAP):
        _add_toc_line(document, created, f"{item.code} {item.name}", "", 1)
    _add_toc_line(document, created, "2.EAP -> EQP 接口", "", 0)
    for item in _interfaces_for_direction(interfaces, InterfaceDirection.EAP_TO_EQP):
        _add_toc_line(document, created, f"{item.code} {item.name}", "", 1)
    after_break = document.add_paragraph()
    after_break.add_run().add_break()
    created.append(after_break._p)
    for element in created:
        body.remove(element)
    for offset, element in enumerate(created):
        body.insert(insert_index + offset, element)


def _remove_existing_toc(document: Document) -> int | None:
    body = document.element.body
    children = list(body)
    for index, child in enumerate(children):
        if child.tag.endswith("sdt") and _element_text(child).strip().startswith("目录"):
            body.remove(child)
            before = _previous_paragraph_index_with_page_break(children, index)
            if before is not None and children[before].getparent() is body:
                body.remove(children[before])
                return before
            return index
        if child.tag.endswith("p") and Paragraph(child, document).text.strip() == "目录":
            end_index = _toc_end_index(children, index + 1, document)
            for item in children[index:end_index]:
                if item.getparent() is body:
                    body.remove(item)
            before = _previous_paragraph_index_with_page_break(children, index)
            if before is not None and children[before].getparent() is body:
                body.remove(children[before])
                return before
            return index
    return None


def _previous_paragraph_index_with_page_break(children: list, index: int) -> int | None:
    for candidate in range(index - 1, max(-1, index - 4), -1):
        if children[candidate].tag.endswith("p") and children[candidate].find(".//" + qn("w:br")) is not None:
            return candidate
    return None


def _toc_end_index(children: list, start_index: int, document: Document) -> int:
    for index in range(start_index, len(children)):
        child = children[index]
        if not child.tag.endswith("p"):
            continue
        text = Paragraph(child, document).text.strip()
        if text.startswith("一、") or text.startswith("三、") or text.startswith("1."):
            return index
    return start_index


def _add_toc_line(document: Document, created: list, title: str, page: str, level: int) -> None:
    paragraph = document.add_paragraph()
    created.append(paragraph._p)
    paragraph.paragraph_format.left_indent = Pt(18 * level)
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.0
    paragraph.add_run(title)
    if page:
        paragraph.add_run("\t")
        paragraph.add_run(page)


def _replace_all_version_text(document: Document, version: str) -> None:
    for paragraph in _iter_all_paragraphs(document):
        _replace_version_in_paragraph(paragraph, version)
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    _replace_version_in_paragraph(paragraph, version)


def _iter_all_paragraphs(document: Document):
    for paragraph in document.paragraphs:
        yield paragraph
    for section in document.sections:
        for paragraph in section.header.paragraphs:
            yield paragraph
        for paragraph in section.footer.paragraphs:
            yield paragraph


def _replace_version_in_paragraph(paragraph: Paragraph, version: str) -> None:
    text = paragraph.text
    if not text:
        return
    new_text = re.sub(r"(Version\s*:\s*)\d+(?:\.\d+)*", rf"\g<1>{version}", text, flags=re.IGNORECASE)
    new_text = re.sub(r"([vV])\d+(?:\.\d+)*", rf"\g<1>{version}", new_text)
    if new_text != text:
        _set_paragraph_text(paragraph, new_text)


def _remove_toc_fields_and_bookmarks(document: Document) -> None:
    body = document.element.body
    for el in list(body.iter()):
        tag = el.tag
        if tag in {qn("w:bookmarkStart"), qn("w:bookmarkEnd")}:
            name = el.get(qn("w:name"), "")
            if name.startswith("_Toc") or tag == qn("w:bookmarkEnd"):
                parent = el.getparent()
                if parent is not None:
                    parent.remove(el)
        if tag == qn("w:instrText") and el.text and ("TOC" in el.text or "PAGEREF" in el.text or "REF" in el.text):
            el.text = ""


def _element_text(element) -> str:
    return "".join(node.text or "" for node in element.iter() if node.tag == qn("w:t"))


def _previous_interface_heading_index(children, table_index: int, document: Document) -> int:
    for index in range(table_index - 1, -1, -1):
        child = children[index]
        if not child.tag.endswith("p"):
            continue
        text = Paragraph(child, document).text.strip()
        if "EQP-EAP-" in text or "EAP-EQP-" in text:
            return index
        if "接口内容" in text:
            return index
    return table_index


def _add_template_like_paragraph(document: Document, template: CT_P | None, text: str) -> Paragraph:
    if template is None:
        paragraph = document.add_paragraph(text)
        return paragraph
    element = copy.deepcopy(template)
    document.element.body.append(element)
    paragraph = Paragraph(element, document)
    _set_paragraph_text(paragraph, text)
    _clear_page_break_before(paragraph)
    return paragraph


def _clear_page_break_before(paragraph: Paragraph) -> None:
    paragraph.paragraph_format.page_break_before = False


def _append_template_table(document: Document, template: CT_Tbl | None, cols: int) -> Table:
    if template is None:
        return document.add_table(rows=0, cols=cols)
    element = copy.deepcopy(template)
    document.element.body.append(element)
    return Table(element, document)


def _fill_interface_table(table: Table, interface: ApiInterface, parameters: list[ApiParameter]) -> None:
    _ensure_table_rows(table, 13)
    _set_row(table, 0, ["需求说明", interface.requirement, interface.requirement, interface.requirement])
    _set_row(table, 1, ["使用场景", interface.scenario, interface.scenario, interface.scenario])
    _set_row(table, 2, ["接口名称", interface.api_name, interface.api_name, interface.api_name])
    _set_row(table, 3, ["接口方式", "接口调用方", "接口提供方", "接口服务描述"])
    _set_row(table, 4, ["Web API", interface.caller, interface.provider, interface.service_description])

    request_rows = _parameter_rows(parameters, ParameterKind.REQUEST)
    response_rows = _parameter_rows(parameters, ParameterKind.RESPONSE)
    rows = [
        ("section", ["请求参数列表", "请求参数列表", "请求参数列表", "请求参数列表"]),
        ("header", ["序号", "字段", "类型", "描述"]),
        ("detail", ["1", "From", "string", f"调用接口来源（{interface.caller}）"]),
        ("detail", ["2", "Message", "string", "消息（接口名）"]),
        ("detail", ["3", "DateTime", "DateTime", "系统时间（秒）（格式：yyyy/MM/dd HH:mm:ss）"]),
        ("detail", ["4", "Content", "object", "参数内容" if request_rows else "空"]),
        ("detail", ["5", "RequestId", "string", "请求 ID（17位唯一标识符：yyyyMMddHHmmssfff）（Format:毫秒时间格式）"]),
        ("detail", ["Content", "Content", "Content", "Content"]),
        *[("detail", row) for row in request_rows],
        ("section", ["返回值列表", "返回值列表", "返回值列表", "返回值列表"]),
        ("header", ["序号", "字段", "类型", "描述"]),
        ("detail", ["1", "Code", "string", "结果代码(0000=成功， 其余为错误代号)"]),
        ("detail", ["2", "Success", "bool", "执行成功与否"]),
        ("detail", ["3", "Msg", "string", "提示讯息"]),
        ("detail", ["4", "DateTime", "DateTime", "系统时间（秒）（格式：yyyy/MM/dd HH:mm:ss）"]),
        ("detail", ["5", "Content", "object", "参数内容" if response_rows else "空"]),
        *[("detail", row) for row in response_rows],
        ("detail", ["6", "RequestId", "string", "回复请求 ID（EAP返回的17位的唯一标识，与请求的RequestID一致）"]),
    ]
    _replace_rows_from(table, 5, rows)


def _parameter_rows(parameters: list[ApiParameter], kind: ParameterKind) -> list[list[str]]:
    rows = []
    items = [
        parameter
        for parameter in sorted(parameters, key=lambda item: (item.sort_order, item.id or 0))
        if parameter.kind == kind
    ]
    for index, parameter in enumerate(items, start=1):
        rows.append(
            [
                f"4.{index}",
                parameter.field_name,
                parameter.data_type,
                _format_parameter_description(parameter),
            ]
        )
    return rows


def _fill_log_table(table: Table, interface: ApiInterface, request_example: dict, response_example: dict) -> None:
    _ensure_table_rows(table, 2)
    request_text = interface.request_log_example or _format_request_log(interface, request_example)
    response_text = interface.response_log_example or json.dumps(response_example, ensure_ascii=False, indent=2)
    _set_row(table, 0, ["日志范例", "请求", request_text])
    _set_row(table, 1, ["日志范例", "应答", response_text])
    while len(table.rows) > 2:
        table._tbl.remove(table.rows[-1]._tr)


def _replace_rows_from(table: Table, start_index: int, rows: list[tuple[str, list[str]]]) -> None:
    section_template = copy.deepcopy(table.rows[start_index]._tr)
    header_template = copy.deepcopy(table.rows[start_index + 1]._tr if len(table.rows) > start_index + 1 else table.rows[start_index]._tr)
    detail_template = copy.deepcopy(table.rows[start_index + 2]._tr if len(table.rows) > start_index + 2 else table.rows[start_index]._tr)
    templates = {
        "section": section_template,
        "header": header_template,
        "detail": detail_template,
    }
    while len(table.rows) > start_index:
        table._tbl.remove(table.rows[-1]._tr)
    for row_kind, row_values in rows:
        new_row = copy.deepcopy(templates[row_kind])
        table._tbl.append(new_row)
        _set_row(table, len(table.rows) - 1, row_values)


def _ensure_table_rows(table: Table, count: int) -> None:
    while len(table.rows) < count:
        table.add_row()


def _set_row(table: Table, row_index: int, values: list[str]) -> None:
    row = table.rows[row_index]
    for index, value in enumerate(values):
        if index < len(row.cells):
            _set_cell_text(row.cells[index], value)


def _set_cell_text(cell, text: str) -> None:
    paragraphs = cell.paragraphs
    if not paragraphs:
        cell.text = text or ""
        return
    _set_paragraph_text(paragraphs[0], text or "")
    for paragraph in paragraphs[1:]:
        paragraph._element.getparent().remove(paragraph._element)


def _set_paragraph_text(paragraph: Paragraph, text: str) -> None:
    if paragraph.runs:
        paragraph.runs[0].text = text
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.add_run(text)


def _format_request_log(interface: ApiInterface, request_example: dict) -> str:
    return f"REST:POST http://IP:Port/api/{interface.api_name}\n{json.dumps(request_example, ensure_ascii=False, indent=2)}"


def _format_parameter_description(parameter: ApiParameter) -> str:
    suffix = "（必填）" if parameter.required else "（非必填）"
    if parameter.is_array:
        suffix = f"{suffix}（数组）"
    return f"{parameter.description}{suffix}" if parameter.description else suffix


def _is_interface_table(table: Table) -> bool:
    if len(table.columns) != 4 or not table.rows:
        return False
    text = _table_text(table)
    return "需求说明" in text and "接口名称" in text


def _is_log_table(table: Table) -> bool:
    if len(table.columns) != 3:
        return False
    return "日志范例" in _table_text(table)


def _table_text(table: Table) -> str:
    return "\n".join(cell.text for row in table.rows for cell in row.cells)


def _add_heading(document: Document, text: str, level: int):
    try:
        return document.add_heading(text, level=level)
    except KeyError:
        paragraph = document.add_paragraph(text)
        for run in paragraph.runs:
            run.bold = True
        return paragraph
