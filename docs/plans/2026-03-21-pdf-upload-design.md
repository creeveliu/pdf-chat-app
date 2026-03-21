# PDF Upload Implementation Plan

**Status:** Completed on 2026-03-21

**Result:** `POST /upload` is implemented, PDF storage/parsing is wired through `backend/app/routes/` and `backend/app/services/`, tests pass, and manual HTTP verification was completed.

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a backend PDF upload endpoint that stores a PDF locally, extracts text with PyMuPDF, and returns upload metadata for later RAG work.

**Architecture:** Keep FastAPI app startup in `main.py`, move HTTP handlers into `backend/app/routes/`, and isolate PDF storage/parsing logic in `backend/app/services/`. Preserve existing health/status endpoints and add basic validation and controlled error responses.

**Tech Stack:** FastAPI, PyMuPDF, python-multipart, pytest

---

### Task 1: Add backend tests for upload behavior

**Files:**
- Create: `backend/tests/test_upload.py`
- Modify: `backend/requirements.txt`

**Step 1: Write the failing test**

Add tests for:
- uploading a valid PDF returns `filename`, `text_length`, `page_count`, `preview`
- uploading a non-PDF file returns `400`
- existing `/` and `/health` endpoints still work

**Step 2: Run test to verify it fails**

Run: `backend/.venv/bin/pytest backend/tests/test_upload.py -v`
Expected: FAIL because upload route does not exist yet and testing deps may be missing.

### Task 2: Implement PDF upload route and service

**Files:**
- Create: `backend/app/routes/__init__.py`
- Create: `backend/app/routes/upload.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/pdf_service.py`
- Modify: `backend/app/main.py`
- Create: `backend/data/uploads/.gitkeep`

**Step 1: Write minimal implementation**

Implement:
- local upload directory creation
- file type validation
- PDF save logic
- PyMuPDF parsing
- structured response payload
- controlled 4xx/5xx handling

**Step 2: Run tests to verify they pass**

Run: `backend/.venv/bin/pytest backend/tests/test_upload.py -v`
Expected: PASS

### Task 3: Verify the running app manually

**Files:**
- No new files required

**Step 1: Start backend**

Run: `backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000`

**Step 2: Exercise endpoints**

Verify:
- `GET /`
- `GET /health`
- `POST /upload`

**Step 3: Confirm output**

Ensure upload response includes parsed metadata and preview text.
