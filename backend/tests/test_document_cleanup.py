from __future__ import annotations

from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient

from app import main
from app.main import app
from app.services import cleanup_service, document_registry, embedding, pdf_service, vector_store


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


def test_cleanup_expired_document_removes_pdf_index_and_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    pdf_bytes = build_pdf_bytes(("Cleanup target document. " * 40).strip(), page_count=2)
    response = client.post(
        "/upload",
        files={"file": ("cleanup.pdf", BytesIO(pdf_bytes), "application/pdf")},
    )

    assert response.status_code == 200
    document_id = response.json()["document_id"]
    file_sha256 = document_registry.compute_file_sha256(pdf_bytes)
    storage_path = pdf_service.build_storage_path(file_sha256)
    document_dir = vector_store.ensure_index_root() / document_id

    registry = document_registry.load_registry()
    stored_document = registry[file_sha256]
    monkeypatch.setattr(
        cleanup_service,
        "utcnow",
        lambda: datetime.fromisoformat(stored_document.expires_at) + timedelta(seconds=1),
    )

    cleaned_document_ids = cleanup_service.cleanup_expired_documents()

    assert cleaned_document_ids == [document_id]
    assert not storage_path.exists()
    assert not document_dir.exists()
    assert file_sha256 not in document_registry.load_registry()


def test_cleanup_expired_documents_preserves_active_documents(monkeypatch: pytest.MonkeyPatch) -> None:
    active_pdf = build_pdf_bytes(("Still active. " * 40).strip(), page_count=1)
    response = client.post(
        "/upload",
        files={"file": ("active.pdf", BytesIO(active_pdf), "application/pdf")},
    )

    assert response.status_code == 200
    document_id = response.json()["document_id"]
    file_sha256 = document_registry.compute_file_sha256(active_pdf)
    storage_path = pdf_service.build_storage_path(file_sha256)
    document_dir = vector_store.ensure_index_root() / document_id

    monkeypatch.setattr(
        cleanup_service,
        "utcnow",
        lambda: datetime.fromisoformat(response.json()["expires_at"]) - timedelta(seconds=1),
    )

    assert cleanup_service.cleanup_expired_documents() == []
    assert storage_path.exists()
    assert document_dir.exists()
    assert file_sha256 in document_registry.load_registry()


def test_ask_returns_expired_message_after_cleanup(monkeypatch: pytest.MonkeyPatch) -> None:
    pdf_bytes = build_pdf_bytes(("Expired guide. " * 60).strip(), page_count=1)
    upload_response = client.post(
        "/upload",
        files={"file": ("expired.pdf", BytesIO(pdf_bytes), "application/pdf")},
    )

    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]
    expires_at = datetime.fromisoformat(upload_response.json()["expires_at"])

    monkeypatch.setattr(
        cleanup_service,
        "utcnow",
        lambda: expires_at + timedelta(seconds=1),
    )

    response = client.post(
        "/ask",
        json={"question": "还能问吗？", "document_id": document_id},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "指定文档已过期并已自动清理，请重新上传 PDF。"}


def test_run_startup_cleanup_invokes_cleanup_service(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        cleanup_service,
        "cleanup_expired_documents",
        lambda: calls.append("cleanup") or [],
    )

    main.run_startup_cleanup()

    assert calls == ["cleanup"]


def test_cleanup_expired_documents_ignores_gitkeep_and_orphaned_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    uploads_dir = pdf_service.ensure_upload_dir()
    index_root = vector_store.ensure_index_root()
    (uploads_dir / ".gitkeep").write_text("", encoding="utf-8")
    (index_root / ".gitkeep").write_text("", encoding="utf-8")
    orphan_pdf = uploads_dir / "orphan.pdf"
    orphan_pdf.write_bytes(b"%PDF-orphan")
    orphan_dir = index_root / "doc-orphan"
    orphan_dir.mkdir()
    (orphan_dir / "faiss.index").write_bytes(b"index")
    (orphan_dir / "chunks.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(
        cleanup_service,
        "utcnow",
        lambda: datetime.now(timezone.utc),
    )

    assert cleanup_service.cleanup_expired_documents() == []
    assert (uploads_dir / ".gitkeep").exists()
    assert (index_root / ".gitkeep").exists()
    assert not orphan_pdf.exists()
    assert not orphan_dir.exists()
