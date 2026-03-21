from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import faiss
import numpy as np

from app.services import embedding, vector_store


logger = logging.getLogger(__name__)


class RetrievalError(RuntimeError):
    pass


@dataclass
class RetrievedContext:
    document_id: str
    filename: str
    chunk_id: int
    text: str
    score: float


def _load_index_payload(document_dir) -> tuple[faiss.Index, dict]:
    index_path = document_dir / "faiss.index"
    chunks_path = document_dir / "chunks.json"

    if not index_path.exists() or not chunks_path.exists():
        raise RetrievalError("No vector index available. Upload a PDF first.")

    index = faiss.read_index(str(index_path))
    payload = json.loads(chunks_path.read_text(encoding="utf-8"))
    return index, payload


def retrieve_contexts(question: str, top_k: int = 3) -> list[RetrievedContext]:
    document_dirs = [path for path in vector_store.ensure_index_root().iterdir() if path.is_dir()]
    if not document_dirs:
        raise RetrievalError("No vector index available. Upload a PDF first.")

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
        search_k = min(top_k, index.ntotal)
        if search_k <= 0:
            continue

        distances, indices = index.search(query_vector, search_k)
        chunks = payload.get("chunks", [])

        for distance, index_position in zip(distances[0], indices[0]):
            if index_position < 0 or index_position >= len(chunks):
                continue

            chunk_payload = chunks[index_position]
            matches.append(
                RetrievedContext(
                    document_id=payload["document_id"],
                    filename=payload["filename"],
                    chunk_id=chunk_payload["chunk_id"],
                    text=chunk_payload["text"],
                    score=float(distance),
                )
            )

    if not compatible_index_found:
        raise RetrievalError("No compatible vector index available. Re-upload the PDF to rebuild the index.")

    if not matches:
        raise RetrievalError("No vector index available. Upload a PDF first.")

    matches.sort(key=lambda item: item.score)
    selected = matches[:top_k]
    logger.info("Retrieved %s contexts for question", len(selected))
    return selected
