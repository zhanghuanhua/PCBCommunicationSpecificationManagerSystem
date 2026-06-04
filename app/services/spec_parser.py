import re
from dataclasses import dataclass
from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P

from app.models import InterfaceDirection, ParameterKind


INTERFACE_CODE_PATTERN = re.compile(r"\b(EQP-EAP|EAP-EQP)-\d{3,}\b", re.IGNORECASE)
API_NAME_PATTERN = re.compile(r"\b(EQP|EAP)_[A-Za-z0-9_]+\b")


@dataclass(frozen=True)
class ParsedParameter:
    kind: ParameterKind
    field_name: str
    data_type: str
    required: bool
    example_value: str
    description: str


@dataclass(frozen=True)
class ParsedInterface:
    code: str
    name: str
    direction: InterfaceDirection
    api_name: str
    caller: str
    provider: str
    parameters: list[ParsedParameter]


def parse_interface_basics_from_docx(docx_path: Path) -> list[ParsedInterface]:
    document = Document(docx_path)
    blocks = _extract_blocks(document)
    lines = [block["text"] for block in blocks if block["type"] == "text"]
    parsed: list[ParsedInterface] = []
    seen_codes: set[str] = set()

    text_index_by_block_index = _build_text_index_by_block_index(blocks)
    for block_index, block in enumerate(blocks):
        if block["type"] != "text":
            continue
        line = block["text"]
        match = INTERFACE_CODE_PATTERN.search(line)
        if not match:
            continue

        code = match.group(0).upper()
        if code in seen_codes:
            continue
        seen_codes.add(code)

        name = _extract_name(line, code)
        text_index = text_index_by_block_index[block_index]
        api_name = _find_api_name(lines, text_index, code)
        direction, caller, provider = _direction_parties(code)
        parameters = _extract_parameters_for_interface(blocks, block_index)
        parsed.append(
            ParsedInterface(
                code=code,
                name=name or code,
                direction=direction,
                api_name=api_name or _default_api_name(code),
                caller=caller,
                provider=provider,
                parameters=parameters,
            )
        )

    return parsed


def _extract_blocks(document: Document) -> list[dict]:
    blocks: list[dict] = []
    for item in _iter_document_blocks(document):
        if isinstance(item, Paragraph):
            text = item.text.strip()
            if text:
                blocks.append({"type": "text", "text": text})
        if isinstance(item, Table):
            rows = [[cell.text.strip() for cell in row.cells] for row in item.rows]
            if rows:
                blocks.append({"type": "table", "rows": rows, "text": _flatten_rows(rows)})
    return blocks


def _iter_document_blocks(document: Document):
    for child in document.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, document)
        elif isinstance(child, CT_Tbl):
            yield Table(child, document)


def _flatten_rows(rows: list[list[str]]) -> str:
    return " ".join(value for row in rows for value in row if value)


def _build_text_index_by_block_index(blocks: list[dict]) -> dict[int, int]:
    index_by_block: dict[int, int] = {}
    text_index = 0
    for block_index, block in enumerate(blocks):
        if block["type"] == "text":
            index_by_block[block_index] = text_index
            text_index += 1
    return index_by_block


def _extract_name(line: str, code: str) -> str:
    name = re.sub(r"^[\s:：-]+", "", line.replace(code, "", 1))
    return re.sub(r"\s+", " ", name)


def _find_api_name(lines: list[str], start_index: int, code: str) -> str:
    for line in lines[start_index : start_index + 8]:
        match = API_NAME_PATTERN.search(line)
        if match:
            return match.group(0)
    return _default_api_name(code)


def _direction_parties(code: str) -> tuple[InterfaceDirection, str, str]:
    if code.startswith("EQP-EAP-"):
        return InterfaceDirection.EQP_TO_EAP, "EQP", "EAP"
    return InterfaceDirection.EAP_TO_EQP, "EAP", "EQP"


def _default_api_name(code: str) -> str:
    return code.replace("-", "_")


def _extract_parameters_for_interface(blocks: list[dict], start_block_index: int) -> list[ParsedParameter]:
    parameters: list[ParsedParameter] = []
    current_kind: ParameterKind | None = None

    for block in blocks[start_block_index + 1 :]:
        if block["type"] == "text":
            text = block["text"]
            if INTERFACE_CODE_PATTERN.search(text):
                break
            current_kind = _parameter_kind_from_text(text) or current_kind
            continue
        if block["type"] == "table":
            if current_kind:
                parameters.extend(_parse_parameter_table(block["rows"], current_kind))
            parameters.extend(_parse_sectioned_parameter_table(block["rows"]))

    return parameters


def _parameter_kind_from_text(text: str) -> ParameterKind | None:
    compact = text.replace(" ", "")
    if "请求参数" in compact or "Request" in text:
        return ParameterKind.REQUEST
    if "响应参数" in compact or "返回值" in compact or "应答参数" in compact or "Response" in text:
        return ParameterKind.RESPONSE
    return None


def _parse_parameter_table(rows: list[list[str]], kind: ParameterKind) -> list[ParsedParameter]:
    if len(rows) < 2:
        return []
    headers = [_normalize_header(value) for value in rows[0]]
    field_index = _find_header_index(headers, {"字段名", "字段", "参数名", "field", "name"})
    type_index = _find_header_index(headers, {"类型", "数据类型", "type"})
    required_index = _find_header_index(headers, {"必填", "是否必填", "required"})
    example_index = _find_header_index(headers, {"示例值", "示例", "example"})
    desc_index = _find_header_index(headers, {"说明", "描述", "description", "remark"})
    if field_index is None or type_index is None:
        return []

    parsed: list[ParsedParameter] = []
    for row in rows[1:]:
        field_name = _cell(row, field_index)
        data_type = _cell(row, type_index)
        if not field_name or not data_type:
            continue
        parsed.append(
            ParsedParameter(
                kind=kind,
                field_name=field_name,
                data_type=data_type,
                required=_parse_required(_cell(row, required_index)),
                example_value=_cell(row, example_index),
                description=_cell(row, desc_index) or field_name,
            )
        )
    return parsed


def _parse_sectioned_parameter_table(rows: list[list[str]]) -> list[ParsedParameter]:
    parsed: list[ParsedParameter] = []
    current_kind: ParameterKind | None = None
    field_index: int | None = None
    type_index: int | None = None
    desc_index: int | None = None
    in_content = False

    for row in rows:
        row_text = "".join(row).replace(" ", "")
        if not row_text:
            continue
        if "返回值列表" in row_text or "响应参数列表" in row_text or "应答参数列表" in row_text:
            current_kind = ParameterKind.RESPONSE
            in_content = False
            field_index = type_index = desc_index = None
            continue
        if "请求参数列表" in row_text or row_text == "参数列表" * len(row):
            current_kind = ParameterKind.REQUEST
            in_content = False
            field_index = type_index = desc_index = None
            continue

        headers = [_normalize_header(value) for value in row]
        detected_field_index = _find_header_index(headers, {"字段名", "字段", "参数名", "field", "name"})
        detected_type_index = _find_header_index(headers, {"类型", "数据类型", "type"})
        detected_desc_index = _find_header_index(headers, {"说明", "描述", "description", "remark"})
        if detected_field_index is not None and detected_type_index is not None:
            field_index = detected_field_index
            type_index = detected_type_index
            desc_index = detected_desc_index
            in_content = False
            continue

        if current_kind and _is_content_marker(row):
            in_content = True
            continue

        if not current_kind or not in_content or field_index is None or type_index is None:
            continue

        field_name = _cell(row, field_index)
        data_type = _cell(row, type_index)
        if not field_name or not data_type or field_name.lower() == "content":
            continue
        parsed.append(
            ParsedParameter(
                kind=current_kind,
                field_name=field_name,
                data_type=data_type,
                required=True,
                example_value="",
                description=_cell(row, desc_index) or field_name,
            )
        )

    return parsed


def _is_content_marker(row: list[str]) -> bool:
    values = [value.strip().lower() for value in row if value.strip()]
    return bool(values) and all(value == "content" for value in values)


def _normalize_header(value: str) -> str:
    return re.sub(r"\s+", "", value.strip().lower())


def _find_header_index(headers: list[str], candidates: set[str]) -> int | None:
    normalized_candidates = {_normalize_header(candidate) for candidate in candidates}
    for index, header in enumerate(headers):
        if header in normalized_candidates:
            return index
    return None


def _cell(row: list[str], index: int | None) -> str:
    if index is None or index >= len(row):
        return ""
    return row[index].strip()


def _parse_required(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"否", "n", "no", "false", "0", "非必填"}:
        return False
    return True
