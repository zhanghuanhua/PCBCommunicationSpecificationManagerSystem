from app.models import ApiInterface, ApiParameter, InterfaceDirection, ParameterKind
from app.services.validation import validate_interface


def test_eqp_to_eap_requires_matching_caller_provider():
    interface = ApiInterface(
        code="EQP-EAP-037",
        name="测试接口",
        direction=InterfaceDirection.EQP_TO_EAP,
        api_name="EQP_Test",
        caller="EAP",
        provider="EQP",
    )

    errors = validate_interface(interface, [])

    assert "EQP -> EAP 的调用方必须为 EQP，提供方必须为 EAP。" in errors


def test_eap_to_eqp_requires_matching_code_prefix():
    interface = ApiInterface(
        code="EQP-EAP-012",
        name="测试接口",
        direction=InterfaceDirection.EAP_TO_EQP,
        api_name="EAP_Test",
        caller="EAP",
        provider="EQP",
    )

    errors = validate_interface(interface, [])

    assert "EAP -> EQP 的接口编号必须以 EAP-EQP- 开头。" in errors


def test_parameter_requires_name_type_and_description():
    interface = ApiInterface(
        code="EQP-EAP-037",
        name="测试接口",
        direction=InterfaceDirection.EQP_TO_EAP,
        api_name="EQP_Test",
        caller="EQP",
        provider="EAP",
    )
    parameter = ApiParameter(
        interface_id=1,
        kind=ParameterKind.REQUEST,
        sort_order=1,
        field_name="",
        data_type="",
        description="",
    )

    errors = validate_interface(interface, [parameter])

    assert "参数字段名不能为空。" in errors
    assert "参数类型不能为空。" in errors
    assert "参数描述不能为空。" in errors


def test_duplicate_field_name_in_same_parent_is_rejected():
    interface = ApiInterface(
        code="EQP-EAP-037",
        name="测试接口",
        direction=InterfaceDirection.EQP_TO_EAP,
        api_name="EQP_Test",
        caller="EQP",
        provider="EAP",
    )
    parameters = [
        ApiParameter(
            interface_id=1,
            kind=ParameterKind.REQUEST,
            sort_order=1,
            field_name="EqpId",
            data_type="string",
            description="设备 ID",
        ),
        ApiParameter(
            interface_id=1,
            kind=ParameterKind.REQUEST,
            sort_order=2,
            field_name="EqpId",
            data_type="string",
            description="设备 ID",
        ),
    ]

    errors = validate_interface(interface, parameters)

    assert "同一层级下字段名重复：EqpId" in errors
