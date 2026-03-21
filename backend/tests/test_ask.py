from io import BytesIO
from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import embedding, llm, pdf_service, vector_store


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
def isolate_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pdf_service, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(vector_store, "INDEX_ROOT", tmp_path / "index")


@pytest.fixture(autouse=True)
def fake_embeddings(monkeypatch: pytest.MonkeyPatch) -> None:
    def _generate_embeddings(chunks: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for chunk in chunks:
            score = 1.0 if "PlayStation" in chunk else 0.0
            embeddings.append([score, float(len(chunk)), 0.5])
        return embeddings

    monkeypatch.setattr(embedding, "generate_embeddings", _generate_embeddings)


def test_ask_rejects_empty_question() -> None:
    response = client.post("/ask", json={"question": "   "})

    assert response.status_code == 400
    assert response.json() == {"detail": "Question cannot be empty."}


def test_ask_returns_error_when_no_index_exists() -> None:
    response = client.post("/ask", json={"question": "这份 PDF 讲了什么？"})

    assert response.status_code == 404
    assert response.json() == {"detail": "No vector index available. Upload a PDF first."}


def test_ask_returns_answer_and_contexts(monkeypatch: pytest.MonkeyPatch) -> None:
    pdf_bytes = build_pdf_bytes(("PlayStation 5 Pro quick start guide. " * 80).strip(), page_count=2)

    upload_response = client.post(
        "/upload",
        files={"file": ("guide.pdf", BytesIO(pdf_bytes), "application/pdf")},
    )

    assert upload_response.status_code == 200

    def _generate_answer(question: str, contexts: list[dict[str, object]]) -> str:
        assert question == "这份 PDF 主要讲了什么？"
        assert len(contexts) == 2
        assert "PlayStation 5 Pro" in contexts[0]["text"]
        return "这是一份 PlayStation 5 Pro 的快速开始指南。"

    monkeypatch.setattr(llm, "generate_answer", _generate_answer)

    response = client.post("/ask", json={"question": "这份 PDF 主要讲了什么？", "top_k": 2})

    assert response.status_code == 200

    body = response.json()
    assert body["question"] == "这份 PDF 主要讲了什么？"
    assert body["answer"] == "这是一份 PlayStation 5 Pro 的快速开始指南。"
    assert body["top_k"] == 2
    assert len(body["contexts"]) == 2
    assert body["contexts"][0]["filename"] == "guide.pdf"


def test_ask_skips_incompatible_legacy_index(monkeypatch: pytest.MonkeyPatch) -> None:
    vector_store.persist_document_index(
        document_id="legacy-index",
        filename="legacy.pdf",
        chunks=["legacy chunk"],
        embeddings=[[1.0, 2.0, 3.0, 4.0]],
    )

    pdf_bytes = build_pdf_bytes(("PlayStation 5 Pro quick start guide. " * 80).strip(), page_count=2)
    upload_response = client.post(
        "/upload",
        files={"file": ("guide.pdf", BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_response.status_code == 200

    monkeypatch.setattr(llm, "generate_answer", lambda question, contexts: "基于 PDF，这是一份快速开始指南。")

    response = client.post("/ask", json={"question": "这份 PDF 主要讲了什么？", "top_k": 1})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "基于 PDF，这是一份快速开始指南。"
    assert body["contexts"][0]["filename"] == "guide.pdf"
