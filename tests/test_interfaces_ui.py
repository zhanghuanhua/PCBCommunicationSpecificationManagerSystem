from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_session
from app.main import app
from app.models import ApiInterface, ApiParameter, InterfaceDirection, InterfaceStatus, ParameterKind


def _client_with_interface(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        interface = ApiInterface(
            code="EQP-EAP-101",
            name="设备状态上报",
            direction=InterfaceDirection.EQP_TO_EAP,
            api_name="EQP_StatusReport",
            caller="EQP",
            provider="EAP",
            status=InterfaceStatus.DRAFT,
        )
        session.add(interface)
        session.commit()
        session.refresh(interface)
        interface_id = interface.id

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    return TestClient(app), interface_id


def _client_with_parameter(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        interface = ApiInterface(
            code="EQP-EAP-101",
            name="设备状态上报",
            direction=InterfaceDirection.EQP_TO_EAP,
            api_name="EQP_StatusReport",
            caller="EQP",
            provider="EAP",
            status=InterfaceStatus.DRAFT,
        )
        session.add(interface)
        session.commit()
        session.refresh(interface)
        parameter = ApiParameter(
            interface_id=interface.id or 0,
            kind=ParameterKind.REQUEST,
            sort_order=1,
            field_name="LotId",
            data_type="string",
            required=True,
            example_value="L001",
            description="批次号",
        )
        session.add(parameter)
        session.commit()
        session.refresh(parameter)
        interface_id = interface.id
        parameter_id = parameter.id

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    return TestClient(app), interface_id, parameter_id


def test_home_page_shows_interface_workspace_actions():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "接口管理工作台" in response.text
    assert "结构化维护 EAP-EQP 接口" in response.text
    assert "新增接口" in response.text
    assert "导入原规格书" in response.text
    assert "导出中心" in response.text
    assert "接口总数" in response.text
    assert "快捷操作" in response.text
    assert "最近导出记录" in response.text


def test_home_page_uses_vertical_workspace_layout():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert 'class="quick-actions-panel"' in response.text
    assert "interface-list-panel" in response.text
    assert 'class="interface-table-scroll"' in response.text
    assert "workspace-grid" not in response.text


def test_new_interface_page_shows_create_form():
    client = TestClient(app)

    response = client.get("/interfaces/new")

    assert response.status_code == 200
    assert "新增接口" in response.text
    assert "接口方向" in response.text
    assert "EQP -> EAP" in response.text
    assert "EAP -> EQP" in response.text


def test_import_spec_page_shows_template_import_placeholder():
    client = TestClient(app)

    response = client.get("/imports/spec")

    assert response.status_code == 200
    assert "导入原规格书" in response.text
    assert "选择 Word 文件" in response.text
    assert "作为模板导入" in response.text
    assert "解析接口草稿" in response.text


def test_interface_detail_page_shows_parameter_sections(tmp_path):
    client, interface_id = _client_with_interface(tmp_path)
    try:
        response = client.get(f"/interfaces/{interface_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "设备状态上报" in response.text
    assert "请求参数" in response.text
    assert "响应参数" in response.text
    assert "日志范例" in response.text
    assert "请求日志范例" in response.text
    assert "响应日志范例" in response.text
    assert "新增参数" in response.text
    assert "添加参数" in response.text
    assert "点击添加请求或响应字段" not in response.text
    assert "interface-detail-layout" in response.text
    assert "interface-detail-container" in response.text
    assert "parameter-add-panel" in response.text
    assert "parameter-add-cta" in response.text
    assert "parameter-table-scroll" in response.text
    assert '<option value="string">string</option>' in response.text
    assert '<option value="CUSTOM">自定义</option>' in response.text
    assert 'name="custom_data_type"' in response.text
    assert 'name="example_value"' in response.text
    assert "parameter-grid" not in response.text
    assert "detail-side-panel" not in response.text
    assert "示例值</th>" not in response.text


def test_add_parameter_to_interface_detail_page(tmp_path):
    client, interface_id = _client_with_interface(tmp_path)
    try:
        response = client.post(
            f"/interfaces/{interface_id}/parameters",
            data={
                "kind": "REQUEST",
                "field_name": "LotId",
                "data_type": "string",
                "required": "true",
                "is_array": "",
                "example_value": "L001",
                "description": "批次号",
            },
            follow_redirects=True,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "LotId" in response.text
    assert "批次号" in response.text
    assert "请求参数" in response.text
    assert "L001" in response.text


def test_update_parameter_on_interface_detail_page(tmp_path):
    client, interface_id, parameter_id = _client_with_parameter(tmp_path)
    try:
        response = client.post(
            f"/interfaces/{interface_id}/parameters/{parameter_id}",
            data={
                "kind": "RESPONSE",
                "field_name": "ResultCode",
                "data_type": "int",
                "required": "",
                "is_array": "true",
                "description": "处理结果码",
            },
            follow_redirects=True,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "ResultCode" in response.text
    assert "处理结果码" in response.text
    assert 'value="LotId"' not in response.text


def test_update_parameter_keeps_valid_kind_value(tmp_path):
    client, interface_id, parameter_id = _client_with_parameter(tmp_path)
    try:
        response = client.post(
            f"/interfaces/{interface_id}/parameters/{parameter_id}",
            data={
                "kind": "REQUEST",
                "field_name": "LotId",
                "data_type_choice": "string",
                "required": "true",
                "description": "批次号",
            },
            follow_redirects=True,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "ParameterKind.REQUEST" not in response.text


def test_add_request_parameter_updates_request_log_example(tmp_path):
    client, interface_id = _client_with_interface(tmp_path)
    try:
        response = client.post(
            f"/interfaces/{interface_id}/parameters",
            data={
                "kind": "REQUEST",
                "field_name": "IP",
                "data_type_choice": "string",
                "required": "true",
                "example_value": "127.0.0.1",
                "description": "IP地址",
            },
            follow_redirects=True,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "127.0.0.1" in response.text
    assert "IP" in response.text


def test_add_custom_list_parameter_updates_log_example(tmp_path):
    client, interface_id = _client_with_interface(tmp_path)
    try:
        response = client.post(
            f"/interfaces/{interface_id}/parameters",
            data={
                "kind": "RESPONSE",
                "field_name": "DataList",
                "data_type_choice": "CUSTOM",
                "custom_data_type": "List<Data>",
                "required": "true",
                "is_array": "true",
                "example_value": "D001",
                "description": "资料列表",
            },
            follow_redirects=True,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "List&lt;Data&gt;" in response.text
    assert "DataList" in response.text


def test_delete_parameter_from_interface_detail_page(tmp_path):
    client, interface_id, parameter_id = _client_with_parameter(tmp_path)
    try:
        response = client.post(
            f"/interfaces/{interface_id}/parameters/{parameter_id}/delete",
            follow_redirects=True,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert 'value="LotId"' not in response.text
    assert "批次号" not in response.text


def test_save_interface_log_examples(tmp_path):
    client, interface_id = _client_with_interface(tmp_path)
    try:
        response = client.post(
            f"/interfaces/{interface_id}/log-examples",
            data={
                "request_log_example": "REST:POST /api/EQP_StatusReport\n{\"From\":\"EQP\"}",
                "response_log_example": "{\"Code\":\"0000\",\"Success\":true}",
            },
            follow_redirects=True,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "REST:POST /api/EQP_StatusReport" in response.text
    assert "Code" in response.text
    assert "0000" in response.text
