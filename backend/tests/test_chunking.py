from app.services.chunking import chunk_text


def test_chunk_text_creates_overlapping_chunks() -> None:
    text = "".join(str(index % 10) for index in range(1800))

    chunks = chunk_text(text, chunk_size=700, chunk_overlap=100)

    assert len(chunks) >= 3
    assert all(1 <= len(chunk) <= 700 for chunk in chunks)
    assert chunks[0][-100:] == chunks[1][:100]
