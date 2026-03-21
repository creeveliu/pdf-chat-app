from io import BytesIO
from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import chunking, embedding, llm, pdf_service, vector_store


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
    document_id = upload_response.json()["document_id"]

    def _generate_answer(question: str, contexts: list[dict[str, object]]) -> str:
        assert question == "这份 PDF 主要讲了什么？"
        assert len(contexts) == 2
        assert "PlayStation 5 Pro" in contexts[0]["text"]
        assert all(context["document_id"] == document_id for context in contexts)
        assert contexts[0]["page_number"] >= 1
        assert contexts[0]["page_numbers"] == [contexts[0]["page_number"]]
        return "这是一份 PlayStation 5 Pro 的快速开始指南。"

    monkeypatch.setattr(llm, "generate_answer", _generate_answer)

    response = client.post(
        "/ask",
        json={"question": "这份 PDF 主要讲了什么？", "top_k": 2, "document_id": document_id},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["question"] == "这份 PDF 主要讲了什么？"
    assert body["answer"] == "这是一份 PlayStation 5 Pro 的快速开始指南。"
    assert body["top_k"] == 2
    assert len(body["contexts"]) == 2
    assert body["contexts"][0]["filename"] == "guide.pdf"
    assert all(context["document_id"] == document_id for context in body["contexts"])
    assert body["contexts"][0]["page_number"] >= 1
    assert body["contexts"][0]["page_numbers"] == [body["contexts"][0]["page_number"]]
    assert body["citations"]
    assert body["citations"][0]["page_numbers"]
    assert body["citations"][0]["chunk_index"] == body["contexts"][0]["chunk_index"]


def test_ask_skips_incompatible_legacy_index(monkeypatch: pytest.MonkeyPatch) -> None:
    vector_store.persist_document_index(
        document_id="legacy-index",
        filename="legacy.pdf",
        file_sha256="legacy-hash",
        chunks=[
            chunking.ChunkRecord(
                chunk_index=0,
                text="legacy chunk",
                page_number=1,
                page_numbers=[1],
                chunk_hash="legacy-chunk-hash",
            )
        ],
        embeddings=[[1.0, 2.0, 3.0, 4.0]],
    )

    pdf_bytes = build_pdf_bytes(("PlayStation 5 Pro quick start guide. " * 80).strip(), page_count=2)
    upload_response = client.post(
        "/upload",
        files={"file": ("guide.pdf", BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    monkeypatch.setattr(llm, "generate_answer", lambda question, contexts: "基于 PDF，这是一份快速开始指南。")

    response = client.post(
        "/ask",
        json={"question": "这份 PDF 主要讲了什么？", "top_k": 1, "document_id": document_id},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "基于 PDF，这是一份快速开始指南。"
    assert body["contexts"][0]["filename"] == "guide.pdf"
    assert body["contexts"][0]["document_id"] == document_id


def test_ask_requires_document_id_when_multiple_indexes_exist(monkeypatch: pytest.MonkeyPatch) -> None:
    first_pdf = build_pdf_bytes(("PlayStation guide. " * 120).strip(), page_count=1)
    second_pdf = build_pdf_bytes(("Nintendo Switch guide. " * 120).strip(), page_count=1)

    first_response = client.post(
        "/upload",
        files={"file": ("first.pdf", BytesIO(first_pdf), "application/pdf")},
    )
    second_response = client.post(
        "/upload",
        files={"file": ("second.pdf", BytesIO(second_pdf), "application/pdf")},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    monkeypatch.setattr(llm, "generate_answer", lambda question, contexts: "不应该执行到这里。")

    response = client.post("/ask", json={"question": "这份 PDF 主要讲了什么？"})

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Multiple indexed PDFs are available. Specify document_id to ask about a specific file."
    }


def test_ask_deduplicates_contexts_after_duplicate_upload(monkeypatch: pytest.MonkeyPatch) -> None:
    repeated_page = ("PlayStation 5 Pro repeated instructions for setup and power management. " * 18).strip()
    pdf_bytes = build_pdf_bytes(repeated_page, page_count=3)

    first_upload = client.post(
        "/upload",
        files={"file": ("guide.pdf", BytesIO(pdf_bytes), "application/pdf")},
    )
    second_upload = client.post(
        "/upload",
        files={"file": ("guide.pdf", BytesIO(pdf_bytes), "application/pdf")},
    )

    assert first_upload.status_code == 200
    assert second_upload.status_code == 200
    assert second_upload.json()["already_exists"] is True

    document_id = second_upload.json()["document_id"]

    def _generate_answer(question: str, contexts: list[dict[str, object]]) -> str:
        assert question == "这份 PDF 主要讲了什么？"
        texts = [context["text"] for context in contexts]
        assert len(texts) == len(set(texts))
        return "这是一份不包含重复引用片段的回答。"

    monkeypatch.setattr(llm, "generate_answer", _generate_answer)

    response = client.post(
        "/ask",
        json={"question": "这份 PDF 主要讲了什么？", "top_k": 3, "document_id": document_id},
    )

    assert response.status_code == 200
    body = response.json()
    texts = [context["text"] for context in body["contexts"]]
    assert body["answer"] == "这是一份不包含重复引用片段的回答。"
    assert len(texts) == len(set(texts))
