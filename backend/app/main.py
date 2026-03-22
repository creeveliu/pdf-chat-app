import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routes.ask import router as ask_router
from app.routes.upload import router as upload_router
from app.services import cleanup_service

logging.basicConfig(level=logging.INFO)
load_dotenv()

DEFAULT_ALLOWED_ORIGINS = (
    "http://127.0.0.1:3000",
    "http://localhost:3000",
)
BEIJING_TZ = timezone(timedelta(hours=8))
PROCESS_STARTED_AT = datetime.now(BEIJING_TZ).isoformat()


def _normalize_origin(origin: str) -> str:
    return origin.strip().rstrip("/")


def _split_origins(value: str | None) -> list[str]:
    if not value:
        return []

    return [
        normalized
        for item in value.split(",")
        if (normalized := _normalize_origin(item))
    ]


def build_allowed_origins() -> list[str]:
    origins = {
        _normalize_origin(origin)
        for origin in DEFAULT_ALLOWED_ORIGINS
    }

    for env_name in ("FRONTEND_URL", "VERCEL_FRONTEND_URL"):
        env_value = _normalize_origin(os.getenv(env_name, ""))
        if env_value:
            origins.add(env_value)

    origins.update(_split_origins(os.getenv("CORS_ALLOW_ORIGINS")))
    return sorted(origins)


def build_allow_origin_regex() -> str | None:
    regex = os.getenv("CORS_ALLOW_ORIGIN_REGEX", "").strip()
    return regex or None


def build_health_payload() -> dict[str, object]:
    return {
        "status": "ok",
        "version": os.getenv("APP_VERSION", app.version),
        "deployment": {
            "environment": _first_non_empty_env("DEPLOYMENT_ENV", "RAILWAY_ENVIRONMENT_NAME", "VERCEL_ENV"),
            "commit_sha": _first_non_empty_env("DEPLOYED_COMMIT_SHA", "RAILWAY_GIT_COMMIT_SHA", "VERCEL_GIT_COMMIT_SHA"),
            "deployment_id": _first_non_empty_env("RAILWAY_DEPLOYMENT_ID", "VERCEL_DEPLOYMENT_ID"),
            "deployed_at": _first_non_empty_env("DEPLOYED_AT", default=PROCESS_STARTED_AT),
        },
    }


def _first_non_empty_env(*names: str, default: str = "unknown") -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return default


def run_startup_cleanup() -> None:
    try:
        cleanup_service.cleanup_expired_documents()
    except Exception:
        logging.exception("Startup document cleanup failed")


@asynccontextmanager
async def lifespan(_: FastAPI):
    run_startup_cleanup()
    yield

app = FastAPI(
    title="PDF Chat API",
    description="Backend service for uploading PDFs and asking AI questions.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=build_allowed_origins(),
    allow_origin_regex=build_allow_origin_regex(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(ask_router)


@app.get("/")
async def read_root() -> dict[str, str]:
    return {"message": "PDF Chat API is running."}


@app.get("/health")
async def healthcheck() -> dict[str, object]:
    return build_health_payload()
