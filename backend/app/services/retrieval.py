from __future__ import annotations

from hashlib import sha256
import json
import logging
from dataclasses import dataclass

import faiss
import numpy as np

from app.services import cleanup_service, embedding, vector_store


logger = logging.getLogger(__name__)


class RetrievalError(RuntimeError):
    pass


class DocumentSelectionError(ValueError):
    pass


@dataclass
class RetrievedContext:
    document_id: str
    filename: str
    chunk_id: int
    chunk_index: int
    page_number: int | None
    page_numbers: list[int]
    chunk_hash: str
    text: str
    score: float


def _load_index_payload(document_dir) -> tuple[faiss.Index, dict]:
    index_path = document_dir / "faiss.index"
    chunks_path = document_dir / "chunks.json"

    if not index_path.exists() or not chunks_path.exists():
        raise RetrievalError("当前没有可用索引，请先上传 PDF。")

    index = faiss.read_index(str(index_path))
    payload = json.loads(chunks_path.read_text(encoding="utf-8"))
    return index, payload


def _resolve_document_dirs(document_id: str | None) -> list:
    if document_id:
        cleanup_service.ensure_document_available(document_id)

    cleanup_service.cleanup_expired_documents()
    index_root = vector_store.ensure_index_root()
    document_dirs = [path for path in index_root.iterdir() if path.is_dir()]
    if not document_dirs:
        raise RetrievalError("当前没有可用索引，请先上传 PDF。")

    if document_id:
        document_dir = index_root / document_id
        if not document_dir.is_dir():
            raise RetrievalError("未找到指定 document_id 对应的向量索引。")
        return [document_dir]

    if len(document_dirs) > 1:
        raise DocumentSelectionError(
            "当前已有多份已索引的 PDF，请传入 document_id 后再提问。"
        )

    return document_dirs


def _build_chunk_hash(chunk_payload: dict[str, object]) -> str:
    stored_hash = chunk_payload.get("chunk_hash")
    if isinstance(stored_hash, str) and stored_hash:
        return stored_hash

    text = str(chunk_payload.get("text", ""))
    return sha256(text.encode("utf-8")).hexdigest()


def _build_page_numbers(chunk_payload: dict[str, object]) -> list[int]:
    stored_page_numbers = chunk_payload.get("page_numbers")
    if isinstance(stored_page_numbers, list):
        return [int(page_number) for page_number in stored_page_numbers if isinstance(page_number, (int, float))]

    page_number = chunk_payload.get("page_number")
    if isinstance(page_number, (int, float)):
        return [int(page_number)]

    return []


def _build_primary_page_number(chunk_payload: dict[str, object]) -> int | None:
    page_number = chunk_payload.get("page_number")
    if isinstance(page_number, (int, float)):
        return int(page_number)

    page_numbers = _build_page_numbers(chunk_payload)
    return page_numbers[0] if page_numbers else None


def _deduplicate_matches(matches: list[RetrievedContext], top_k: int) -> list[RetrievedContext]:
    unique_matches: list[RetrievedContext] = []
    seen_keys: set[tuple[str, str]] = set()

    for match in sorted(matches, key=lambda item: item.score):
        dedupe_key = (match.document_id, match.chunk_hash)
        if dedupe_key in seen_keys:
            continue

        seen_keys.add(dedupe_key)
        unique_matches.append(match)
        if len(unique_matches) >= top_k:
            break

    return unique_matches


def retrieve_contexts(
    question: str,
    top_k: int = 3,
    document_id: str | None = None,
) -> list[RetrievedContext]:
    document_dirs = _resolve_document_dirs(document_id)

    query_embeddings = embedding.generate_embeddings([question])
    query_vector = np.array(query_embeddings, dtype="float32")
    query_dimension = query_vector.shape[1]

    matches: list[RetrievedContext] = []
    compatible_index_found = False

    for document_dir in document_dirs:
        index, payload = _load_index_payload(document_dir)
        if index.d != query_dimension:
            logger.warning(
                "Skipping incompatible index %s: query dim=%s index dim=%s",
                document_dir,
                query_dimension,
                index.d,
            )
            continue

        compatible_index_found = True
        search_k = min(max(top_k * 5, top_k), index.ntotal)
        if search_k <= 0:
            continue

        distances, indices = index.search(query_vector, search_k)
        chunks = payload.get("chunks", [])

        for distance, index_position in zip(distances[0], indices[0]):
            if index_position < 0 or index_position >= len(chunks):
                continue

            chunk_payload = chunks[index_position]
            chunk_index = int(chunk_payload.get("chunk_index", chunk_payload.get("chunk_id", index_position)))
            page_numbers = _build_page_numbers(chunk_payload)
            matches.append(
                RetrievedContext(
                    document_id=payload["document_id"],
                    filename=payload["filename"],
                    chunk_id=chunk_index,
                    chunk_index=chunk_index,
                    page_number=_build_primary_page_number(chunk_payload),
                    page_numbers=page_numbers,
                    chunk_hash=_build_chunk_hash(chunk_payload),
                    text=chunk_payload["text"],
                    score=float(distance),
                )
            )

    if not compatible_index_found:
        raise RetrievalError("当前没有兼容的向量索引，请重新上传 PDF 以重建索引。")

    if not matches:
        raise RetrievalError("当前没有可用索引，请先上传 PDF。")

    selected = _deduplicate_matches(matches, top_k=top_k)
    logger.info("Retrieved %s contexts for question", len(selected))
    return selected
