from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import faiss
import numpy as np

from app.services.chunking import ChunkRecord


logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[2]
INDEX_ROOT = BACKEND_DIR / "data" / "index"


class VectorStoreError(RuntimeError):
    pass


@dataclass
class VectorStoreArtifacts:
    document_id: str
    index_path: Path
    chunks_path: Path


def ensure_index_root() -> Path:
    try:
        INDEX_ROOT.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise VectorStoreError("Could not create index directory.") from exc

    return INDEX_ROOT


def document_artifacts_exist(document_id: str) -> bool:
    document_dir = ensure_index_root() / document_id
    return (document_dir / "faiss.index").exists() and (document_dir / "chunks.json").exists()


def persist_document_index(
    document_id: str,
    filename: str,
    file_sha256: str,
    chunks: list[ChunkRecord],
    embeddings: list[list[float]],
) -> VectorStoreArtifacts:
    if not chunks or not embeddings:
        raise ValueError("Chunks and embeddings are required to build an index.")

    if len(chunks) != len(embeddings):
        raise ValueError("Chunk count and embedding count must match.")

    try:
        document_dir = ensure_index_root() / document_id
        document_dir.mkdir(parents=True, exist_ok=True)

        vectors = np.array(embeddings, dtype="float32")
        index = faiss.IndexFlatL2(vectors.shape[1])
        index.add(vectors)

        index_path = document_dir / "faiss.index"
        chunks_path = document_dir / "chunks.json"

        faiss.write_index(index, str(index_path))
        chunks_payload = {
            "document_id": document_id,
            "filename": filename,
            "file_sha256": file_sha256,
            "chunk_count": len(chunks),
            "chunks": [
                {
                    "chunk_id": chunk.chunk_index,
                    "chunk_index": chunk.chunk_index,
                    "page_number": chunk.page_number,
                    "page_numbers": chunk.page_numbers,
                    "chunk_hash": chunk.chunk_hash,
                    "text": chunk.text,
                }
                for chunk in chunks
            ],
        }
        chunks_path.write_text(
            json.dumps(chunks_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except (OSError, RuntimeError, ValueError) as exc:
        raise VectorStoreError("Failed to persist FAISS index and chunks.") from exc

    logger.info(
        "Persisted vector index for %s at %s with %s chunks",
        document_id,
        index_path,
        len(chunks),
    )
    return VectorStoreArtifacts(
        document_id=document_id,
        index_path=index_path,
        chunks_path=chunks_path,
    )
