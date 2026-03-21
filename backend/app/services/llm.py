from __future__ import annotations

from dataclasses import dataclass
import logging
import os

from openai import OpenAI


logger = logging.getLogger(__name__)

DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
FALLBACK_ANSWER = "我无法从当前 PDF 中找到答案。"


class LlmServiceError(RuntimeError):
    pass


@dataclass(frozen=True)
class LlmSettings:
    provider: str
    api_key: str
    base_url: str | None
    model: str


def get_llm_settings() -> LlmSettings:
    provider = os.getenv("LLM_PROVIDER") or os.getenv("EMBEDDING_PROVIDER", "openai")
    provider = provider.strip().lower()

    if provider in {"dashscope", "aliyun", "bailian"}:
        api_key = os.getenv("LLM_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
        base_url = os.getenv("LLM_BASE_URL") or DASHSCOPE_BASE_URL
        model = os.getenv("LLM_MODEL", "qwen-plus")
        resolved_provider = "dashscope"
    else:
        api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL")
        model = os.getenv("LLM_MODEL", "gpt-4.1-mini")
        resolved_provider = "openai"

    if not api_key:
        env_name = "DASHSCOPE_API_KEY" if resolved_provider == "dashscope" else "OPENAI_API_KEY"
        raise LlmServiceError(f"{env_name} is required to generate answers.")

    return LlmSettings(
        provider=resolved_provider,
        api_key=api_key,
        base_url=base_url,
        model=model,
    )


def build_llm_client(settings: LlmSettings) -> OpenAI:
    client_kwargs = {"api_key": settings.api_key}
    if settings.base_url:
        client_kwargs["base_url"] = settings.base_url
    return OpenAI(**client_kwargs)


def generate_answer(question: str, contexts: list[dict[str, object]]) -> str:
    if not contexts:
        return FALLBACK_ANSWER

    settings = get_llm_settings()
    logger.info("Generating answer with provider=%s model=%s", settings.provider, settings.model)

    context_text = "\n\n".join(
        f"[{index + 1}] {context['filename']}#{context['chunk_id']}\n{context['text']}"
        for index, context in enumerate(contexts)
    )

    system_prompt = (
        "你是一个严格基于 PDF 内容回答问题的助手。"
        "你只能依据提供的上下文回答。"
        "如果上下文无法支持答案，必须明确回答：我无法从当前 PDF 中找到答案。"
        "不要编造，不要补充上下文之外的信息。"
    )
    user_prompt = f"问题：{question}\n\n可用上下文：\n{context_text}"

    try:
        client = build_llm_client(settings)
        response = client.chat.completions.create(
            model=settings.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )
        answer = (response.choices[0].message.content or "").strip()
    except Exception as exc:
        logger.exception("LLM request failed for provider=%s", settings.provider)
        raise LlmServiceError(f"Failed to generate answer from {settings.provider}.") from exc

    return answer or FALLBACK_ANSWER
