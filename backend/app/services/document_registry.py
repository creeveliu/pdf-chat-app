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
    return {
        file_sha256: RegisteredDocument(**document_payload)
        for file_sha256, document_payload in documents.items()
    }


def get_document_by_hash(file_sha256: str) -> RegisteredDocument | None:
    return load_registry().get(file_sha256)


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
