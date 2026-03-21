from __future__ import annotations


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
