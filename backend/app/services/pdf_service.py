from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path

import fitz
from fastapi import UploadFile

from app.services import chunking, document_registry, embedding, vector_store


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
    document_id: str
    already_exists: bool
    filename: str
    text_length: int
    page_count: int
    preview: str
    chunk_count: int
    embedding_count: int
    indexed_new_chunks: int


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


def build_storage_path(file_sha256: str) -> Path:
    return ensure_upload_dir() / f"{file_sha256}.pdf"

def extract_pdf_content(file_bytes: bytes) -> tuple[list[str], str, int]:
    try:
        document = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:  # pragma: no cover - fitz error types vary
        raise PdfProcessingError("Uploaded file could not be parsed as a PDF.") from exc

    try:
        page_texts = [page.get_text() for page in document]
        full_text = "\n".join(page_texts).strip()
        return page_texts, full_text, document.page_count
    finally:
        document.close()


async def save_and_parse_pdf(file: UploadFile) -> PdfUploadResponse:
    file_bytes = await file.read()
    validate_pdf_upload(file.filename or "", file.content_type, file_bytes)
    logger.info("Received upload: %s", file.filename)

    file_sha256 = document_registry.compute_file_sha256(file_bytes)
    existing_document = document_registry.get_document_by_hash(file_sha256)

    if existing_document and vector_store.document_artifacts_exist(existing_document.document_id):
        logger.info(
            "Reusing existing index for %s with document_id=%s",
            file.filename,
            existing_document.document_id,
        )
        return PdfUploadResponse(
            document_id=existing_document.document_id,
            already_exists=True,
            filename=file.filename or existing_document.filename,
            text_length=existing_document.text_length,
            page_count=existing_document.page_count,
            preview=existing_document.preview,
            chunk_count=existing_document.chunk_count,
            embedding_count=existing_document.embedding_count,
            indexed_new_chunks=0,
        )

    page_texts, text, page_count = extract_pdf_content(file_bytes)
    chunks = chunking.chunk_page_texts(page_texts)
    if not chunks:
        raise PdfProcessingError("No extractable text was found in the uploaded PDF.")

    storage_path = build_storage_path(file_sha256)
    if not storage_path.exists():
        try:
            storage_path.write_bytes(file_bytes)
        except OSError as exc:
            raise StorageError("Could not save uploaded file.") from exc

    chunk_texts = [chunk.text for chunk in chunks]
    embeddings = embedding.generate_embeddings(chunk_texts)
    document_id = existing_document.document_id if existing_document else document_registry.build_document_id(file_sha256)
    vector_store.persist_document_index(
        document_id=document_id,
        filename=file.filename or storage_path.name,
        file_sha256=file_sha256,
        chunks=chunks,
        embeddings=embeddings,
    )
    document_registry.save_document(
        document_registry.RegisteredDocument(
            document_id=document_id,
            file_sha256=file_sha256,
            filename=file.filename or storage_path.name,
            storage_filename=storage_path.name,
            page_count=page_count,
            text_length=len(text),
            preview=text[:PREVIEW_LENGTH],
            chunk_count=len(chunks),
            embedding_count=len(embeddings),
        )
    )
    logger.info(
        "Completed indexing for %s with %s chunks",
        file.filename,
        len(chunks),
    )

    return PdfUploadResponse(
        document_id=document_id,
        already_exists=False,
        filename=file.filename or storage_path.name,
        text_length=len(text),
        page_count=page_count,
        preview=text[:PREVIEW_LENGTH],
        chunk_count=len(chunks),
        embedding_count=len(embeddings),
        indexed_new_chunks=len(chunks),
    )
