from fastapi.testclient import TestClient

from app.main import app


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
