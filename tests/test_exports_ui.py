from pathlib import Path

from fastapi.testclient import TestClient
from docx import Document
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_session
from app.main import app
from app.models import ApiInterface, ApiParameter, InterfaceDirection, ParameterKind, SpecTemplate


def test_export_center_page_shows_format_and_watermark_options():
    client = TestClient(app)

    response = client.get("/exports")

    assert response.status_code == 200
    assert "导出中心" in response.text
    assert "Word + PDF" in response.text
    assert "添加水印" in response.text


def test_export_center_creates_markdown_file():
    client = TestClient(app)
    output = Path("exports/EAP-EQP接口通讯规格书.md")
    if output.exists():
        output.unlink()

    response = client.post(
        "/exports",
        data={
            "export_format": "markdown",
            "watermark_text": "厂商查看",
        },
    )

    assert response.status_code == 200
    assert "导出结果" in response.text
    assert output.exists()
    assert "珠海超毅 EAP-EQP API 接口通讯规格书" in output.read_text(encoding="utf-8")


def test_export_center_uses_imported_template_for_word(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)
    template_path = tmp_path / "template.docx"
    template = Document()
    template.add_heading("原规格书标题", level=0)
    template.add_paragraph("原规格书已有章节")
    template.save(template_path)

    with Session(engine) as session:
        session.add(
            SpecTemplate(
                original_filename="原规格书.docx",
                stored_path=str(template_path),
                file_size=template_path.stat().st_size,
            )
        )
        session.commit()

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    output = Path("exports/EAP-EQP接口通讯规格书.docx")
    if output.exists():
        output.unlink()

    try:
        client = TestClient(app)
        response = client.post(
            "/exports",
            data={
                "export_format": "word",
                "watermark_text": "厂商查看",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert output.exists()
    exported = Document(output)
    body_text = "\n".join(paragraph.text for paragraph in exported.paragraphs)
    assert "原规格书标题" in body_text
    assert "原规格书已有章节" in body_text
    assert "系统新增接口内容" in body_text


def test_export_center_word_includes_saved_parameters(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        interface = ApiInterface(
            code="EQP-EAP-201",
            name="参数导出测试",
            direction=InterfaceDirection.EQP_TO_EAP,
            api_name="EQP_ParamExport",
            caller="EQP",
            provider="EAP",
        )
        session.add(interface)
        session.commit()
        session.refresh(interface)
        session.add(
            ApiParameter(
                interface_id=interface.id,
                kind=ParameterKind.REQUEST,
                sort_order=1,
                field_name="LotId",
                data_type="string",
                example_value="L001",
                description="批次号",
            )
        )
        session.commit()

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    output = Path("exports/EAP-EQP接口通讯规格书.docx")
    if output.exists():
        output.unlink()

    try:
        client = TestClient(app)
        response = client.post("/exports", data={"export_format": "word"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    exported = Document(output)
    body_text = "\n".join(paragraph.text for paragraph in exported.paragraphs)
    assert '"LotId": "L001"' in body_text
