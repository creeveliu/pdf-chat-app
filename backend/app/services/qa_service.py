from __future__ import annotations

from dataclasses import dataclass

from app.services import llm, retrieval


@dataclass
class AskResponse:
    question: str
    answer: str
    contexts: list[dict[str, object]]
    citations: list[dict[str, object]]
    top_k: int


class QuestionValidationError(ValueError):
    pass


def build_citations(contexts: list[dict[str, object]]) -> list[dict[str, object]]:
    citations: list[dict[str, object]] = []

    for context in contexts:
        page_numbers = context.get("page_numbers")
        normalized_page_numbers = (
            [int(page_number) for page_number in page_numbers]
            if isinstance(page_numbers, list)
            else []
        )
        citations.append(
            {
                "document_id": context["document_id"],
                "filename": context["filename"],
                "chunk_id": context["chunk_id"],
                "chunk_index": context["chunk_index"],
                "page_number": context.get("page_number"),
                "page_numbers": normalized_page_numbers,
            }
        )

    return citations


def ask_question(question: str, top_k: int = 3, document_id: str | None = None) -> AskResponse:
    normalized_question = question.strip()
    if not normalized_question:
        raise QuestionValidationError("Question cannot be empty.")

    if top_k <= 0:
        raise QuestionValidationError("top_k must be greater than 0.")

    retrieved = retrieval.retrieve_contexts(
        normalized_question,
        top_k=top_k,
        document_id=document_id,
    )
    contexts = [
        {
            "document_id": item.document_id,
            "filename": item.filename,
            "chunk_id": item.chunk_id,
            "chunk_index": item.chunk_index,
            "page_number": item.page_number,
            "page_numbers": item.page_numbers,
            "chunk_hash": item.chunk_hash,
            "text": item.text,
            "score": item.score,
        }
        for item in retrieved
    ]
    answer = llm.generate_answer(normalized_question, contexts)
    citations = build_citations(contexts)

    return AskResponse(
        question=normalized_question,
        answer=answer,
        contexts=contexts,
        citations=citations,
        top_k=top_k,
    )
