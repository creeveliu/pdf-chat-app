from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.llm import LlmServiceError
from app.services.qa_service import AskResponse, QuestionValidationError, ask_question
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
    top_k: int


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
    except LlmServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return AskResponseModel(**result.__dict__)
