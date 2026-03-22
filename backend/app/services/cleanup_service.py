from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from pathlib import Path
import shutil

from app.services import document_registry, vector_store


logger = logging.getLogger(__name__)

RETENTION_PERIOD = timedelta(days=1)
EXPIRATION_ERROR_MESSAGE = "指定文档已过期并已自动清理，请重新上传 PDF。"


class DocumentExpiredError(RuntimeError):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def build_expiration_timestamps(now: datetime | None = None) -> tuple[str, str]:
    current_time = now or utcnow()
    expires_at = current_time + RETENTION_PERIOD
    return current_time.isoformat(), expires_at.isoformat()


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        timestamp = datetime.fromisoformat(value)
    except ValueError:
        return None

    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=timezone.utc)

    return timestamp.astimezone(timezone.utc)


def _latest_artifact_mtime(document: document_registry.RegisteredDocument) -> datetime | None:
    candidate_paths = [
        _build_storage_path(document.file_sha256),
        vector_store.ensure_index_root() / document.document_id / "faiss.index",
        vector_store.ensure_index_root() / document.document_id / "chunks.json",
    ]

    mtimes = [
        datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        for path in candidate_paths
        if path.exists()
    ]
    if not mtimes:
        return None
    return max(mtimes)


def get_document_expiration(document: document_registry.RegisteredDocument) -> datetime | None:
    expires_at = _parse_timestamp(document.expires_at)
    if expires_at is not None:
        return expires_at

    latest_mtime = _latest_artifact_mtime(document)
    if latest_mtime is None:
        return None

    return latest_mtime + RETENTION_PERIOD


def is_document_expired(
    document: document_registry.RegisteredDocument,
    now: datetime | None = None,
) -> bool:
    expires_at = get_document_expiration(document)
    if expires_at is None:
        return False
    return expires_at <= (now or utcnow())


def delete_document_assets(document: document_registry.RegisteredDocument) -> None:
    storage_path = _build_storage_path(document.file_sha256)
    if storage_path.exists():
        storage_path.unlink()

    document_dir = vector_store.ensure_index_root() / document.document_id
    if document_dir.exists():
        shutil.rmtree(document_dir)

    document_registry.remove_document(document.file_sha256)


def cleanup_expired_documents() -> list[str]:
    cleaned_document_ids: list[str] = []
    current_time = utcnow()
    registry = document_registry.load_registry()

    for document in registry.values():
        if not is_document_expired(document, now=current_time):
            continue

        try:
            delete_document_assets(document)
        except OSError:
            logger.exception("Failed to delete expired document assets for %s", document.document_id)
            continue
        except document_registry.DocumentRegistryError:
            logger.exception("Failed to update registry while deleting %s", document.document_id)
            continue

        cleaned_document_ids.append(document.document_id)

    _cleanup_orphan_uploads()
    _cleanup_orphan_indexes()
    return cleaned_document_ids


def ensure_document_available(document_id: str) -> None:
    document = document_registry.get_document_by_id(document_id)
    if document is None:
        return

    if not is_document_expired(document):
        return

    try:
        delete_document_assets(document)
    except OSError:
        logger.exception("Failed to delete expired document assets for %s", document_id)
    except document_registry.DocumentRegistryError:
        logger.exception("Failed to update registry while deleting expired document %s", document_id)

    raise DocumentExpiredError(EXPIRATION_ERROR_MESSAGE)


def _cleanup_orphan_uploads() -> None:
    uploads_dir = _ensure_upload_dir()
    registry = document_registry.load_registry()
    referenced_filenames = {
        document.storage_filename
        for document in registry.values()
        if document.storage_filename
    }

    for path in uploads_dir.iterdir():
        if path.name.startswith("."):
            continue
        if not path.is_file():
            continue
        if path.name in referenced_filenames:
            continue

        try:
            path.unlink()
        except OSError:
            logger.exception("Failed to remove orphan upload file %s", path)


def _cleanup_orphan_indexes() -> None:
    index_root = vector_store.ensure_index_root()
    referenced_document_ids = {
        document.document_id
        for document in document_registry.load_registry().values()
    }

    for path in index_root.iterdir():
        if path.name.startswith("."):
            continue
        if not path.is_dir():
            continue
        if path.name in referenced_document_ids:
            continue

        try:
            shutil.rmtree(path)
        except OSError:
            logger.exception("Failed to remove orphan index directory %s", path)


def _ensure_upload_dir() -> Path:
    from app.services import pdf_service

    return pdf_service.ensure_upload_dir()


def _build_storage_path(file_sha256: str) -> Path:
    from app.services import pdf_service

    return pdf_service.build_storage_path(file_sha256)
