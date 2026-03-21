from app.services.chunking import chunk_page_texts, chunk_text


def test_chunk_text_creates_overlapping_chunks() -> None:
    text = "".join(str(index % 10) for index in range(1800))

    chunks = chunk_text(text, chunk_size=700, chunk_overlap=100)

    assert len(chunks) >= 3
    assert all(1 <= len(chunk) <= 700 for chunk in chunks)
    assert chunks[0][-100:] == chunks[1][:100]


def test_chunk_page_texts_records_page_metadata() -> None:
    page_texts = [
        "First page content. " * 80,
        "Second page content. " * 80,
    ]

    chunks = chunk_page_texts(page_texts, chunk_size=220, chunk_overlap=40)

    assert chunks
    assert chunks[0].page_number == 1
    assert chunks[0].page_numbers == [1]
    assert chunks[-1].page_number == 2
    assert chunks[-1].page_numbers == [2]
    assert all(chunk.chunk_hash for chunk in chunks)
