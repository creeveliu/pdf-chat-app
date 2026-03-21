from __future__ import annotations

from dataclasses import dataclass

from app.services import llm, retrieval


@dataclass
class AskResponse:
    question: str
    answer: str
    contexts: list[dict[str, object]]
    top_k: int


class QuestionValidationError(ValueError):
    pass


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
            "text": item.text,
            "score": item.score,
        }
        for item in retrieved
    ]
    answer = llm.generate_answer(normalized_question, contexts)

    return AskResponse(
        question=normalized_question,
        answer=answer,
        contexts=contexts,
        top_k=top_k,
    )
