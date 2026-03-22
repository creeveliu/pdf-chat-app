from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Callable

import fitz
from fastapi import UploadFile

from app.services import chunking, cleanup_service, document_registry, embedding, vector_store


BACKEND_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BACKEND_DIR / "data" / "uploads"
PREVIEW_LENGTH = 1000
MAX_EXTRACTED_TEXT_LENGTH = 40_000

logger = logging.getLogger(__name__)

UploadProgressCallback = Callable[[str, dict[str, object]], None]


class ValidationError(Exception):
    pass


class PdfProcessingError(Exception):
    pass


class StorageError(Exception):
    pass


@dataclass
class PdfUploadResponse:
    document_id: str
    already_exists: bool
    filename: str
    text_length: int
    page_count: int
    preview: str
    chunk_count: int
    embedding_count: int
    indexed_new_chunks: int
    expires_at: str | None = None


def ensure_upload_dir() -> Path:
    try:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise StorageError("无法创建上传目录。") from exc

    return UPLOAD_DIR


def validate_pdf_upload(filename: str, content_type: str | None, file_bytes: bytes) -> None:
    if not filename:
        raise ValidationError("文件名不能为空。")

    if not filename.lower().endswith(".pdf"):
        raise ValidationError("仅支持上传 PDF 文件。")

    if content_type and content_type != "application/pdf":
        raise ValidationError("仅支持上传 PDF 文件。")

    if not file_bytes:
        raise ValidationError("上传的文件为空。")

    if not file_bytes.startswith(b"%PDF"):
        raise ValidationError("仅支持上传 PDF 文件。")


def build_storage_path(file_sha256: str) -> Path:
    return ensure_upload_dir() / f"{file_sha256}.pdf"


def _emit_progress(
    progress_callback: UploadProgressCallback | None,
    event_name: str,
    data: dict[str, object],
) -> None:
    if progress_callback is not None:
        progress_callback(event_name, data)


def extract_pdf_content(file_bytes: bytes) -> tuple[list[str], str, int]:
    try:
        document = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:  # pragma: no cover - fitz error types vary
        raise PdfProcessingError("上传的文件无法解析为 PDF。") from exc

    try:
        page_texts = [page.get_text() for page in document]
        full_text = "\n".join(page_texts).strip()
        return page_texts, full_text, document.page_count
    finally:
        document.close()


def validate_extracted_text_length(text: str) -> None:
    if len(text) > MAX_EXTRACTED_TEXT_LENGTH:
        raise PdfProcessingError(
            f"提取出的文本过长，无法建立索引（当前 {len(text)} 个字符，限制为 "
            f"{MAX_EXTRACTED_TEXT_LENGTH} 个字符）。"
        )


def process_pdf_upload(
    file_bytes: bytes,
    filename: str,
    content_type: str | None,
    progress_callback: UploadProgressCallback | None = None,
) -> PdfUploadResponse:
    cleanup_service.cleanup_expired_documents()
    validate_pdf_upload(filename, content_type, file_bytes)
    logger.info("Received upload: %s", filename)
    _emit_progress(
        progress_callback,
        "stage",
        {
            "stage": "upload_received",
            "filename": filename,
        },
    )

    file_sha256 = document_registry.compute_file_sha256(file_bytes)
    existing_document = document_registry.get_document_by_hash(file_sha256)

    if existing_document and vector_store.document_artifacts_exist(existing_document.document_id):
        uploaded_at, expires_at = cleanup_service.build_expiration_timestamps()
        document_registry.save_document(
            document_registry.RegisteredDocument(
                document_id=existing_document.document_id,
                file_sha256=existing_document.file_sha256,
                filename=existing_document.filename,
                storage_filename=existing_document.storage_filename,
                page_count=existing_document.page_count,
                text_length=existing_document.text_length,
                preview=existing_document.preview,
                chunk_count=existing_document.chunk_count,
                embedding_count=existing_document.embedding_count,
                uploaded_at=uploaded_at,
                expires_at=expires_at,
            )
        )
        logger.info(
            "Reusing existing index for %s with document_id=%s",
            filename,
            existing_document.document_id,
        )
        _emit_progress(
            progress_callback,
            "stage",
            {
                "stage": "reusing_index",
                "filename": filename or existing_document.filename,
                "document_id": existing_document.document_id,
            },
        )
        return PdfUploadResponse(
            document_id=existing_document.document_id,
            already_exists=True,
            filename=filename or existing_document.filename,
            text_length=existing_document.text_length,
            page_count=existing_document.page_count,
            preview=existing_document.preview,
            chunk_count=existing_document.chunk_count,
            embedding_count=existing_document.embedding_count,
            indexed_new_chunks=0,
            expires_at=expires_at,
        )

    _emit_progress(
        progress_callback,
        "stage",
        {
            "stage": "parsing_pdf",
            "filename": filename,
        },
    )
    page_texts, text, page_count = extract_pdf_content(file_bytes)
    validate_extracted_text_length(text)
    _emit_progress(
        progress_callback,
        "stage",
        {
            "stage": "chunking",
            "filename": filename,
            "page_count": page_count,
        },
    )
    chunks = chunking.chunk_page_texts(page_texts)
    if not chunks:
        raise PdfProcessingError("上传的 PDF 中未提取到可用文本。")

    storage_path = build_storage_path(file_sha256)
    if not storage_path.exists():
        try:
            storage_path.write_bytes(file_bytes)
        except OSError as exc:
            raise StorageError("无法保存上传的 PDF 文件。") from exc

    chunk_texts = [chunk.text for chunk in chunks]
    _emit_progress(
        progress_callback,
        "stage",
        {
            "stage": "generating_embeddings",
            "filename": filename,
            "chunk_count": len(chunks),
        },
    )
    embedding_progress_callback = None
    if progress_callback is not None:
        embedding_progress_callback = lambda payload: _emit_progress(
            progress_callback,
            "embedding_progress",
            payload,
        )
    if embedding_progress_callback is None:
        embeddings = embedding.generate_embeddings(chunk_texts)
    else:
        embeddings = embedding.generate_embeddings(
            chunk_texts,
            progress_callback=embedding_progress_callback,
        )
    document_id = existing_document.document_id if existing_document else document_registry.build_document_id(file_sha256)
    uploaded_at, expires_at = cleanup_service.build_expiration_timestamps()
    _emit_progress(
        progress_callback,
        "stage",
        {
            "stage": "persisting_index",
            "filename": filename,
            "chunk_count": len(chunks),
        },
    )
    vector_store.persist_document_index(
        document_id=document_id,
        filename=filename or storage_path.name,
        file_sha256=file_sha256,
        chunks=chunks,
        embeddings=embeddings,
    )
    document_registry.save_document(
        document_registry.RegisteredDocument(
            document_id=document_id,
            file_sha256=file_sha256,
            filename=filename or storage_path.name,
            storage_filename=storage_path.name,
            page_count=page_count,
            text_length=len(text),
            preview=text[:PREVIEW_LENGTH],
            chunk_count=len(chunks),
            embedding_count=len(embeddings),
            uploaded_at=uploaded_at,
            expires_at=expires_at,
        )
    )
    logger.info(
        "Completed indexing for %s with %s chunks",
        filename,
        len(chunks),
    )

    return PdfUploadResponse(
        document_id=document_id,
        already_exists=False,
        filename=filename or storage_path.name,
        text_length=len(text),
        page_count=page_count,
        preview=text[:PREVIEW_LENGTH],
        chunk_count=len(chunks),
        embedding_count=len(embeddings),
        indexed_new_chunks=len(chunks),
        expires_at=expires_at,
    )


async def save_and_parse_pdf(file: UploadFile) -> PdfUploadResponse:
    file_bytes = await file.read()
    return process_pdf_upload(
        file_bytes=file_bytes,
        filename=file.filename or "",
        content_type=file.content_type,
    )
