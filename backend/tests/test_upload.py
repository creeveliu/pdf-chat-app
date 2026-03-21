from io import BytesIO
from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import embedding, vector_store
from app.services import pdf_service


client = TestClient(app)


def build_pdf_bytes(text: str, page_count: int = 1) -> bytes:
    document = fitz.open()
    for _ in range(page_count):
        page = document.new_page()
        page.insert_textbox(fitz.Rect(48, 48, 540, 760), text)
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


@pytest.fixture(autouse=True)
def isolate_upload_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pdf_service, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(vector_store, "INDEX_ROOT", tmp_path / "index")


@pytest.fixture(autouse=True)
def fake_embeddings(monkeypatch: pytest.MonkeyPatch) -> None:
    def _generate_embeddings(chunks: list[str]) -> list[list[float]]:
        return [[float(index + 1), float(len(chunk)), 0.5] for index, chunk in enumerate(chunks)]

    monkeypatch.setattr(embedding, "generate_embeddings", _generate_embeddings)


def test_status_endpoints_still_work() -> None:
    root_response = client.get("/")
    health_response = client.get("/health")

    assert root_response.status_code == 200
    assert root_response.json() == {"message": "PDF Chat API is running."}
    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}


def test_upload_pdf_returns_parsed_metadata() -> None:
    pdf_bytes = build_pdf_bytes(("Hello from a PDF upload test. " * 120).strip(), page_count=3)

    response = client.post(
        "/upload",
        files={"file": ("sample.pdf", BytesIO(pdf_bytes), "application/pdf")},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["document_id"]
    assert body["filename"] == "sample.pdf"
    assert body["page_count"] == 3
    assert body["text_length"] > 0
    assert body["chunk_count"] > 1
    assert body["embedding_count"] == body["chunk_count"]
    assert "Hello from a PDF upload test." in body["preview"]
    assert len(body["preview"]) <= 1000

    saved_indexes = list((vector_store.INDEX_ROOT).glob("*/faiss.index"))
    saved_chunks = list((vector_store.INDEX_ROOT).glob("*/chunks.json"))

    assert len(saved_indexes) == 1
    assert len(saved_chunks) == 1


def test_upload_rejects_non_pdf_file() -> None:
    response = client.post(
        "/upload",
        files={"file": ("note.txt", BytesIO(b"not a pdf"), "text/plain")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Only PDF files are supported."}
