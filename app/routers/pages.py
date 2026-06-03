from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.database import get_session
from app.models import ApiInterface, ExportRecord, InterfaceDirection, InterfaceStatus

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def home(request: Request, session: Session = Depends(get_session)):
    interfaces = session.exec(select(ApiInterface).order_by(ApiInterface.code)).all()
    recent_exports = session.exec(
        select(ExportRecord).order_by(ExportRecord.created_at.desc()).limit(2)
    ).all()
    stats = {
        "total": len(interfaces),
        "eqp_to_eap": sum(1 for item in interfaces if item.direction == InterfaceDirection.EQP_TO_EAP),
        "eap_to_eqp": sum(1 for item in interfaces if item.direction == InterfaceDirection.EAP_TO_EQP),
        "draft": sum(1 for item in interfaces if item.status == InterfaceStatus.DRAFT),
    }
    return templates.TemplateResponse(
        request,
        "interfaces_list.html",
        {
            "title": "接口管理工作台",
            "interfaces": interfaces,
            "recent_exports": recent_exports,
            "stats": stats,
        },
    )


@router.get("/interfaces/new")
def new_interface(request: Request):
    return templates.TemplateResponse(
        request,
        "interface_form.html",
        {
            "title": "新增接口",
            "directions": InterfaceDirection,
        },
    )


@router.get("/imports/spec")
def import_spec(request: Request):
    return templates.TemplateResponse(
        request,
        "import_spec.html",
        {
            "title": "导入原规格书",
        },
    )
