from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


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
