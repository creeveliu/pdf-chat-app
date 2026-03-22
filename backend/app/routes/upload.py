import json
import queue
import threading

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.document_registry import DocumentRegistryError
from app.services.embedding import EmbeddingServiceError
from app.services.pdf_service import (
    PdfProcessingError,
    PdfUploadResponse,
    StorageError,
    ValidationError,
    process_pdf_upload,
    save_and_parse_pdf,
)
from app.services.vector_store import VectorStoreError

router = APIRouter()


def format_sse_event(event_name: str, data: dict[str, object]) -> str:
    return f"event: {event_name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


class UploadResponse(BaseModel):
    document_id: str
    already_exists: bool
    filename: str
    text_length: int
    page_count: int
    preview: str
    chunk_count: int
    embedding_count: int
    indexed_new_chunks: int
    expires_at: str | None = None


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
            detail="保存上传的 PDF 文件失败。",
        ) from exc
    except DocumentRegistryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
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


@router.post("/upload/stream")
async def upload_pdf_stream(file: UploadFile = File(...)) -> StreamingResponse:
    try:
        file_bytes = await file.read()
    except Exception as exc:  # pragma: no cover - request body errors vary
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="读取上传文件失败。",
        ) from exc

    def _generate():
        event_queue: queue.Queue[tuple[str, dict[str, object]] | None] = queue.Queue()

        def _push_event(event_name: str, data: dict[str, object]) -> None:
            event_queue.put((event_name, data))

        def _worker() -> None:
            try:
                result = process_pdf_upload(
                    file_bytes=file_bytes,
                    filename=file.filename or "",
                    content_type=file.content_type,
                    progress_callback=_push_event,
                )
                event_queue.put(("done", result.__dict__))
            except ValidationError as exc:
                event_queue.put(("error", {"detail": str(exc)}))
            except PdfProcessingError as exc:
                event_queue.put(("error", {"detail": str(exc)}))
            except StorageError:
                event_queue.put(("error", {"detail": "保存上传的 PDF 文件失败。"}))
            except DocumentRegistryError as exc:
                event_queue.put(("error", {"detail": str(exc)}))
            except EmbeddingServiceError as exc:
                event_queue.put(("error", {"detail": str(exc)}))
            except VectorStoreError as exc:
                event_queue.put(("error", {"detail": str(exc)}))
            finally:
                event_queue.put(None)

        threading.Thread(target=_worker, daemon=True).start()

        while True:
            event = event_queue.get()
            if event is None:
                break

            event_name, data = event
            yield format_sse_event(event_name, data)

    return StreamingResponse(_generate(), media_type="text/event-stream")
