from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True)
class ChunkRecord:
    chunk_index: int
    text: str
    page_number: int | None
    page_numbers: list[int]
    chunk_hash: str


def chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 100) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be non-negative and smaller than chunk_size.")

    normalized_text = " ".join(text.split()).strip()
    if not normalized_text:
        return []

    step = chunk_size - chunk_overlap
    chunks: list[str] = []

    for start in range(0, len(normalized_text), step):
        chunk = normalized_text[start : start + chunk_size]
        if not chunk:
            continue
        chunks.append(chunk)
        if start + chunk_size >= len(normalized_text):
            break

    return chunks


def chunk_page_texts(
    page_texts: list[str],
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> list[ChunkRecord]:
    chunk_records: list[ChunkRecord] = []

    for page_number, page_text in enumerate(page_texts, start=1):
        for chunk in chunk_text(page_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap):
            chunk_records.append(
                ChunkRecord(
                    chunk_index=len(chunk_records),
                    text=chunk,
                    page_number=page_number,
                    page_numbers=[page_number],
                    chunk_hash=sha256(chunk.encode("utf-8")).hexdigest(),
                )
            )

    return chunk_records
