# RAG Indexing Implementation Plan

**Status:** Completed on 2026-03-21

**Result:** `/upload` now performs parsing, chunking, embeddings, and FAISS persistence. The embedding layer supports both OpenAI and Alibaba DashScope compatible-mode configuration, and the flow has been verified with a real PDF upload.

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend the backend upload flow so each uploaded PDF is chunked, embedded with OpenAI, and persisted as a FAISS vector index plus chunk metadata.

**Architecture:** Keep `/upload` in `backend/app/routes/`, keep orchestration in `backend/app/services/pdf_service.py`, and add dedicated modules for chunking, embeddings, and vector persistence. Store each PDF's artifacts under its own directory inside `backend/data/index/` so the implementation can grow to multiple documents cleanly.

**Tech Stack:** FastAPI, PyMuPDF, OpenAI Python SDK, FAISS, pytest

---

### Task 1: Add failing tests

**Files:**
- Modify: `backend/tests/test_upload.py`
- Create: `backend/tests/test_chunking.py`
- Modify: `backend/requirements.txt`

**Step 1: Write failing tests**

Add tests for:
- chunking returns overlapping chunks within the expected size range
- upload response now includes `chunk_count` and `embedding_count`
- upload persists `faiss.index` and `chunks.json`

**Step 2: Run tests to verify failure**

Run: `backend/.venv/bin/pytest backend/tests -v`
Expected: FAIL because the new modules and response fields do not exist yet.

### Task 2: Implement service modules

**Files:**
- Create: `backend/app/services/chunking.py`
- Create: `backend/app/services/embedding.py`
- Create: `backend/app/services/vector_store.py`
- Modify: `backend/app/services/pdf_service.py`

**Step 1: Write minimal implementation**

Implement:
- chunking with overlap
- OpenAI embedding client wrapper
- FAISS persistence helpers
- per-document index directory creation

**Step 2: Run tests**

Run: `backend/.venv/bin/pytest backend/tests -v`
Expected: PASS

### Task 3: Verify with a running server

**Files:**
- Modify: `backend/app/routes/upload.py`
- Create: `backend/data/index/.gitkeep`

**Step 1: Start backend**

Run: `backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000`

**Step 2: Upload a PDF**

Run a real `curl -F file=@... http://127.0.0.1:8000/upload`

**Step 3: Confirm artifacts**

Verify a per-document directory exists under `backend/data/index/` with `faiss.index` and `chunks.json`.
