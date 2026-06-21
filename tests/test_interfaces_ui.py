from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select

from app.database import get_session
from app.main import app
from app.models import ApiInterface, ApiParameter, InterfaceDirection, InterfaceStatus, ParameterKind, SpecVersion


def _client_with_interface(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        spec_version = SpecVersion(version="4.0")
        session.add(spec_version)
        session.commit()
        session.refresh(spec_version)
        interface = ApiInterface(
            spec_version_id=spec_version.id,
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
        spec_version_id = spec_version.id

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    return TestClient(app), interface_id


def _client_with_parameter(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        spec_version = SpecVersion(version="4.0")
        session.add(spec_version)
        session.commit()
        session.refresh(spec_version)
        interface = ApiInterface(
            spec_version_id=spec_version.id,
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


def _client_with_parameter_and_log(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        spec_version = SpecVersion(version="4.0")
        session.add(spec_version)
        session.commit()
        session.refresh(spec_version)
        interface = ApiInterface(
            spec_version_id=spec_version.id,
            code="EQP-EAP-101",
            name="设备状态上报",
            direction=InterfaceDirection.EQP_TO_EAP,
            api_name="EQP_StatusReport",
            caller="EQP",
            provider="EAP",
            status=InterfaceStatus.DRAFT,
            request_log_example='{"Content":{"LotId":"L001"}}',
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
    assert "规格书版本管理" in response.text
    assert "导入原规格书" in response.text


def test_home_page_stays_empty_after_all_versions_are_deleted(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        spec_version = SpecVersion(version="4.0", original_filename="原规格书.docx")
        session.add(spec_version)
        session.commit()
        session.refresh(spec_version)
        spec_version_id = spec_version.id

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        client = TestClient(app)
        response = client.post(f"/specs/{spec_version_id}/delete", follow_redirects=True)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "暂无规格书版本" in response.text
    assert "Version 4.0" not in response.text
    assert "进入管理" not in response.text


def test_home_page_orders_versions_newest_first_and_places_version_in_stats(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        for version in ["4.0", "4.2", "4.1"]:
            session.add(SpecVersion(version=version, name="超毅项目Web API通讯规格书"))
        session.commit()

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        client = TestClient(app)
        response = client.get("/")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    text = response.text
    assert text.index("超毅项目Web API通讯规格书 v4.2") < text.index("超毅项目Web API通讯规格书 v4.1")
    assert text.index("超毅项目Web API通讯规格书 v4.1") < text.index("超毅项目Web API通讯规格书 v4.0")
    assert "<span>版本</span>" in text
    assert "<strong>v4.2</strong>" in text
    assert "Version 4.2" not in text


def test_spec_workspace_shows_interface_workspace_actions(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        spec_version = SpecVersion(version="4.0")
        session.add(spec_version)
        session.commit()
        session.refresh(spec_version)
        spec_version_id = spec_version.id

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        client = TestClient(app)
        response = client.get(f"/specs/{spec_version_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "导入原规格书" in response.text
    assert "导出规格书" in response.text
    assert "接口总数" in response.text
    assert "快捷操作" in response.text
    assert "最近导出记录" in response.text


def test_home_page_uses_vertical_workspace_layout():
    client = TestClient(app)

    home_response = client.get("/")
    assert home_response.status_code == 200
    import re

    match = re.search(r'href="/specs/(\d+)"', home_response.text)
    assert match
    response = client.get(f"/specs/{match.group(1)}")

    assert response.status_code == 200
    assert 'class="quick-actions-panel"' in response.text
    assert "interface-list-panel" in response.text
    assert 'class="interface-table-scroll"' in response.text
    assert 'data-resizable-table' in response.text
    assert 'data-column-resizer' in response.text
    assert "workspace-grid" not in response.text


def test_home_page_filter_buttons_are_links():
    client = TestClient(app)

    home_response = client.get("/")
    import re

    match = re.search(r'href="/specs/(\d+)"', home_response.text)
    assert match
    spec_id = match.group(1)
    response = client.get(f"/specs/{spec_id}")

    assert response.status_code == 200
    assert f'href="/specs/{spec_id}?direction=all"' in response.text
    assert f'href="/specs/{spec_id}?direction=EQP_TO_EAP"' in response.text
    assert f'href="/specs/{spec_id}?direction=EAP_TO_EQP"' in response.text
    assert f'href="/specs/{spec_id}?status=DRAFT"' in response.text


def test_home_page_filters_interfaces_by_direction(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        spec_version = SpecVersion(version="4.0")
        session.add(spec_version)
        session.commit()
        session.refresh(spec_version)
        session.add(
            ApiInterface(
                spec_version_id=spec_version.id,
                code="EQP-EAP-001",
                name="设备上报",
                direction=InterfaceDirection.EQP_TO_EAP,
                api_name="EQP_Report",
                caller="EQP",
                provider="EAP",
                status=InterfaceStatus.DRAFT,
            )
        )
        session.add(
            ApiInterface(
                spec_version_id=spec_version.id,
                code="EAP-EQP-001",
                name="EAP下发",
                direction=InterfaceDirection.EAP_TO_EQP,
                api_name="EAP_Command",
                caller="EAP",
                provider="EQP",
                status=InterfaceStatus.DRAFT,
            )
        )
        session.commit()
        spec_version_id = spec_version.id

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        client = TestClient(app)
        response = client.get(f"/specs/{spec_version_id}?direction=EQP_TO_EAP")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "设备上报" in response.text
    assert "EAP下发" not in response.text


def test_home_page_direction_filter_uses_code_prefix_when_saved_direction_conflicts(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        spec_version = SpecVersion(version="4.0")
        session.add(spec_version)
        session.commit()
        session.refresh(spec_version)
        session.add(
            ApiInterface(
                spec_version_id=spec_version.id,
                code="EAP-EQP-0038",
                name="编号为EAP下发",
                direction=InterfaceDirection.EQP_TO_EAP,
                api_name="EQP_BadDirection",
                caller="EQP",
                provider="EAP",
                status=InterfaceStatus.PUBLISHED,
            )
        )
        session.add(
            ApiInterface(
                spec_version_id=spec_version.id,
                code="EQP-EAP-001",
                name="设备上报",
                direction=InterfaceDirection.EQP_TO_EAP,
                api_name="EQP_Report",
                caller="EQP",
                provider="EAP",
                status=InterfaceStatus.PUBLISHED,
            )
        )
        session.commit()
        spec_version_id = spec_version.id

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        client = TestClient(app)
        response = client.get(f"/specs/{spec_version_id}?direction=EQP_TO_EAP")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "设备上报" in response.text
    assert "编号为EAP下发" not in response.text


def test_home_page_shows_normal_status_for_published_interfaces(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        spec_version = SpecVersion(version="4.0")
        session.add(spec_version)
        session.commit()
        session.refresh(spec_version)
        session.add(
            ApiInterface(
                spec_version_id=spec_version.id,
                code="EQP-EAP-001",
                name="设备上报",
                direction=InterfaceDirection.EQP_TO_EAP,
                api_name="EQP_Report",
                caller="EQP",
                provider="EAP",
                status=InterfaceStatus.PUBLISHED,
            )
        )
        session.commit()
        spec_version_id = spec_version.id

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        client = TestClient(app)
        response = client.get(f"/specs/{spec_version_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "正常" in response.text
    assert "status-draft" not in response.text


def test_delete_interface_from_home_page_removes_interface(tmp_path):
    client, interface_id = _client_with_interface(tmp_path)
    try:
        response = client.post(f"/interfaces/{interface_id}/delete", follow_redirects=True)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "EQP-EAP-101" not in response.text


def test_new_interface_page_shows_create_form():
    client = TestClient(app)

    response = client.get("/interfaces/new")

    assert response.status_code == 200
    assert "新增接口" in response.text
    assert "接口方向" in response.text
    assert "EQP -> EAP" in response.text
    assert "EAP -> EQP" in response.text
    assert "请求参数" in response.text
    assert "响应参数" in response.text
    assert 'name="request_field_name"' in response.text
    assert 'name="response_field_name"' in response.text
    assert "new-interface-form" in response.text
    assert "batch-parameter-table" in response.text
    assert "字段说明" in response.text
    assert "auto-grow-textarea" in response.text
    assert "请求参数自定义节点" in response.text
    assert "响应参数自定义节点" in response.text
    assert 'name="request_row_key"' in response.text
    assert 'name="request_node_parent_key"' in response.text
    assert "request-parameter-row-template" in response.text
    assert "response-parameter-row-template" in response.text
    assert "新增一行" in response.text
    assert '<option value="int">int</option>' in response.text
    assert '<option value="float">float</option>' in response.text
    assert '<option value="double">double</option>' in response.text
    assert '<option value="Int">Int</option>' not in response.text


def test_create_interface_can_save_parameters_from_new_page(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        spec_version = SpecVersion(version="4.0")
        session.add(spec_version)
        session.commit()
        session.refresh(spec_version)
        spec_version_id = spec_version.id

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        client = TestClient(app)
        response = client.post(
            "/interfaces",
                data={
                    "spec_version_id": str(spec_version_id),
                    "direction": "EAP_TO_EQP",
                "code": "EAP-EQP-040",
                "name": "其他打码数据上报",
                "api_name": "EAP_OtherCodeData",
                "requirement": "新增需求",
                "scenario": "新增场景",
                "service_description": "新增服务",
                "version": "4.0",
                "request_field_name": ["MaData"],
                "request_data_type_choice": ["string"],
                "request_custom_data_type": [""],
                "request_example_value": ["D001"],
                "request_description": ["打码数据"],
                "request_required": ["0"],
                "request_is_array": ["0"],
                "response_field_name": ["Result"],
                "response_data_type_choice": ["bool"],
                "response_custom_data_type": [""],
                "response_example_value": ["true"],
                "response_description": ["执行结果"],
                "response_required": ["0"],
                "response_is_array": ["0"],
            },
            follow_redirects=True,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert f"/interfaces/" in str(response.url)
    assert "MaData" in response.text
    assert "Result" in response.text
    with Session(engine) as session:
        interface = session.exec(select(ApiInterface).where(ApiInterface.code == "EAP-EQP-040")).one()
        parameters = session.exec(
            select(ApiParameter).where(ApiParameter.interface_id == interface.id).order_by(ApiParameter.kind)
        ).all()
    assert interface.direction == InterfaceDirection.EAP_TO_EQP
    assert {parameter.field_name for parameter in parameters} == {"MaData", "Result"}


def test_create_interface_can_save_multiple_parameters_from_new_page(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        spec_version = SpecVersion(version="4.2")
        session.add(spec_version)
        session.commit()
        session.refresh(spec_version)
        spec_version_id = spec_version.id

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        client = TestClient(app)
        response = client.post(
            "/interfaces",
            data={
                "spec_version_id": str(spec_version_id),
                "direction": "EQP_TO_EAP",
                "code": "EQP-EAP-110",
                "name": "批量参数接口",
                "api_name": "EQP_BatchParameterReport",
                "version": "4.2",
                "request_field_name": ["LotId", "PanelId", ""],
                "request_data_type_choice": ["string", "CUSTOM", "string"],
                "request_custom_data_type": ["", "List<Panel>", ""],
                "request_example_value": ["L001", "P001", ""],
                "request_description": ["批次号", "板号列表", ""],
                "response_field_name": ["Result", "Message"],
                "response_data_type_choice": ["bool", "string"],
                "response_custom_data_type": ["", ""],
                "response_example_value": ["true", "OK"],
                "response_description": ["执行结果", "返回信息"],
            },
            follow_redirects=True,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    with Session(engine) as session:
        interface = session.exec(select(ApiInterface).where(ApiInterface.code == "EQP-EAP-110")).one()
        parameters = session.exec(
            select(ApiParameter)
            .where(ApiParameter.interface_id == interface.id)
            .order_by(ApiParameter.kind, ApiParameter.sort_order)
        ).all()
    assert [parameter.field_name for parameter in parameters] == ["LotId", "PanelId", "Result", "Message"]
    assert [parameter.sort_order for parameter in parameters] == [1, 2, 1, 2]
    assert parameters[1].data_type == "List<Panel>"


def test_create_interface_can_save_custom_node_parameters_from_new_page(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        spec_version = SpecVersion(version="4.2")
        session.add(spec_version)
        session.commit()
        session.refresh(spec_version)
        spec_version_id = spec_version.id

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        client = TestClient(app)
        response = client.post(
            "/interfaces",
            data={
                "spec_version_id": str(spec_version_id),
                "direction": "EAP_TO_EQP",
                "code": "EAP-EQP-120",
                "name": "自定义节点接口",
                "api_name": "EAP_CustomNodeReport",
                "version": "4.2",
                "request_row_key": ["req-a", "req-stack"],
                "request_field_name": ["EqpId", "StackUpDetail"],
                "request_data_type_choice": ["string", "CUSTOM"],
                "request_custom_data_type": ["", "List<StackUp>"],
                "request_example_value": ["EQ01", ""],
                "request_description": ["设备ID", "叠构"],
                "request_node_parent_key": ["req-stack", "req-stack"],
                "request_node_field_name": ["LayerNo", "Material"],
                "request_node_data_type_choice": ["Int", "string"],
                "request_node_custom_data_type": ["", ""],
                "request_node_example_value": ["1", "Core"],
                "request_node_description": ["层序号", "材料名称"],
                "response_row_key": ["rsp-result", "rsp-error"],
                "response_field_name": ["Result", "ErrorList"],
                "response_data_type_choice": ["bool", "CUSTOM"],
                "response_custom_data_type": ["", "List<ErrorInfo>"],
                "response_example_value": ["true", ""],
                "response_description": ["执行结果", "错误明细"],
                "response_node_parent_key": ["rsp-error"],
                "response_node_field_name": ["Code"],
                "response_node_data_type_choice": ["string"],
                "response_node_custom_data_type": [""],
                "response_node_example_value": ["E001"],
                "response_node_description": ["错误代码"],
            },
            follow_redirects=True,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "StackUpDetail" in response.text
    assert "LayerNo" in response.text
    assert "ErrorList" in response.text
    assert "E001" in response.text
    with Session(engine) as session:
        interface = session.exec(select(ApiInterface).where(ApiInterface.code == "EAP-EQP-120")).one()
        parameters = session.exec(
            select(ApiParameter)
            .where(ApiParameter.interface_id == interface.id)
            .order_by(ApiParameter.kind, ApiParameter.parent_id, ApiParameter.sort_order)
        ).all()
        stack_parent = next(parameter for parameter in parameters if parameter.field_name == "StackUpDetail")
        stack_children = [parameter for parameter in parameters if parameter.parent_id == stack_parent.id]
        error_parent = next(parameter for parameter in parameters if parameter.field_name == "ErrorList")
        error_children = [parameter for parameter in parameters if parameter.parent_id == error_parent.id]
        session.refresh(interface)
        request_log = interface.request_log_example
        response_log = interface.response_log_example
    assert [parameter.field_name for parameter in stack_children] == ["LayerNo", "Material"]
    assert stack_children[0].data_type == "int"
    assert [parameter.field_name for parameter in error_children] == ["Code"]
    assert '"StackUpDetail": [' in request_log
    assert '"LayerNo": 1' in request_log
    assert '"Material": "Core"' in request_log
    assert '"ErrorList": [' in response_log
    assert '"Code": "E001"' in response_log


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
    assert "一次添加多条请求或响应字段" in response.text
    assert "batch-parameter-row-template" in response.text
    assert "保存接口信息" in response.text
    assert 'name="code"' in response.text
    assert 'name="api_name"' in response.text
    assert "点击添加请求或响应字段" not in response.text
    assert "interface-detail-layout" in response.text
    assert "interface-detail-container" in response.text
    assert "parameter-add-panel" in response.text
    assert "parameter-add-cta" in response.text
    assert "parameter-table-scroll" in response.text
    assert '<option value="string">string</option>' in response.text
    assert '<option value="CUSTOM">自定义</option>' in response.text
    assert 'name="batch_custom_data_type"' in response.text
    assert "例如 List&lt;Data&gt;" in response.text
    assert 'name="batch_example_value"' in response.text
    assert "parameter-grid" not in response.text
    assert "detail-side-panel" not in response.text
    assert "示例值</th>" not in response.text


def test_update_interface_info_from_detail_page(tmp_path):
    client, interface_id = _client_with_interface(tmp_path)
    try:
        response = client.post(
            f"/interfaces/{interface_id}",
            data={
                "code": "EAP-EQP-038",
                "name": "其他打码数据上报",
                "api_name": "EAP_OtherCodeData",
                "caller": "EAP",
                "provider": "EQP",
                "version": "4.3",
                "requirement": "更新后的需求说明",
                "scenario": "更新后的使用场景",
                "service_description": "更新后的接口服务描述",
            },
            follow_redirects=True,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "EAP-EQP-038" in response.text
    assert "其他打码数据上报" in response.text
    assert "EAP_OtherCodeData" in response.text
    assert "4.3" in response.text
    assert "更新后的需求说明" in response.text
    assert "EQP_StatusReport" not in response.text


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


def test_add_multiple_parameters_to_interface_detail_page(tmp_path):
    client, interface_id = _client_with_interface(tmp_path)
    try:
        response = client.post(
            f"/interfaces/{interface_id}/parameters/batch",
            data={
                "batch_kind": "REQUEST",
                "batch_field_name": ["LotId", "PanelId"],
                "batch_data_type_choice": ["string", "string"],
                "batch_custom_data_type": ["", ""],
                "batch_example_value": ["L001", "P001"],
                "batch_description": ["批次号", "板号"],
            },
            follow_redirects=True,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "LotId" in response.text
    assert "PanelId" in response.text


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


def test_custom_parameter_type_requires_custom_value(tmp_path):
    client, interface_id = _client_with_interface(tmp_path)
    try:
        response = client.post(
            f"/interfaces/{interface_id}/parameters",
            data={
                "kind": "REQUEST",
                "field_name": "DataList",
                "data_type_choice": "CUSTOM",
                "custom_data_type": "",
                "required": "true",
                "description": "资料列表",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert "选择自定义时必须填写自定义类型" in response.text


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


def test_delete_parameter_updates_log_example(tmp_path):
    client, interface_id, parameter_id = _client_with_parameter_and_log(tmp_path)
    try:
        response = client.post(
            f"/interfaces/{interface_id}/parameters/{parameter_id}/delete",
            follow_redirects=True,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "L001" not in response.text
    assert "Content" in response.text


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
