from fastapi.testclient import TestClient

from app.main import app


def test_home_page_shows_interface_workspace_actions():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "接口管理工作台" in response.text
    assert "新增接口" in response.text
    assert "导出中心" in response.text


def test_new_interface_page_shows_create_form():
    client = TestClient(app)

    response = client.get("/interfaces/new")

    assert response.status_code == 200
    assert "新增接口" in response.text
    assert "接口方向" in response.text
    assert "EQP -> EAP" in response.text
    assert "EAP -> EQP" in response.text
