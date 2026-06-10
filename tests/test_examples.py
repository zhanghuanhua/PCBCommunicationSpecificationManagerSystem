from app.models import ApiInterface, ApiParameter, InterfaceDirection, ParameterKind
from app.services.examples import build_request_example, build_response_example


def test_build_request_example_for_eqp_to_eap():
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
            example_value="EQ01",
            description="设备 ID",
        )
    ]

    result = build_request_example(interface, parameters)

    assert result["From"] == "EQP"
    assert result["Message"] == "EQP_Test"
    assert result["DateTime"] == "2024/11/27 15:00:00"
    assert result["Content"]["EqpId"] == "EQ01"
    assert result["RequestId"] == "20250107121135343"


def test_build_response_example_has_public_fields():
    interface = ApiInterface(
        code="EAP-EQP-012",
        name="测试接口",
        direction=InterfaceDirection.EAP_TO_EQP,
        api_name="EAP_Test",
        caller="EAP",
        provider="EQP",
    )

    result = build_response_example(interface, [])

    assert result["Code"] == "0000"
    assert result["Success"] is True
    assert result["Msg"] == ""
    assert result["Content"] == {}
    assert result["RequestId"] == "20250107121135343"


def test_build_example_converts_scalar_types_and_arrays():
    interface = ApiInterface(
        code="EQP-EAP-038",
        name="测试接口",
        direction=InterfaceDirection.EQP_TO_EAP,
        api_name="EQP_TestTypes",
        caller="EQP",
        provider="EAP",
    )
    parameters = [
        ApiParameter(
            interface_id=1,
            kind=ParameterKind.REQUEST,
            sort_order=1,
            field_name="Count",
            data_type="int",
            example_value="3",
            description="数量",
        ),
        ApiParameter(
            interface_id=1,
            kind=ParameterKind.REQUEST,
            sort_order=2,
            field_name="Success",
            data_type="bool",
            example_value="false",
            description="是否成功",
        ),
        ApiParameter(
            interface_id=1,
            kind=ParameterKind.REQUEST,
            sort_order=3,
            field_name="Items",
            data_type="string",
            is_array=True,
            example_value="A001",
            description="项目列表",
        ),
    ]

    result = build_request_example(interface, parameters)

    assert result["Content"]["Count"] == 3
    assert result["Content"]["Success"] is False
    assert result["Content"]["Items"] == ["A001"]


def test_build_request_example_uses_nested_parameter_children():
    interface = ApiInterface(
        code="EQP-EAP-005",
        name="设备任务进展信息上报",
        direction=InterfaceDirection.EQP_TO_EAP,
        api_name="EQP_EquipmentJobDataProcessReport",
        caller="EQP",
        provider="EAP",
    )
    parameters = [
        ApiParameter(
            id=1,
            interface_id=1,
            kind=ParameterKind.REQUEST,
            sort_order=1,
            field_name="Ext",
            data_type="ExtInfo",
            description="扩展信息",
        ),
        ApiParameter(
            id=2,
            interface_id=1,
            parent_id=1,
            kind=ParameterKind.REQUEST,
            sort_order=2,
            field_name="NgPanelList",
            data_type="List<NgPanel>",
            description="高压失败的Panel列表",
        ),
        ApiParameter(
            id=3,
            interface_id=1,
            parent_id=2,
            kind=ParameterKind.REQUEST,
            sort_order=3,
            field_name="PanelId",
            data_type="string",
            example_value="Panel001",
            description="产品序列码",
        ),
    ]

    result = build_request_example(interface, parameters)

    assert result["Content"] == {"Ext": {"NgPanelList": [{"PanelId": "Panel001"}]}}
