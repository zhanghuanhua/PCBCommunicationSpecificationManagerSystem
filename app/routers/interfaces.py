from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.database import get_session
from app.models import ApiInterface, ApiParameter, InterfaceDirection, InterfaceStatus, ParameterKind


router = APIRouter(prefix="/interfaces")
templates = Jinja2Templates(directory="app/templates")


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


@router.get("/{interface_id}")
def interface_detail(
    interface_id: int,
    request: Request,
    session: Session = Depends(get_session),
):
    interface = session.get(ApiInterface, interface_id)
    if not interface:
        raise HTTPException(status_code=404, detail="接口不存在")
    parameters = session.exec(
        select(ApiParameter)
        .where(ApiParameter.interface_id == interface_id)
        .order_by(ApiParameter.kind, ApiParameter.sort_order, ApiParameter.id)
    ).all()
    return templates.TemplateResponse(
        request,
        "interface_detail.html",
        {
            "title": interface.name,
            "interface": interface,
            "request_parameters": [item for item in parameters if item.kind == ParameterKind.REQUEST],
            "response_parameters": [item for item in parameters if item.kind == ParameterKind.RESPONSE],
            "kinds": ParameterKind,
        },
    )


@router.post("/{interface_id}/parameters")
def add_parameter(
    interface_id: int,
    kind: ParameterKind = Form(...),
    field_name: str = Form(...),
    data_type: str = Form(...),
    required: bool = Form(False),
    is_array: bool = Form(False),
    example_value: str = Form(""),
    description: str = Form(...),
    session: Session = Depends(get_session),
):
    interface = session.get(ApiInterface, interface_id)
    if not interface:
        raise HTTPException(status_code=404, detail="接口不存在")
    count = session.exec(
        select(ApiParameter).where(
            ApiParameter.interface_id == interface_id,
            ApiParameter.kind == kind,
        )
    ).all()
    parameter = ApiParameter(
        interface_id=interface_id,
        kind=kind,
        sort_order=len(count) + 1,
        field_name=field_name,
        data_type=data_type,
        required=required,
        is_array=is_array,
        example_value=example_value,
        description=description,
    )
    session.add(parameter)
    interface.updated_at = datetime.now(UTC)
    session.add(interface)
    session.commit()
    session.refresh(parameter)
    return RedirectResponse(f"/interfaces/{interface_id}#parameter-{parameter.id}", status_code=303)


@router.post("/{interface_id}/parameters/{parameter_id}")
def update_parameter(
    interface_id: int,
    parameter_id: int,
    kind: ParameterKind = Form(...),
    field_name: str = Form(...),
    data_type: str = Form(...),
    required: bool = Form(False),
    is_array: bool = Form(False),
    example_value: str = Form(""),
    description: str = Form(...),
    session: Session = Depends(get_session),
):
    interface = session.get(ApiInterface, interface_id)
    parameter = session.get(ApiParameter, parameter_id)
    if not interface or not parameter or parameter.interface_id != interface_id:
        raise HTTPException(status_code=404, detail="接口参数不存在")
    parameter.kind = kind
    parameter.field_name = field_name
    parameter.data_type = data_type
    parameter.required = required
    parameter.is_array = is_array
    parameter.example_value = example_value
    parameter.description = description
    session.add(parameter)
    interface.updated_at = datetime.now(UTC)
    session.add(interface)
    session.commit()
    return RedirectResponse(f"/interfaces/{interface_id}#parameter-{parameter_id}", status_code=303)


@router.post("/{interface_id}/parameters/{parameter_id}/delete")
def delete_parameter(
    interface_id: int,
    parameter_id: int,
    session: Session = Depends(get_session),
):
    interface = session.get(ApiInterface, interface_id)
    parameter = session.get(ApiParameter, parameter_id)
    if not interface or not parameter or parameter.interface_id != interface_id:
        raise HTTPException(status_code=404, detail="接口参数不存在")
    session.delete(parameter)
    interface.updated_at = datetime.now(UTC)
    session.add(interface)
    session.commit()
    return RedirectResponse(f"/interfaces/{interface_id}", status_code=303)


@router.post("/{interface_id}/log-examples")
def save_log_examples(
    interface_id: int,
    request_log_example: str = Form(""),
    response_log_example: str = Form(""),
    session: Session = Depends(get_session),
):
    interface = session.get(ApiInterface, interface_id)
    if not interface:
        raise HTTPException(status_code=404, detail="接口不存在")
    interface.request_log_example = request_log_example
    interface.response_log_example = response_log_example
    interface.updated_at = datetime.now(UTC)
    session.add(interface)
    session.commit()
    return RedirectResponse(f"/interfaces/{interface_id}", status_code=303)
