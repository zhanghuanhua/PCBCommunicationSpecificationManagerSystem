from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
from zipfile import BadZipFile

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from starlette.status import HTTP_400_BAD_REQUEST

from app.database import get_session
from app.models import ApiInterface, InterfaceStatus, SpecTemplate
from app.services.spec_parser import ParsedInterface, parse_interface_basics_from_docx

router = APIRouter(prefix="/imports")
templates = Jinja2Templates(directory="app/templates")

TEMPLATE_DIR = Path("data/templates")


@router.post("/spec")
async def upload_spec_template(
    request: Request,
    spec_file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    filename = spec_file.filename or ""
    if not filename.lower().endswith(".docx"):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="只支持上传 .docx Word 文件",
        )

    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    stored_path = TEMPLATE_DIR / f"{uuid4().hex}.docx"
    content = await spec_file.read()
    stored_path.write_bytes(content)

    template = SpecTemplate(
        original_filename=filename,
        stored_path=str(stored_path),
        file_size=len(content),
    )
    session.add(template)
    session.commit()
    session.refresh(template)
    import_result = _save_parsed_interfaces(stored_path, session)

    return templates.TemplateResponse(
        request,
        "import_spec.html",
        {
            "title": "导入原规格书",
            "template": template,
            "message": "导入成功",
            "import_result": import_result,
        },
    )


def _save_parsed_interfaces(docx_path: Path, session: Session) -> dict:
    try:
        parsed = parse_interface_basics_from_docx(docx_path)
    except (BadZipFile, ValueError):
        parsed = []
    created: list[ParsedInterface] = []
    updated: list[ParsedInterface] = []

    for item in parsed:
        exists = session.exec(select(ApiInterface).where(ApiInterface.code == item.code)).first()
        if exists:
            exists.name = item.name
            exists.direction = item.direction
            exists.api_name = item.api_name
            exists.caller = item.caller
            exists.provider = item.provider
            exists.version = "4.0"
            exists.status = InterfaceStatus.DRAFT
            exists.updated_at = datetime.now(UTC)
            session.add(exists)
            updated.append(item)
            continue
        interface = ApiInterface(
            code=item.code,
            name=item.name,
            direction=item.direction,
            api_name=item.api_name,
            caller=item.caller,
            provider=item.provider,
            version="4.0",
            status=InterfaceStatus.DRAFT,
        )
        session.add(interface)
        created.append(item)

    session.commit()
    return {
        "parsed_total": len(parsed),
        "created_total": len(created),
        "updated_total": len(updated),
        "eqp_to_eap_total": sum(1 for item in parsed if item.code.startswith("EQP-EAP-")),
        "eap_to_eqp_total": sum(1 for item in parsed if item.code.startswith("EAP-EQP-")),
        "created": created,
        "updated": updated,
    }
