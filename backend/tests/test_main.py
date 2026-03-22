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


def test_build_health_payload_includes_deployment_metadata(monkeypatch) -> None:
    monkeypatch.setenv("APP_VERSION", "0.2.0")
    monkeypatch.setenv("DEPLOYMENT_ENV", "production")
    monkeypatch.setenv("DEPLOYED_COMMIT_SHA", "ffafadd")
    monkeypatch.setenv("DEPLOYED_AT", "2026-03-22T11:11:11Z")

    payload = main.build_health_payload()

    assert payload == {
        "status": "ok",
        "version": "0.2.0",
        "deployment": {
            "environment": "production",
            "commit_sha": "ffafadd",
            "deployment_id": "unknown",
            "deployed_at": "2026-03-22T11:11:11Z",
        },
    }


def test_build_health_payload_prefers_railway_variables(monkeypatch) -> None:
    monkeypatch.delenv("APP_VERSION", raising=False)
    monkeypatch.delenv("DEPLOYMENT_ENV", raising=False)
    monkeypatch.delenv("DEPLOYED_COMMIT_SHA", raising=False)
    monkeypatch.delenv("DEPLOYED_AT", raising=False)
    monkeypatch.setenv("RAILWAY_ENVIRONMENT_NAME", "production")
    monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "1416e61abcdef")
    monkeypatch.setenv("RAILWAY_DEPLOYMENT_ID", "dpl_123")

    payload = main.build_health_payload()

    assert payload["deployment"] == {
        "environment": "production",
        "commit_sha": "1416e61abcdef",
        "deployment_id": "dpl_123",
        "deployed_at": payload["deployment"]["deployed_at"],
    }
    assert payload["deployment"]["deployed_at"] != "unknown"
    assert payload["deployment"]["deployed_at"].endswith("+08:00")
