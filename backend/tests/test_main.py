from app import main


def test_build_allowed_origins_includes_local_defaults(monkeypatch) -> None:
    monkeypatch.delenv("FRONTEND_URL", raising=False)
    monkeypatch.delenv("VERCEL_FRONTEND_URL", raising=False)
    monkeypatch.delenv("CORS_ALLOW_ORIGINS", raising=False)

    origins = main.build_allowed_origins()

    assert origins == [
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ]


def test_build_allowed_origins_merges_frontend_envs(monkeypatch) -> None:
    monkeypatch.setenv("FRONTEND_URL", "https://pdf-chat-with.vercel.app/")
    monkeypatch.setenv("VERCEL_FRONTEND_URL", "https://pdf-chat-git-main-cl.vercel.app")
    monkeypatch.setenv(
        "CORS_ALLOW_ORIGINS",
        "https://staging.example.com, https://preview.example.com/ ",
    )

    origins = main.build_allowed_origins()

    assert origins == [
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "https://pdf-chat-git-main-cl.vercel.app",
        "https://pdf-chat-with.vercel.app",
        "https://preview.example.com",
        "https://staging.example.com",
    ]


def test_build_allow_origin_regex_reads_optional_env(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ALLOW_ORIGIN_REGEX", r"https://pdf-chat-.*\.vercel\.app")

    assert main.build_allow_origin_regex() == r"https://pdf-chat-.*\.vercel\.app"
