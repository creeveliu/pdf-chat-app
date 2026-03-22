from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import logging
from pathlib import Path

from app.services import vector_store


logger = logging.getLogger(__name__)


class DocumentRegistryError(RuntimeError):
    pass


@dataclass
class RegisteredDocument:
    document_id: str
    file_sha256: str
    filename: str
    storage_filename: str
    page_count: int
    text_length: int
    preview: str
    chunk_count: int
    embedding_count: int
    uploaded_at: str | None = None
    expires_at: str | None = None


def compute_file_sha256(file_bytes: bytes) -> str:
    return sha256(file_bytes).hexdigest()


def build_document_id(file_sha256: str) -> str:
    return f"doc-{file_sha256[:16]}"


def _registry_path() -> Path:
    return vector_store.ensure_index_root() / "documents.json"


def load_registry() -> dict[str, RegisteredDocument]:
    registry_path = _registry_path()
    if not registry_path.exists():
        return {}

    try:
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DocumentRegistryError("读取文档注册表失败。") from exc

    documents = payload.get("documents", {})
    normalized_documents: dict[str, RegisteredDocument] = {}
    for file_sha256, document_payload in documents.items():
        normalized_payload = dict(document_payload)
        normalized_payload.setdefault("uploaded_at", None)
        normalized_payload.setdefault("expires_at", None)
        normalized_documents[file_sha256] = RegisteredDocument(**normalized_payload)
    return normalized_documents


def get_document_by_hash(file_sha256: str) -> RegisteredDocument | None:
    return load_registry().get(file_sha256)


def get_document_by_id(document_id: str) -> RegisteredDocument | None:
    for document in load_registry().values():
        if document.document_id == document_id:
            return document
    return None


def remove_document(file_sha256: str) -> RegisteredDocument | None:
    registry = load_registry()
    removed_document = registry.pop(file_sha256, None)
    if removed_document is None:
        return None

    payload = {
        "documents": {
            current_sha256: asdict(registered_document)
            for current_sha256, registered_document in registry.items()
        }
    }

    registry_path = _registry_path()
    try:
        registry_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        raise DocumentRegistryError("保存文档注册表失败。") from exc

    logger.info(
        "Removed document %s for hash %s from registry",
        removed_document.document_id,
        removed_document.file_sha256,
    )
    return removed_document


def save_document(document: RegisteredDocument) -> RegisteredDocument:
    registry = load_registry()
    registry[document.file_sha256] = document

    payload = {
        "documents": {
            file_sha256: asdict(registered_document)
            for file_sha256, registered_document in registry.items()
        }
    }

    registry_path = _registry_path()
    try:
        registry_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        raise DocumentRegistryError("保存文档注册表失败。") from exc

    logger.info(
        "Registered document %s for hash %s",
        document.document_id,
        document.file_sha256,
    )
    return document
