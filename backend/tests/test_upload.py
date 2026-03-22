from datetime import datetime, timedelta, timezone
from io import BytesIO
import json
from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import document_registry, embedding, vector_store
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
    def _generate_embeddings(chunks: list[str], progress_callback=None) -> list[list[float]]:
        if progress_callback is not None:
            progress_callback(
                {
                    "current_batch": 1,
                    "total_batches": 1,
                    "completed_chunks": len(chunks),
                    "total_chunks": len(chunks),
                }
            )
        return [[float(index + 1), float(len(chunk)), 0.5] for index, chunk in enumerate(chunks)]

    monkeypatch.setattr(embedding, "generate_embeddings", _generate_embeddings)


def test_status_endpoints_still_work() -> None:
    root_response = client.get("/")
    health_response = client.get("/health")

    assert root_response.status_code == 200
    assert root_response.json() == {"message": "PDF Chat API is running."}
    assert health_response.status_code == 200
    body = health_response.json()
    assert body["status"] == "ok"
    assert body["version"] == "0.1.0"
    assert body["deployment"]["environment"] == "unknown"
    assert body["deployment"]["commit_sha"] == "unknown"
    assert body["deployment"]["deployment_id"] == "unknown"
    assert body["deployment"]["deployed_at"]


def test_upload_pdf_returns_parsed_metadata() -> None:
    pdf_bytes = build_pdf_bytes(("Hello from a PDF upload test. " * 120).strip(), page_count=3)

    response = client.post(
        "/upload",
        files={"file": ("sample.pdf", BytesIO(pdf_bytes), "application/pdf")},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["document_id"]
    assert body["already_exists"] is False
    assert body["filename"] == "sample.pdf"
    assert body["page_count"] == 3
    assert body["text_length"] > 0
    assert body["chunk_count"] > 1
    assert body["embedding_count"] == body["chunk_count"]
    assert body["indexed_new_chunks"] == body["chunk_count"]
    assert body["expires_at"]
    assert "Hello from a PDF upload test." in body["preview"]
    assert len(body["preview"]) <= 1000

    registry = document_registry.load_registry()
    stored_document = registry[document_registry.compute_file_sha256(pdf_bytes)]
    assert stored_document.uploaded_at
    assert stored_document.expires_at == body["expires_at"]

    saved_indexes = list((vector_store.INDEX_ROOT).glob("*/faiss.index"))
    saved_chunks = list((vector_store.INDEX_ROOT).glob("*/chunks.json"))

    assert len(saved_indexes) == 1
    assert len(saved_chunks) == 1


def test_upload_reuses_existing_index_for_duplicate_pdf() -> None:
    pdf_bytes = build_pdf_bytes(("Repeated PDF upload should not duplicate indexes. " * 60).strip(), page_count=2)

    first_response = client.post(
        "/upload",
        files={"file": ("sample.pdf", BytesIO(pdf_bytes), "application/pdf")},
    )
    second_response = client.post(
        "/upload",
        files={"file": ("sample.pdf", BytesIO(pdf_bytes), "application/pdf")},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_body = first_response.json()
    second_body = second_response.json()

    assert first_body["already_exists"] is False
    assert second_body["already_exists"] is True
    assert second_body["document_id"] == first_body["document_id"]
    assert second_body["indexed_new_chunks"] == 0
    assert second_body["chunk_count"] == first_body["chunk_count"]
    assert datetime.fromisoformat(second_body["expires_at"]) >= datetime.fromisoformat(first_body["expires_at"])
    assert len(list((vector_store.INDEX_ROOT).glob("*/faiss.index"))) == 1
    assert len(list((vector_store.INDEX_ROOT).glob("*/chunks.json"))) == 1
    assert len(list((pdf_service.UPLOAD_DIR).glob("*.pdf"))) == 1


def test_duplicate_upload_refreshes_document_expiration(monkeypatch: pytest.MonkeyPatch) -> None:
    pdf_bytes = build_pdf_bytes(("Repeated PDF upload should refresh expiration. " * 60).strip(), page_count=2)
    first_now = datetime(2026, 3, 22, 10, 0, tzinfo=timezone.utc)
    second_now = first_now + timedelta(hours=6)
    timestamps = [
        (first_now.isoformat(), (first_now + timedelta(days=1)).isoformat()),
        (second_now.isoformat(), (second_now + timedelta(days=1)).isoformat()),
    ]

    monkeypatch.setattr("app.services.cleanup_service.cleanup_expired_documents", lambda: [])
    monkeypatch.setattr(
        "app.services.cleanup_service.build_expiration_timestamps",
        lambda: timestamps.pop(0),
    )

    first_response = client.post(
        "/upload",
        files={"file": ("sample.pdf", BytesIO(pdf_bytes), "application/pdf")},
    )
    second_response = client.post(
        "/upload",
        files={"file": ("sample.pdf", BytesIO(pdf_bytes), "application/pdf")},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_expires_at = datetime.fromisoformat(first_response.json()["expires_at"])
    second_expires_at = datetime.fromisoformat(second_response.json()["expires_at"])
    assert second_expires_at == second_now + timedelta(days=1)
    assert second_expires_at > first_expires_at


def test_upload_rejects_non_pdf_file() -> None:
    response = client.post(
        "/upload",
        files={"file": ("note.txt", BytesIO(b"not a pdf"), "text/plain")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "仅支持上传 PDF 文件。"}


def test_upload_rejects_pdf_when_extracted_text_exceeds_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    oversized_text = "A" * (pdf_service.MAX_EXTRACTED_TEXT_LENGTH + 1)

    monkeypatch.setattr(
        pdf_service,
        "extract_pdf_content",
        lambda _: ([oversized_text], oversized_text, 1),
    )

    response = client.post(
        "/upload",
        files={"file": ("oversized.pdf", BytesIO(build_pdf_bytes("placeholder")), "application/pdf")},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": (
            f"提取出的文本过长，无法建立索引（当前 {len(oversized_text)} 个字符，限制为 "
            f"{pdf_service.MAX_EXTRACTED_TEXT_LENGTH} 个字符）。"
        )
    }
    assert len(list((vector_store.INDEX_ROOT).glob("*/faiss.index"))) == 0
    assert len(list((vector_store.INDEX_ROOT).glob("*/chunks.json"))) == 0


def _parse_sse_events(payload: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    blocks = [block for block in payload.split("\n\n") if block.strip()]
    for block in blocks:
        event_name = ""
        data = ""
        for line in block.splitlines():
            if line.startswith("event:"):
                event_name = line.split(":", 1)[1].strip()
            if line.startswith("data:"):
                data = line.split(":", 1)[1].strip()
        assert event_name
        assert data
        events.append((event_name, json.loads(data)))
    return events


def test_upload_stream_returns_staged_progress_and_done_payload() -> None:
    pdf_bytes = build_pdf_bytes(("Streaming upload should emit progress. " * 60).strip(), page_count=3)

    with client.stream(
        "POST",
        "/upload/stream",
        files={"file": ("sample.pdf", BytesIO(pdf_bytes), "application/pdf")},
    ) as response:
        assert response.status_code == 200
        payload = response.read().decode("utf-8")

    events = _parse_sse_events(payload)
    assert [event_name for event_name, _ in events] == [
        "stage",
        "stage",
        "stage",
        "stage",
        "embedding_progress",
        "stage",
        "done",
    ]

    stage_payloads = [event for event_name, event in events if event_name == "stage"]
    assert [event["stage"] for event in stage_payloads] == [
        "upload_received",
        "parsing_pdf",
        "chunking",
        "generating_embeddings",
        "persisting_index",
    ]

    done_payload = events[-1][1]
    assert done_payload["filename"] == "sample.pdf"
    assert done_payload["page_count"] == 3
    assert done_payload["chunk_count"] > 1


def test_upload_stream_emits_embedding_batch_progress_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf_bytes = build_pdf_bytes(("Embedding progress should include batch metadata. " * 80).strip(), page_count=4)

    def _generate_embeddings(chunks: list[str], progress_callback=None) -> list[list[float]]:
        midpoint = max(len(chunks) // 2, 1)
        if progress_callback is not None:
            progress_callback(
                {
                    "current_batch": 1,
                    "total_batches": 2,
                    "completed_chunks": midpoint,
                    "total_chunks": len(chunks),
                }
            )
            progress_callback(
                {
                    "current_batch": 2,
                    "total_batches": 2,
                    "completed_chunks": len(chunks),
                    "total_chunks": len(chunks),
                }
            )
        return [[float(index + 1), float(len(chunk)), 0.5] for index, chunk in enumerate(chunks)]

    monkeypatch.setattr(embedding, "generate_embeddings", _generate_embeddings)

    with client.stream(
        "POST",
        "/upload/stream",
        files={"file": ("sample.pdf", BytesIO(pdf_bytes), "application/pdf")},
    ) as response:
        assert response.status_code == 200
        events = _parse_sse_events(response.read().decode("utf-8"))

    embedding_events = [event for event_name, event in events if event_name == "embedding_progress"]
    assert len(embedding_events) == 2
    assert embedding_events[0]["current_batch"] == 1
    assert embedding_events[0]["total_batches"] == 2
    assert embedding_events[1]["current_batch"] == 2
    assert embedding_events[1]["total_batches"] == 2
    assert embedding_events[-1]["completed_chunks"] == embedding_events[-1]["total_chunks"]


def test_upload_stream_emits_error_when_extracted_text_exceeds_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    oversized_text = "A" * (pdf_service.MAX_EXTRACTED_TEXT_LENGTH + 1)

    monkeypatch.setattr(
        pdf_service,
        "extract_pdf_content",
        lambda _: ([oversized_text], oversized_text, 1),
    )

    with client.stream(
        "POST",
        "/upload/stream",
        files={"file": ("oversized.pdf", BytesIO(build_pdf_bytes("placeholder")), "application/pdf")},
    ) as response:
        assert response.status_code == 200
        events = _parse_sse_events(response.read().decode("utf-8"))

    assert [event_name for event_name, _ in events] == ["stage", "stage", "error"]
    assert [event["stage"] for event_name, event in events if event_name == "stage"] == [
        "upload_received",
        "parsing_pdf",
    ]
    assert events[-1][1] == {
        "detail": (
            f"提取出的文本过长，无法建立索引（当前 {len(oversized_text)} 个字符，限制为 "
            f"{pdf_service.MAX_EXTRACTED_TEXT_LENGTH} 个字符）。"
        )
    }
