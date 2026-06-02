from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from app.database import get_session
from app.models import ApiInterface, InterfaceDirection, InterfaceStatus


router = APIRouter(prefix="/interfaces")


@router.post("")
def create_interface(
    code: str = Form(...),
    name: str = Form(...),
    direction: InterfaceDirection = Form(...),
    api_name: str = Form(...),
    requirement: str = Form(""),
    scenario: str = Form(""),
    service_description: str = Form(""),
    version: str = Form("4.0"),
    module: str = Form(""),
    session: Session = Depends(get_session),
):
    caller = "EQP" if direction == InterfaceDirection.EQP_TO_EAP else "EAP"
    provider = "EAP" if direction == InterfaceDirection.EQP_TO_EAP else "EQP"
    interface = ApiInterface(
        code=code,
        name=name,
        direction=direction,
        api_name=api_name,
        caller=caller,
        provider=provider,
        requirement=requirement,
        scenario=scenario,
        service_description=service_description,
        version=version,
        module=module,
        status=InterfaceStatus.DRAFT,
        updated_at=datetime.now(UTC),
    )
    session.add(interface)
    session.commit()
    return RedirectResponse("/", status_code=303)
