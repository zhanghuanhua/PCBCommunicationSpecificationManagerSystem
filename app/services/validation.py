from app.models import ApiInterface, ApiParameter, InterfaceDirection


def validate_interface(interface: ApiInterface, parameters: list[ApiParameter]) -> list[str]:
    errors: list[str] = []

    if interface.direction == InterfaceDirection.EQP_TO_EAP:
        if not interface.code.startswith("EQP-EAP-"):
            errors.append("EQP -> EAP 的接口编号必须以 EQP-EAP- 开头。")
        if interface.caller != "EQP" or interface.provider != "EAP":
            errors.append("EQP -> EAP 的调用方必须为 EQP，提供方必须为 EAP。")

    if interface.direction == InterfaceDirection.EAP_TO_EQP:
        if not interface.code.startswith("EAP-EQP-"):
            errors.append("EAP -> EQP 的接口编号必须以 EAP-EQP- 开头。")
        if interface.caller != "EAP" or interface.provider != "EQP":
            errors.append("EAP -> EQP 的调用方必须为 EAP，提供方必须为 EQP。")

    if not interface.name.strip():
        errors.append("接口名称不能为空。")
    if not interface.api_name.strip():
        errors.append("API 名称不能为空。")

    seen_by_parent: set[tuple[int | None, str]] = set()
    for parameter in parameters:
        field_name = parameter.field_name.strip()

        if not field_name:
            errors.append("参数字段名不能为空。")
        if not parameter.data_type.strip():
            errors.append("参数类型不能为空。")
        if not parameter.description.strip():
            errors.append("参数描述不能为空。")

        key = (parameter.parent_id, field_name)
        if field_name and key in seen_by_parent:
            errors.append(f"同一层级下字段名重复：{field_name}")
        seen_by_parent.add(key)

    return errors
