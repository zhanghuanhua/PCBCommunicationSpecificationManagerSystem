from pathlib import Path

import pytest
from docx import Document
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select

from app.database import get_session
from app.main import app
from app.models import ApiInterface, SpecTemplate
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


def test_upload_docx_parses_interface_basics_and_shows_result(client_with_engine, tmp_path):
    client, engine = client_with_engine
    docx_path = tmp_path / "source.docx"
    document = Document()
    document.add_heading("EQP-EAP-010 设备状态上报", level=2)
    document.add_paragraph("接口名称 EQP_StatusReport")
    document.add_heading("EAP-EQP-011 启动设备", level=2)
    document.add_paragraph("接口名称 EAP_StartMachine")
    document.save(docx_path)

    response = client.post(
        "/imports/spec",
        files={
            "spec_file": (
                "原规格书.docx",
                docx_path.read_bytes(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 200
    assert "本次解析结果" in response.text
    assert "解析接口总数" in response.text
    assert "EQP-EAP-010" in response.text
    assert "EAP-EQP-011" in response.text

    with Session(engine) as session:
        interfaces = session.exec(select(ApiInterface).order_by(ApiInterface.code)).all()

    assert len(interfaces) == 2
    assert interfaces[0].code == "EAP-EQP-011"
    assert interfaces[1].code == "EQP-EAP-010"


def test_upload_docx_skips_existing_interface_codes(client_with_engine, tmp_path):
    client, engine = client_with_engine
    docx_path = tmp_path / "source.docx"
    document = Document()
    document.add_heading("EQP-EAP-010 设备状态上报", level=2)
    document.add_paragraph("接口名称 EQP_StatusReport")
    document.save(docx_path)

    for _ in range(2):
        response = client.post(
            "/imports/spec",
            files={
                "spec_file": (
                    "原规格书.docx",
                    docx_path.read_bytes(),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

    assert response.status_code == 200
    assert "已存在跳过" in response.text

    with Session(engine) as session:
        interfaces = session.exec(select(ApiInterface)).all()

    assert len(interfaces) == 1
