import re
from dataclasses import dataclass
from pathlib import Path

from docx import Document

from app.models import InterfaceDirection


INTERFACE_CODE_PATTERN = re.compile(r"\b(EQP-EAP|EAP-EQP)-\d{3,}\b", re.IGNORECASE)
API_NAME_PATTERN = re.compile(r"\b(EQP|EAP)_[A-Za-z0-9_]+\b")


@dataclass(frozen=True)
class ParsedInterface:
    code: str
    name: str
    direction: InterfaceDirection
    api_name: str
    caller: str
    provider: str


def parse_interface_basics_from_docx(docx_path: Path) -> list[ParsedInterface]:
    document = Document(docx_path)
    lines = _extract_text_lines(document)
    parsed: list[ParsedInterface] = []
    seen_codes: set[str] = set()

    for index, line in enumerate(lines):
        match = INTERFACE_CODE_PATTERN.search(line)
        if not match:
            continue

        code = match.group(0).upper()
        if code in seen_codes:
            continue
        seen_codes.add(code)

        name = _extract_name(line, code)
        api_name = _find_api_name(lines, index, code)
        direction, caller, provider = _direction_parties(code)
        parsed.append(
            ParsedInterface(
                code=code,
                name=name or code,
                direction=direction,
                api_name=api_name or _default_api_name(code),
                caller=caller,
                provider=provider,
            )
        )

    return parsed


def _extract_text_lines(document: Document) -> list[str]:
    lines: list[str] = []
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text:
            lines.append(text)
    for table in document.tables:
        for row in table.rows:
            text = " ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if text:
                lines.append(text)
    return lines


def _extract_name(line: str, code: str) -> str:
    name = line.replace(code, "", 1).strip(" :-：\t")
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
