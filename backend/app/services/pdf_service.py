from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
import re
from uuid import uuid4

import fitz
from fastapi import UploadFile

from app.services import chunking, embedding, vector_store


BACKEND_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BACKEND_DIR / "data" / "uploads"
PREVIEW_LENGTH = 1000

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    pass


class PdfProcessingError(Exception):
    pass


class StorageError(Exception):
    pass


@dataclass
class PdfUploadResponse:
    filename: str
    text_length: int
    page_count: int
    preview: str
    chunk_count: int
    embedding_count: int


def ensure_upload_dir() -> Path:
    try:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise StorageError("Could not create upload directory.") from exc

    return UPLOAD_DIR


def validate_pdf_upload(filename: str, content_type: str | None, file_bytes: bytes) -> None:
    if not filename:
        raise ValidationError("Filename is required.")

    if not filename.lower().endswith(".pdf"):
        raise ValidationError("Only PDF files are supported.")

    if content_type and content_type != "application/pdf":
        raise ValidationError("Only PDF files are supported.")

    if not file_bytes:
        raise ValidationError("Uploaded file is empty.")

    if not file_bytes.startswith(b"%PDF"):
        raise ValidationError("Only PDF files are supported.")


def build_storage_path(filename: str) -> Path:
    safe_name = Path(filename).name
    return ensure_upload_dir() / f"{uuid4().hex}_{safe_name}"


def build_document_id(filename: str) -> str:
    stem = Path(filename).stem.lower()
    safe_stem = re.sub(r"[^a-z0-9]+", "-", stem).strip("-") or "document"
    return f"{safe_stem}-{uuid4().hex}"


def extract_pdf_text(file_path: Path) -> tuple[str, int]:
    try:
        document = fitz.open(file_path)
    except Exception as exc:  # pragma: no cover - fitz error types vary
        raise PdfProcessingError("Uploaded file could not be parsed as a PDF.") from exc

    try:
        pages = [page.get_text() for page in document]
        full_text = "\n".join(pages).strip()
        return full_text, document.page_count
    finally:
        document.close()


async def save_and_parse_pdf(file: UploadFile) -> PdfUploadResponse:
    file_bytes = await file.read()
    validate_pdf_upload(file.filename or "", file.content_type, file_bytes)
    logger.info("Received upload: %s", file.filename)

    storage_path = build_storage_path(file.filename or "upload.pdf")

    try:
        storage_path.write_bytes(file_bytes)
    except OSError as exc:
        raise StorageError("Could not save uploaded file.") from exc

    try:
        text, page_count = extract_pdf_text(storage_path)
    except PdfProcessingError:
        storage_path.unlink(missing_ok=True)
        raise

    chunks = chunking.chunk_text(text)
    if not chunks:
        raise PdfProcessingError("No extractable text was found in the uploaded PDF.")

    embeddings = embedding.generate_embeddings(chunks)
    document_id = build_document_id(file.filename or storage_path.name)
    vector_store.persist_document_index(
        document_id=document_id,
        filename=file.filename or storage_path.name,
        chunks=chunks,
        embeddings=embeddings,
    )
    logger.info(
        "Completed indexing for %s with %s chunks",
        file.filename,
        len(chunks),
    )

    return PdfUploadResponse(
        filename=file.filename or storage_path.name,
        text_length=len(text),
        page_count=page_count,
        preview=text[:PREVIEW_LENGTH],
        chunk_count=len(chunks),
        embedding_count=len(embeddings),
    )
