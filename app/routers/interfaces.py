import json
from datetime import UTC, datetime

from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, delete, select

from app.database import get_session
from app.models import ApiInterface, ApiParameter, InterfaceDirection, InterfaceStatus, ParameterKind, SpecVersion
from app.services.examples import build_request_example, build_response_example


router = APIRouter(prefix="/interfaces")
templates = Jinja2Templates(directory="app/templates")
PARAMETER_TYPE_OPTIONS = ["string", "list", "bool", "DateTime", "Int", "object"]


@router.post("")
def create_interface(
    spec_version_id: int | None = Form(None),
    code: str = Form(...),
    name: str = Form(...),
    direction: InterfaceDirection = Form(...),
    api_name: str = Form(...),
    requirement: str = Form(""),
    scenario: str = Form(""),
    service_description: str = Form(""),
    version: str = Form("4.0"),
    module: str = Form(""),
    request_field_name: Annotated[list[str], Form()] = [],
    request_data_type_choice: Annotated[list[str], Form()] = [],
    request_custom_data_type: Annotated[list[str], Form()] = [],
    request_example_value: Annotated[list[str], Form()] = [],
    request_description: Annotated[list[str], Form()] = [],
    request_required: Annotated[list[str], Form()] = [],
    request_is_array: Annotated[list[str], Form()] = [],
    response_field_name: Annotated[list[str], Form()] = [],
    response_data_type_choice: Annotated[list[str], Form()] = [],
    response_custom_data_type: Annotated[list[str], Form()] = [],
    response_example_value: Annotated[list[str], Form()] = [],
    response_description: Annotated[list[str], Form()] = [],
    response_required: Annotated[list[str], Form()] = [],
    response_is_array: Annotated[list[str], Form()] = [],
    session: Session = Depends(get_session),
):
    spec_version = session.get(SpecVersion, spec_version_id) if spec_version_id else _latest_spec_version(session)
    if not spec_version:
        raise HTTPException(status_code=400, detail="暂无规格书版本，请先导入原规格书")
    spec_version_id = spec_version.id or 0
    caller = "EQP" if direction == InterfaceDirection.EQP_TO_EAP else "EAP"
    provider = "EAP" if direction == InterfaceDirection.EQP_TO_EAP else "EQP"
    interface = ApiInterface(
        spec_version_id=spec_version_id,
        code=code,
        name=name,
        direction=direction,
        api_name=api_name,
        caller=caller,
        provider=provider,
        requirement=requirement,
        scenario=scenario,
        service_description=service_description,
        version=version or spec_version.version,
        module=module,
        status=InterfaceStatus.DRAFT,
        updated_at=datetime.now(UTC),
    )
    session.add(interface)
    session.flush()
    _add_parameters_from_new_form(
        interface.id or 0,
        ParameterKind.REQUEST,
        request_field_name,
        request_data_type_choice,
        request_custom_data_type,
        request_example_value,
        request_description,
        request_required,
        request_is_array,
        session,
    )
    _add_parameters_from_new_form(
        interface.id or 0,
        ParameterKind.RESPONSE,
        response_field_name,
        response_data_type_choice,
        response_custom_data_type,
        response_example_value,
        response_description,
        response_required,
        response_is_array,
        session,
    )
    session.commit()
    _sync_log_example(interface.id or 0, ParameterKind.REQUEST, session)
    _sync_log_example(interface.id or 0, ParameterKind.RESPONSE, session)
    return RedirectResponse(f"/interfaces/{interface.id}", status_code=303)


def _latest_spec_version(session: Session) -> SpecVersion | None:
    return session.exec(select(SpecVersion).order_by(SpecVersion.created_at.desc())).first()


@router.post("/{interface_id}/delete")
def delete_interface(
    interface_id: int,
    session: Session = Depends(get_session),
):
    interface = session.get(ApiInterface, interface_id)
    if not interface:
        raise HTTPException(status_code=404, detail="接口不存在")
    session.exec(delete(ApiParameter).where(ApiParameter.interface_id == interface_id))
    spec_version_id = interface.spec_version_id
    session.delete(interface)
    session.commit()
    return RedirectResponse(f"/specs/{spec_version_id}" if spec_version_id else "/", status_code=303)


@router.get("/{interface_id}")
def interface_detail(
    interface_id: int,
    request: Request,
    session: Session = Depends(get_session),
):
    interface = session.get(ApiInterface, interface_id)
    if not interface:
        raise HTTPException(status_code=404, detail="接口不存在")
    spec_version = session.get(SpecVersion, interface.spec_version_id) if interface.spec_version_id else None
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
            "spec_version": spec_version,
            "request_parameters": [item for item in parameters if item.kind == ParameterKind.REQUEST],
            "response_parameters": [item for item in parameters if item.kind == ParameterKind.RESPONSE],
            "kinds": ParameterKind,
            "parameter_type_options": PARAMETER_TYPE_OPTIONS,
        },
    )


@router.post("/{interface_id}")
def update_interface(
    interface_id: int,
    code: str = Form(...),
    name: str = Form(...),
    api_name: str = Form(...),
    caller: str = Form(...),
    provider: str = Form(...),
    version: str = Form(""),
    requirement: str = Form(""),
    scenario: str = Form(""),
    service_description: str = Form(""),
    session: Session = Depends(get_session),
):
    interface = session.get(ApiInterface, interface_id)
    if not interface:
        raise HTTPException(status_code=404, detail="接口不存在")
    interface.code = code.strip()
    interface.name = name.strip()
    interface.api_name = api_name.strip()
    interface.caller = caller.strip()
    interface.provider = provider.strip()
    interface.version = version.strip() or interface.version
    interface.requirement = requirement
    interface.scenario = scenario
    interface.service_description = service_description
    interface.direction = _direction_from_parties(interface.caller, interface.provider, interface.direction)
    interface.updated_at = datetime.now(UTC)
    interface.status = InterfaceStatus.DRAFT
    session.add(interface)
    session.commit()
    _sync_log_example(interface_id, ParameterKind.REQUEST, session)
    _sync_log_example(interface_id, ParameterKind.RESPONSE, session)
    return RedirectResponse(f"/interfaces/{interface_id}", status_code=303)


@router.post("/{interface_id}/parameters")
def add_parameter(
    interface_id: int,
    kind: ParameterKind = Form(...),
    field_name: str = Form(...),
    data_type: str = Form(""),
    data_type_choice: str = Form(""),
    custom_data_type: str = Form(""),
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
        data_type=_resolve_data_type(data_type, data_type_choice, custom_data_type),
        required=required,
        is_array=is_array,
        example_value=example_value,
        description=description,
    )
    session.add(parameter)
    interface.updated_at = datetime.now(UTC)
    interface.status = InterfaceStatus.DRAFT
    session.add(interface)
    session.commit()
    session.refresh(parameter)
    _sync_log_example(interface_id, kind, session)
    return RedirectResponse(f"/interfaces/{interface_id}#parameter-{parameter.id}", status_code=303)


@router.post("/{interface_id}/parameters/batch")
def add_parameters_batch(
    interface_id: int,
    batch_kind: ParameterKind = Form(...),
    batch_field_name: Annotated[list[str], Form()] = [],
    batch_data_type_choice: Annotated[list[str], Form()] = [],
    batch_custom_data_type: Annotated[list[str], Form()] = [],
    batch_example_value: Annotated[list[str], Form()] = [],
    batch_description: Annotated[list[str], Form()] = [],
    session: Session = Depends(get_session),
):
    interface = session.get(ApiInterface, interface_id)
    if not interface:
        raise HTTPException(status_code=404, detail="接口不存在")
    existing = session.exec(
        select(ApiParameter).where(
            ApiParameter.interface_id == interface_id,
            ApiParameter.kind == batch_kind,
        )
    ).all()
    added = _add_parameters_from_new_form(
        interface_id,
        batch_kind,
        batch_field_name,
        batch_data_type_choice,
        batch_custom_data_type,
        batch_example_value,
        batch_description,
        [],
        [],
        session,
        start_order=len(existing) + 1,
    )
    if added:
        interface.updated_at = datetime.now(UTC)
        interface.status = InterfaceStatus.DRAFT
        session.add(interface)
        session.commit()
        _sync_log_example(interface_id, batch_kind, session)
    return RedirectResponse(f"/interfaces/{interface_id}", status_code=303)


@router.post("/{interface_id}/parameters/{parameter_id}")
def update_parameter(
    interface_id: int,
    parameter_id: int,
    kind: ParameterKind = Form(...),
    field_name: str = Form(...),
    data_type: str = Form(""),
    data_type_choice: str = Form(""),
    custom_data_type: str = Form(""),
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
    parameter.data_type = _resolve_data_type(data_type, data_type_choice, custom_data_type)
    parameter.required = required
    parameter.is_array = is_array
    if example_value:
        parameter.example_value = example_value
    parameter.description = description
    session.add(parameter)
    interface.updated_at = datetime.now(UTC)
    interface.status = InterfaceStatus.DRAFT
    session.add(interface)
    session.commit()
    _sync_log_example(interface_id, kind, session)
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
    kind = parameter.kind
    session.delete(parameter)
    interface.updated_at = datetime.now(UTC)
    interface.status = InterfaceStatus.DRAFT
    session.add(interface)
    session.commit()
    _sync_log_example(interface_id, kind, session)
    return RedirectResponse(f"/interfaces/{interface_id}", status_code=303)


def _resolve_data_type(data_type: str, data_type_choice: str, custom_data_type: str) -> str:
    if data_type_choice == "CUSTOM":
        custom_type = custom_data_type.strip()
        if not custom_type:
            raise HTTPException(status_code=400, detail="选择自定义时必须填写自定义类型")
        return custom_type
    return (data_type_choice or data_type).strip()


def _direction_from_parties(
    caller: str,
    provider: str,
    fallback: InterfaceDirection,
) -> InterfaceDirection:
    caller = caller.upper()
    provider = provider.upper()
    if caller == "EQP" and provider == "EAP":
        return InterfaceDirection.EQP_TO_EAP
    if caller == "EAP" and provider == "EQP":
        return InterfaceDirection.EAP_TO_EQP
    return fallback


def _add_parameters_from_new_form(
    interface_id: int,
    kind: ParameterKind,
    field_names: list[str],
    data_type_choices: list[str],
    custom_data_types: list[str],
    example_values: list[str],
    descriptions: list[str],
    required_flags: list[str],
    array_flags: list[str],
    session: Session,
    start_order: int = 1,
) -> int:
    added = 0
    for index, field_name in enumerate(field_names):
        field_name = field_name.strip()
        if not field_name:
            continue
        session.add(
            ApiParameter(
                interface_id=interface_id,
                kind=kind,
                sort_order=start_order + added,
                field_name=field_name,
                data_type=_resolve_data_type(
                    "",
                    _list_value(data_type_choices, index, "string"),
                    _list_value(custom_data_types, index),
                ),
                required=_list_value(required_flags, index, "1") == "1",
                is_array=_list_value(array_flags, index, "0") == "1",
                example_value=_list_value(example_values, index),
                description=_list_value(descriptions, index, field_name),
            )
        )
        added += 1
    return added


def _list_value(values: list[str], index: int, default: str = "") -> str:
    if index >= len(values):
        return default
    return values[index].strip()


def _sync_log_example(interface_id: int, kind: ParameterKind, session: Session) -> None:
    interface = session.get(ApiInterface, interface_id)
    if not interface:
        return
    parameters = session.exec(
        select(ApiParameter)
        .where(ApiParameter.interface_id == interface_id)
        .order_by(ApiParameter.sort_order, ApiParameter.id)
    ).all()
    if kind == ParameterKind.REQUEST:
        interface.request_log_example = _format_request_log(interface, parameters)
    else:
        interface.response_log_example = _format_json_log(build_response_example(interface, parameters))
    interface.updated_at = datetime.now(UTC)
    session.add(interface)
    session.commit()


def _format_request_log(interface: ApiInterface, parameters: list[ApiParameter]) -> str:
    return f"REST:POST http://IP:Port/api/{interface.api_name}\n{_format_json_log(build_request_example(interface, parameters))}"


def _format_json_log(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=4)


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
    interface.status = InterfaceStatus.DRAFT
    session.add(interface)
    session.commit()
    return RedirectResponse(f"/interfaces/{interface_id}", status_code=303)
