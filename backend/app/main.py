import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routes.upload import router as upload_router

logging.basicConfig(level=logging.INFO)
load_dotenv()

app = FastAPI(
    title="PDF Chat API",
    description="Backend service for uploading PDFs and asking AI questions.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)


@app.get("/")
async def read_root() -> dict[str, str]:
    return {"message": "PDF Chat API is running."}


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
