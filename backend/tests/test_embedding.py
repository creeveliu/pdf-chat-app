from app.services import embedding


def test_dashscope_settings_use_compatible_openai_endpoint(monkeypatch) -> None:
    monkeypatch.setenv("EMBEDDING_PROVIDER", "dashscope")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "dashscope-test-key")
    monkeypatch.delenv("EMBEDDING_API_KEY", raising=False)
    monkeypatch.delenv("EMBEDDING_BASE_URL", raising=False)
    monkeypatch.delenv("EMBEDDING_MODEL", raising=False)

    settings = embedding.get_embedding_settings()

    assert settings.provider == "dashscope"
    assert settings.api_key == "dashscope-test-key"
    assert settings.base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert settings.model == "text-embedding-v4"


def test_generate_embeddings_uses_configured_client(monkeypatch) -> None:
    monkeypatch.setenv("EMBEDDING_PROVIDER", "dashscope")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "dashscope-test-key")
    monkeypatch.setenv("EMBEDDING_MODEL", "text-embedding-v4")

    captured: dict[str, object] = {}

    class FakeEmbeddingsApi:
        def create(self, *, input, model):
            captured["input"] = input
            captured["model"] = model
            return type(
                "EmbeddingResponse",
                (),
                {
                    "data": [
                        type("EmbeddingData", (), {"embedding": [0.1, 0.2, 0.3]})(),
                        type("EmbeddingData", (), {"embedding": [0.4, 0.5, 0.6]})(),
                    ]
                },
            )()

    class FakeOpenAI:
        def __init__(self, *, api_key, base_url):
            captured["api_key"] = api_key
            captured["base_url"] = base_url
            self.embeddings = FakeEmbeddingsApi()

    monkeypatch.setattr(embedding, "OpenAI", FakeOpenAI)

    vectors = embedding.generate_embeddings(["chunk-a", "chunk-b"])

    assert captured["api_key"] == "dashscope-test-key"
    assert captured["base_url"] == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert captured["model"] == "text-embedding-v4"
    assert captured["input"] == ["chunk-a", "chunk-b"]
    assert vectors == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]


def test_dashscope_batch_size_is_limited() -> None:
    settings = embedding.EmbeddingSettings(
        provider="dashscope",
        api_key="dashscope-test-key",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="text-embedding-v4",
    )

    assert embedding.get_batch_size(settings) == 10
