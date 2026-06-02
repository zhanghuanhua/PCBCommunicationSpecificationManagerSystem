from pathlib import Path

from app.services.pdf_export import export_basic_pdf


def test_basic_pdf_export_creates_file(tmp_path: Path):
    output = tmp_path / "spec.pdf"

    export_basic_pdf(output, "珠海超毅 EAP-EQP API 接口通讯规格书", watermark_text="厂商查看")

    assert output.exists()
    assert output.stat().st_size > 0
