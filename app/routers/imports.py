from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from starlette.status import HTTP_400_BAD_REQUEST

from app.database import get_session
from app.models import SpecTemplate

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

    return templates.TemplateResponse(
        request,
        "import_spec.html",
        {
            "title": "导入原规格书",
            "template": template,
            "message": "导入成功",
        },
    )
