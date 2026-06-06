from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.database import get_session
from app.models import ApiInterface, ExportRecord, InterfaceDirection, InterfaceStatus, SpecTemplate

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def home(
    request: Request,
    direction: str = "all",
    status: str = "all",
    session: Session = Depends(get_session),
):
    all_interfaces = session.exec(select(ApiInterface).order_by(ApiInterface.code)).all()
    interfaces = [
        item
        for item in all_interfaces
        if _matches_direction(item, direction) and _matches_status(item, status)
    ]
    recent_exports = session.exec(
        select(ExportRecord).order_by(ExportRecord.created_at.desc()).limit(2)
    ).all()
    template = session.exec(select(SpecTemplate).order_by(SpecTemplate.created_at.desc())).first()
    stats = {
        "total": len(all_interfaces),
        "eqp_to_eap": sum(1 for item in all_interfaces if item.direction == InterfaceDirection.EQP_TO_EAP),
        "eap_to_eqp": sum(1 for item in all_interfaces if item.direction == InterfaceDirection.EAP_TO_EQP),
        "draft": sum(1 for item in all_interfaces if item.status == InterfaceStatus.DRAFT),
    }
    return templates.TemplateResponse(
        request,
        "interfaces_list.html",
        {
            "title": "接口管理工作台",
            "interfaces": interfaces,
            "recent_exports": recent_exports,
            "stats": stats,
            "template": template,
            "active_direction": direction,
            "active_status": status,
        },
    )


def _matches_direction(interface: ApiInterface, direction: str) -> bool:
    if direction == "all":
        return True
    return interface.direction.value == direction


def _matches_status(interface: ApiInterface, status: str) -> bool:
    if status == "all":
        return True
    return interface.status.value == status


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
            "template": None,
        },
    )
