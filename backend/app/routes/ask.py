import json

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services.cleanup_service import DocumentExpiredError
from app.services.llm import LlmServiceError
from app.services.qa_service import AskResponse, QuestionValidationError, ask_question, stream_question
from app.services.retrieval import DocumentSelectionError, RetrievalError


router = APIRouter()


class AskRequest(BaseModel):
    question: str
    document_id: str | None = None
    top_k: int = Field(default=3, ge=1, le=10)


class AskResponseModel(BaseModel):
    question: str
    answer: str
    contexts: list[dict[str, object]]
    citations: list[dict[str, object]]
    top_k: int


def format_sse_event(event_name: str, data: dict[str, object]) -> str:
    return f"event: {event_name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/ask", response_model=AskResponseModel)
async def ask_route(payload: AskRequest) -> AskResponseModel:
    try:
        result: AskResponse = ask_question(
            payload.question,
            top_k=payload.top_k,
            document_id=payload.document_id,
        )
    except QuestionValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except DocumentSelectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RetrievalError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except DocumentExpiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except LlmServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return AskResponseModel(**result.__dict__)


@router.post("/ask/stream")
async def ask_stream_route(payload: AskRequest) -> StreamingResponse:
    try:
        event_stream = stream_question(
            payload.question,
            top_k=payload.top_k,
            document_id=payload.document_id,
        )
    except QuestionValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except DocumentSelectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RetrievalError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except DocumentExpiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except LlmServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    def _generate():
        try:
            for event in event_stream:
                yield format_sse_event(event.type, event.data)
        except LlmServiceError as exc:
            yield format_sse_event("error", {"detail": str(exc)})

    return StreamingResponse(_generate(), media_type="text/event-stream")
