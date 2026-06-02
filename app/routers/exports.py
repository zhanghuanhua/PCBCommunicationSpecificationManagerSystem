from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.database import get_session
from app.models import ApiInterface, ExportRecord
from app.services.examples import build_request_example, build_response_example
from app.services.markdown_export import render_markdown_document
from app.services.pdf_export import export_basic_pdf
from app.services.word_export import export_word_document


router = APIRouter(prefix="/exports")
templates = Jinja2Templates(directory="app/templates")


@router.get("")
def export_center(request: Request):
    return templates.TemplateResponse(
        request,
        "export_center.html",
        {"title": "导出中心"},
    )


@router.post("")
def run_export(
    request: Request,
    export_format: str = Form(...),
    watermark_enabled: bool = Form(False),
    watermark_text: str = Form(""),
    session: Session = Depends(get_session),
):
    interfaces = session.exec(select(ApiInterface).order_by(ApiInterface.code)).all()
    request_examples = {item.id or 0: build_request_example(item, []) for item in interfaces}
    response_examples = {item.id or 0: build_response_example(item, []) for item in interfaces}
    output_files: list[str] = []
    watermark = watermark_text if watermark_enabled else ""
    export_dir = Path("exports")

    if export_format in {"markdown", "all"}:
        markdown_path = export_dir / "EAP-EQP接口通讯规格书.md"
        markdown_path.write_text(
            render_markdown_document(interfaces, request_examples, response_examples),
            encoding="utf-8",
        )
        output_files.append(str(markdown_path))

    if export_format in {"word", "word_pdf", "all"}:
        word_path = export_dir / "EAP-EQP接口通讯规格书.docx"
        export_word_document(word_path, interfaces, request_examples, response_examples, watermark)
        output_files.append(str(word_path))

    if export_format in {"pdf", "word_pdf", "all"}:
        pdf_path = export_dir / "EAP-EQP接口通讯规格书.pdf"
        export_basic_pdf(pdf_path, "珠海超毅 EAP-EQP API 接口通讯规格书", watermark)
        output_files.append(str(pdf_path))

    record = ExportRecord(
        version="4.0",
        scope="all",
        formats=export_format,
        watermark_enabled=watermark_enabled,
        watermark_text=watermark,
        output_path=";".join(output_files),
        result="success",
    )
    session.add(record)
    session.commit()

    return templates.TemplateResponse(
        request,
        "export_result.html",
        {"title": "导出结果", "output_files": output_files},
    )
