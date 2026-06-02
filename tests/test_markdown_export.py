from app.models import ApiInterface, InterfaceDirection
from app.services.markdown_export import render_markdown_document


def test_markdown_export_contains_interface_sections():
    interface = ApiInterface(
        id=1,
        code="EQP-EAP-037",
        name="测试接口",
        direction=InterfaceDirection.EQP_TO_EAP,
        api_name="EQP_Test",
        caller="EQP",
        provider="EAP",
        requirement="测试需求",
        scenario="测试场景",
        service_description="测试服务",
    )

    content = render_markdown_document(
        [interface],
        {1: {"From": "EQP", "Message": "EQP_Test", "Content": {}}},
        {1: {"Code": "0000", "Success": True, "Content": {}}},
    )

    assert "# 珠海超毅 EAP-EQP API 接口通讯规格书" in content
    assert "## EQP -> EAP 接口" in content
    assert "### EQP-EAP-037 测试接口" in content
    assert "EQP_Test" in content
    assert "```json" in content
