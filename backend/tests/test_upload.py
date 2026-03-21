from io import BytesIO
from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import pdf_service


client = TestClient(app)


def build_pdf_bytes(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


@pytest.fixture(autouse=True)
def isolate_upload_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pdf_service, "UPLOAD_DIR", tmp_path / "uploads")


def test_status_endpoints_still_work() -> None:
    root_response = client.get("/")
    health_response = client.get("/health")

    assert root_response.status_code == 200
    assert root_response.json() == {"message": "PDF Chat API is running."}
    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}


def test_upload_pdf_returns_parsed_metadata() -> None:
    pdf_bytes = build_pdf_bytes("Hello from a PDF upload test.")

    response = client.post(
        "/upload",
        files={"file": ("sample.pdf", BytesIO(pdf_bytes), "application/pdf")},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["filename"] == "sample.pdf"
    assert body["page_count"] == 1
    assert body["text_length"] > 0
    assert "Hello from a PDF upload test." in body["preview"]
    assert len(body["preview"]) <= 1000


def test_upload_rejects_non_pdf_file() -> None:
    response = client.post(
        "/upload",
        files={"file": ("note.txt", BytesIO(b"not a pdf"), "text/plain")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Only PDF files are supported."}
