from datetime import datetime
from typing import Any

from app.models import ApiInterface, ApiParameter, ParameterKind


def current_datetime_text(now: datetime | None = None) -> str:
    return (now or datetime.now()).strftime("%Y/%m/%d %H:%M:%S")


def current_request_id(now: datetime | None = None) -> str:
    return (now or datetime.now()).strftime("%Y%m%d%H%M%S%f")[:17]


def build_request_example(
    interface: ApiInterface,
    parameters: list[ApiParameter],
    now: datetime | None = None,
) -> dict[str, Any]:
    generated_at = now or datetime.now()
    return {
        "From": interface.caller,
        "Message": interface.api_name,
        "DateTime": current_datetime_text(generated_at),
        "Content": _build_content(parameters, ParameterKind.REQUEST),
        "RequestId": current_request_id(generated_at),
    }


def build_response_example(
    interface: ApiInterface,
    parameters: list[ApiParameter],
    now: datetime | None = None,
) -> dict[str, Any]:
    generated_at = now or datetime.now()
    return {
        "Code": "0000",
        "Success": True,
        "Msg": "",
        "DateTime": current_datetime_text(generated_at),
        "Content": _build_content(parameters, ParameterKind.RESPONSE),
        "RequestId": current_request_id(generated_at),
    }


def _build_content(parameters: list[ApiParameter], kind: ParameterKind) -> dict[str, Any]:
    content: dict[str, Any] = {}
    children_by_parent = _children_by_parent(parameters, kind)
    for parameter in sorted(parameters, key=lambda item: item.sort_order):
        if parameter.kind != kind or parameter.parent_id is not None:
            continue
        if _is_group_parameter(parameter):
            continue
        content[parameter.field_name] = _coerce_example_value(parameter, children_by_parent)
    return content


def _children_by_parent(parameters: list[ApiParameter], kind: ParameterKind) -> dict[int, list[ApiParameter]]:
    children: dict[int, list[ApiParameter]] = {}
    for parameter in parameters:
        if parameter.kind != kind or parameter.parent_id is None or _is_group_parameter(parameter):
            continue
        children.setdefault(parameter.parent_id, []).append(parameter)
    for items in children.values():
        items.sort(key=lambda item: item.sort_order)
    return children


def _coerce_example_value(parameter: ApiParameter, children_by_parent: dict[int, list[ApiParameter]]) -> Any:
    children = children_by_parent.get(parameter.id or 0, [])
    data_type = parameter.data_type.lower()
    value = parameter.example_value
    if children:
        nested = {
            child.field_name: _coerce_example_value(child, children_by_parent)
            for child in children
            if not _is_group_parameter(child)
        }
        if parameter.is_array or _is_list_type(data_type):
            return [nested]
        return nested
    scalar = _coerce_scalar(value, data_type)
    if parameter.is_array:
        return [scalar]
    return scalar


def _coerce_scalar(value: str, data_type: str) -> Any:
    if data_type in {"int", "integer"}:
        try:
            return int(value) if value else 0
        except ValueError:
            return 0
    if data_type in {"float", "decimal", "double"}:
        try:
            return float(value) if value else 0.0
        except ValueError:
            return 0.0
    if data_type in {"bool", "boolean"}:
        if value.lower() == "false":
            return False
        return True
    if data_type in {"object", "jsonobject"}:
        return {}
    return value


def _is_list_type(data_type: str) -> bool:
    return data_type.startswith("list<") or data_type.startswith("array<")


def _is_group_parameter(parameter: ApiParameter) -> bool:
    return not parameter.data_type.strip()
