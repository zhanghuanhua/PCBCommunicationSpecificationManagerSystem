from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select

from app.database import get_session
from app.main import app
from app.models import SpecTemplate
from app.routers import imports


@pytest.fixture
def client_with_engine(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)
    monkeypatch.setattr(imports, "TEMPLATE_DIR", tmp_path / "templates")

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        yield TestClient(app), engine
    finally:
        app.dependency_overrides.clear()


def test_upload_docx_spec_template_saves_file_and_metadata(client_with_engine):
    client, engine = client_with_engine

    response = client.post(
        "/imports/spec",
        files={
            "spec_file": (
                "珠海超毅 EAP-EQP API 接口通讯规格书4.0.docx",
                b"fake docx content",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 200
    assert "导入成功" in response.text
    assert "珠海超毅 EAP-EQP API 接口通讯规格书4.0.docx" in response.text

    with Session(engine) as session:
        template = session.exec(select(SpecTemplate).order_by(SpecTemplate.created_at.desc())).first()

    assert template is not None
    assert template.original_filename == "珠海超毅 EAP-EQP API 接口通讯规格书4.0.docx"
    assert Path(template.stored_path).exists()


def test_upload_rejects_non_docx_file(client_with_engine):
    client, _ = client_with_engine

    response = client.post(
        "/imports/spec",
        files={"spec_file": ("readme.txt", b"text", "text/plain")},
    )

    assert response.status_code == 400
    assert "只支持上传 .docx Word 文件" in response.text


def test_home_page_shows_imported_template_status(client_with_engine):
    client, _ = client_with_engine
    client.post(
        "/imports/spec",
        files={
            "spec_file": (
                "原规格书.docx",
                b"docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    response = client.get("/")

    assert response.status_code == 200
    assert "已导入" in response.text
    assert "原规格书.docx" in response.text
