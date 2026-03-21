from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.services.embedding import EmbeddingServiceError
from app.services.pdf_service import (
    PdfProcessingError,
    PdfUploadResponse,
    StorageError,
    ValidationError,
    save_and_parse_pdf,
)
from app.services.vector_store import VectorStoreError

router = APIRouter()


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    text_length: int
    page_count: int
    preview: str
    chunk_count: int
    embedding_count: int


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)) -> UploadResponse:
    try:
        result: PdfUploadResponse = await save_and_parse_pdf(file)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except PdfProcessingError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store uploaded PDF.",
        ) from exc
    except EmbeddingServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except VectorStoreError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return UploadResponse(**result.__dict__)
