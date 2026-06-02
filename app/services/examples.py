from typing import Any

from app.models import ApiInterface, ApiParameter, ParameterKind


DEFAULT_DATETIME = "2024/11/27 15:00:00"
DEFAULT_REQUEST_ID = "20250107121135343"


def build_request_example(interface: ApiInterface, parameters: list[ApiParameter]) -> dict[str, Any]:
    return {
        "From": interface.caller,
        "Message": interface.api_name,
        "DateTime": DEFAULT_DATETIME,
        "Content": _build_content(parameters, ParameterKind.REQUEST),
        "RequestId": DEFAULT_REQUEST_ID,
    }


def build_response_example(interface: ApiInterface, parameters: list[ApiParameter]) -> dict[str, Any]:
    return {
        "Code": "0000",
        "Success": True,
        "Msg": "",
        "DateTime": DEFAULT_DATETIME,
        "Content": _build_content(parameters, ParameterKind.RESPONSE),
        "RequestId": DEFAULT_REQUEST_ID,
    }


def _build_content(parameters: list[ApiParameter], kind: ParameterKind) -> dict[str, Any]:
    content: dict[str, Any] = {}
    for parameter in sorted(parameters, key=lambda item: item.sort_order):
        if parameter.kind != kind or parameter.parent_id is not None:
            continue
        content[parameter.field_name] = _coerce_example_value(parameter)
    return content


def _coerce_example_value(parameter: ApiParameter) -> Any:
    data_type = parameter.data_type.lower()
    value = parameter.example_value
    scalar = _coerce_scalar(value, data_type)
    if parameter.is_array:
        return [scalar]
    return scalar


def _coerce_scalar(value: str, data_type: str) -> Any:
    if data_type in {"int", "integer"}:
        return int(value) if value else 0
    if data_type in {"float", "decimal", "double"}:
        return float(value) if value else 0.0
    if data_type in {"bool", "boolean"}:
        if value.lower() == "false":
            return False
        return True
    if data_type in {"object", "jsonobject"}:
        return {}
    return value
