from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, delete, select

from app.database import get_session
from app.models import (
    ApiInterface,
    ApiParameter,
    ExportRecord,
    InterfaceDirection,
    InterfaceStatus,
    SpecTemplate,
    SpecVersion,
)
from app.routers.interfaces import PARAMETER_TYPE_OPTIONS

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def specs_home(
    request: Request,
    session: Session = Depends(get_session),
):
    spec_versions = session.exec(select(SpecVersion).order_by(SpecVersion.created_at.desc())).all()
    cards = []
    for spec in spec_versions:
        interfaces = session.exec(
            select(ApiInterface).where(ApiInterface.spec_version_id == spec.id)
        ).all()
        cards.append(
            {
                "spec": spec,
                "total": len(interfaces),
                "eqp_to_eap": sum(1 for item in interfaces if _effective_direction(item) == InterfaceDirection.EQP_TO_EAP),
                "eap_to_eqp": sum(1 for item in interfaces if _effective_direction(item) == InterfaceDirection.EAP_TO_EQP),
                "draft": sum(1 for item in interfaces if item.status == InterfaceStatus.DRAFT),
            }
        )
    return templates.TemplateResponse(
        request,
        "spec_versions.html",
        {
            "title": "规格书版本管理",
            "version_cards": cards,
        },
    )


@router.post("/specs/{spec_version_id}/delete")
def delete_spec_version(
    spec_version_id: int,
    session: Session = Depends(get_session),
):
    spec = session.get(SpecVersion, spec_version_id)
    if not spec:
        raise HTTPException(status_code=404, detail="规格书版本不存在")
    interfaces = session.exec(
        select(ApiInterface).where(ApiInterface.spec_version_id == spec_version_id)
    ).all()
    for interface in interfaces:
        session.exec(delete(ApiParameter).where(ApiParameter.interface_id == interface.id))
        session.delete(interface)
    session.delete(spec)
    session.commit()
    return RedirectResponse("/", status_code=303)


@router.get("/specs/{spec_version_id}")
def spec_workspace(
    spec_version_id: int,
    request: Request,
    direction: str = "all",
    status: str = "all",
    session: Session = Depends(get_session),
):
    spec_version = session.get(SpecVersion, spec_version_id)
    if not spec_version:
        raise HTTPException(status_code=404, detail="规格书版本不存在")
    all_interfaces = session.exec(
        select(ApiInterface)
        .where(ApiInterface.spec_version_id == spec_version_id)
        .order_by(ApiInterface.code)
    ).all()
    interfaces = [
        item
        for item in all_interfaces
        if _matches_direction(item, direction) and _matches_status(item, status)
    ]
    recent_exports = session.exec(
        select(ExportRecord).order_by(ExportRecord.created_at.desc()).limit(2)
    ).all()
    template = _template_for_spec(spec_version, session)
    stats = {
        "total": len(all_interfaces),
        "eqp_to_eap": sum(1 for item in all_interfaces if _effective_direction(item) == InterfaceDirection.EQP_TO_EAP),
        "eap_to_eqp": sum(1 for item in all_interfaces if _effective_direction(item) == InterfaceDirection.EAP_TO_EQP),
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
            "spec_version": spec_version,
            "active_direction": direction,
            "active_status": status,
        },
    )


def _matches_direction(interface: ApiInterface, direction: str) -> bool:
    if direction == "all":
        return True
    return _effective_direction(interface).value == direction


def _effective_direction(interface: ApiInterface) -> InterfaceDirection:
    if interface.code.upper().startswith("EQP-EAP-"):
        return InterfaceDirection.EQP_TO_EAP
    if interface.code.upper().startswith("EAP-EQP-"):
        return InterfaceDirection.EAP_TO_EQP
    return interface.direction


def _matches_status(interface: ApiInterface, status: str) -> bool:
    if status == "all":
        return True
    return interface.status.value == status


@router.get("/specs/{spec_version_id}/interfaces/new")
def new_interface(spec_version_id: int, request: Request, session: Session = Depends(get_session)):
    spec_version = session.get(SpecVersion, spec_version_id)
    if not spec_version:
        raise HTTPException(status_code=404, detail="规格书版本不存在")
    return templates.TemplateResponse(
        request,
        "interface_form.html",
        {
            "title": "新增接口",
            "directions": InterfaceDirection,
            "parameter_type_options": PARAMETER_TYPE_OPTIONS,
            "spec_version": spec_version,
        },
    )


@router.get("/interfaces/new")
def legacy_new_interface(request: Request, session: Session = Depends(get_session)):
    spec_version = session.exec(select(SpecVersion).order_by(SpecVersion.created_at.desc())).first()
    if not spec_version:
        return RedirectResponse("/imports/spec", status_code=303)
    return RedirectResponse(f"/specs/{spec_version.id}/interfaces/new", status_code=303)


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


def _template_for_spec(spec_version: SpecVersion, session: Session) -> SpecTemplate | None:
    if spec_version.template_path:
        template = session.exec(
            select(SpecTemplate).where(SpecTemplate.stored_path == spec_version.template_path)
        ).first()
        if template:
            return template
    return session.exec(select(SpecTemplate).order_by(SpecTemplate.created_at.desc())).first()
