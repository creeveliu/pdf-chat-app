# Upload Progress Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Expose real upload/indexing stages so the user can see whether the app is uploading the file, parsing the PDF, generating embeddings, or finishing index persistence.

**Architecture:** Keep the existing synchronous `/upload` route intact for compatibility, and add a new `/upload/stream` route that emits SSE progress events while reusing the same PDF service pipeline. Refactor the upload service and embedding service to accept an optional progress callback, then update the frontend upload client and page state to consume staged events and render them in the existing upload panel.

**Tech Stack:** FastAPI, StreamingResponse/SSE, PyMuPDF, OpenAI-compatible embeddings, Next.js, fetch streaming, Vitest, pytest

---

### Task 1: Backend streaming upload contract

**Files:**
- Modify: `backend/tests/test_upload.py`
- Modify: `backend/app/routes/upload.py`
- Modify: `backend/app/services/pdf_service.py`

**Step 1: Write the failing test**

Add a pytest case that posts a PDF to `/upload/stream`, consumes the SSE response, and asserts it emits ordered stage events followed by a `done` payload containing the existing upload response shape.

**Step 2: Run test to verify it fails**

Run: `backend/.venv/bin/pytest backend/tests/test_upload.py -k upload_stream -v`

Expected: FAIL because `/upload/stream` does not exist yet.

**Step 3: Write minimal implementation**

Add an SSE upload route and a progress-aware upload service path that emits coarse stages:
- `upload_received`
- `parsing_pdf`
- `chunking`
- `generating_embeddings`
- `persisting_index`
- `completed`

**Step 4: Run test to verify it passes**

Run: `backend/.venv/bin/pytest backend/tests/test_upload.py -k upload_stream -v`

Expected: PASS

### Task 2: Embedding batch progress events

**Files:**
- Modify: `backend/tests/test_upload.py`
- Modify: `backend/app/services/embedding.py`
- Modify: `backend/app/services/pdf_service.py`

**Step 1: Write the failing test**

Add a backend test that stubs embedding batches and asserts the stream emits incremental embedding progress metadata such as current batch, total batches, and chunk counts.

**Step 2: Run test to verify it fails**

Run: `backend/.venv/bin/pytest backend/tests/test_upload.py -k embedding_progress -v`

Expected: FAIL because embedding progress metadata is not emitted yet.

**Step 3: Write minimal implementation**

Extend `generate_embeddings()` with an optional callback invoked once per batch and forward that into upload progress events.

**Step 4: Run test to verify it passes**

Run: `backend/.venv/bin/pytest backend/tests/test_upload.py -k embedding_progress -v`

Expected: PASS

### Task 3: Frontend upload streaming client

**Files:**
- Modify: `frontend/src/lib/api.test.ts`
- Modify: `frontend/src/lib/api.ts`

**Step 1: Write the failing test**

Add a Vitest case for a new `uploadPdfStream()` helper that parses upload SSE events, forwards progress callbacks, and returns the final upload payload.

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- src/lib/api.test.ts`

Expected: FAIL because `uploadPdfStream()` does not exist.

**Step 3: Write minimal implementation**

Implement `uploadPdfStream(file, handlers)` using `fetch()` + streamed response parsing, reusing the existing SSE parser pattern from `askQuestionStream()`.

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- src/lib/api.test.ts`

Expected: PASS

### Task 4: Frontend staged upload UI

**Files:**
- Modify: `frontend/src/app/page.test.tsx`
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/components/UploadPanel.tsx`

**Step 1: Write the failing test**

Add a page test that mocks staged upload progress and asserts the UI shows separate status text for upload, parsing, embedding, and completion instead of a single long-running “上传中...” state.

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- src/app/page.test.tsx`

Expected: FAIL because the page only calls `uploadPdf()` and shows one static upload status.

**Step 3: Write minimal implementation**

Switch the page to `uploadPdfStream()`, map backend stages to user-facing copy, and optionally show a concise detail line such as embedding batch progress.

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- src/app/page.test.tsx`

Expected: PASS

### Task 5: Full verification

**Files:**
- Modify: `backend/tests/test_upload.py` if minor expectations need alignment
- Modify: `frontend/src/app/page.test.tsx` if copy assertions need alignment

**Step 1: Run focused backend tests**

Run: `backend/.venv/bin/pytest backend/tests/test_upload.py -v`

Expected: PASS

**Step 2: Run focused frontend tests**

Run: `cd frontend && npm test -- src/lib/api.test.ts src/app/page.test.tsx`

Expected: PASS

**Step 3: Run broader regression checks**

Run: `backend/.venv/bin/pytest backend/tests/test_ask.py backend/tests/test_upload.py -v`

Run: `cd frontend && npm test -- src/components/ChatMessageList.test.tsx src/lib/api.test.ts src/app/page.test.tsx`

Expected: PASS
