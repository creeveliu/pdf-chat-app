from __future__ import annotations

from dataclasses import dataclass
import logging
import math
import os
from typing import Callable, Iterable

from openai import OpenAI


logger = logging.getLogger(__name__)

BATCH_SIZE = 100
DASHSCOPE_BATCH_SIZE = 10
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


class EmbeddingServiceError(RuntimeError):
    pass


@dataclass(frozen=True)
class EmbeddingSettings:
    provider: str
    api_key: str
    base_url: str | None
    model: str


def _batched(items: list[str], batch_size: int) -> Iterable[list[str]]:
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


def get_embedding_settings() -> EmbeddingSettings:
    provider = os.getenv("EMBEDDING_PROVIDER", "openai").strip().lower()

    if provider in {"dashscope", "aliyun", "bailian"}:
        api_key = os.getenv("EMBEDDING_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
        base_url = os.getenv("EMBEDDING_BASE_URL") or DASHSCOPE_BASE_URL
        model = os.getenv("EMBEDDING_MODEL", "text-embedding-v4")
        resolved_provider = "dashscope"
    else:
        api_key = os.getenv("EMBEDDING_API_KEY") or os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("EMBEDDING_BASE_URL")
        model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        resolved_provider = "openai"

    if not api_key:
        env_name = "DASHSCOPE_API_KEY" if resolved_provider == "dashscope" else "OPENAI_API_KEY"
        raise EmbeddingServiceError(f"缺少环境变量 {env_name}，无法生成向量。")

    return EmbeddingSettings(
        provider=resolved_provider,
        api_key=api_key,
        base_url=base_url,
        model=model,
    )


def build_embedding_client(settings: EmbeddingSettings) -> OpenAI:
    client_kwargs = {"api_key": settings.api_key}
    if settings.base_url:
        client_kwargs["base_url"] = settings.base_url
    return OpenAI(**client_kwargs)


def get_batch_size(settings: EmbeddingSettings) -> int:
    if settings.provider == "dashscope":
        return DASHSCOPE_BATCH_SIZE
    return BATCH_SIZE


def generate_embeddings(
    chunks: list[str],
    progress_callback: Callable[[dict[str, int]], None] | None = None,
) -> list[list[float]]:
    if not chunks:
        return []

    settings = get_embedding_settings()

    logger.info(
        "Generating embeddings for %s chunks with provider=%s model=%s",
        len(chunks),
        settings.provider,
        settings.model,
    )

    try:
        client = build_embedding_client(settings)
        embeddings: list[list[float]] = []
        batch_size = get_batch_size(settings)
        total_batches = math.ceil(len(chunks) / batch_size)

        for batch_index, batch in enumerate(_batched(chunks, batch_size), start=1):
            response = client.embeddings.create(
                input=batch,
                model=settings.model,
            )
            embeddings.extend(item.embedding for item in response.data)
            if progress_callback is not None:
                progress_callback(
                    {
                        "current_batch": batch_index,
                        "total_batches": total_batches,
                        "completed_chunks": len(embeddings),
                        "total_chunks": len(chunks),
                    }
                )
    except Exception as exc:
        logger.exception("Embedding request failed for provider=%s", settings.provider)
        raise EmbeddingServiceError(
            f"调用 {settings.provider} 生成向量失败。"
        ) from exc

    logger.info("Generated %s embeddings", len(embeddings))
    return embeddings


def generate_embeddings_with_progress(
    chunks: list[str],
    progress_callback: Callable[[dict[str, int]], None] | None = None,
) -> list[list[float]]:
    return generate_embeddings(chunks, progress_callback=progress_callback)
