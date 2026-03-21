# Ask Endpoint Implementation Plan

**Status:** Completed on 2026-03-21

**Result:** `/ask` is implemented with question validation, FAISS retrieval, grounded answer generation via the configured LLM provider, and end-to-end verification against a real indexed PDF. The current behavior scopes retrieval to a specific uploaded PDF via `document_id` when multiple indexes exist.

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a backend `/ask` endpoint that retrieves relevant chunks from persisted FAISS indexes and generates an answer grounded only in uploaded PDF content.

**Architecture:** Keep HTTP handling in `backend/app/routes/ask.py`, move vector lookup into `backend/app/services/retrieval.py`, move model calls into `backend/app/services/llm.py`, and use a small orchestration service to assemble the response. When multiple persisted document indexes exist, require `document_id` so retrieval stays scoped to the intended PDF instead of silently searching across every document.

**Tech Stack:** FastAPI, FAISS, OpenAI-compatible SDK, pytest

---

### Task 1: Add failing tests

**Files:**
- Create: `backend/tests/test_ask.py`

**Step 1: Write failing tests**

Add tests for:
- empty question returns `400`
- no available index returns an explicit error
- successful ask returns `question`, `answer`, `contexts`, and `top_k`

**Step 2: Run tests**

Run: `backend/.venv/bin/pytest backend/tests/test_ask.py -v`
Expected: FAIL because the route and services do not exist yet.

### Task 2: Implement retrieval and LLM modules

**Files:**
- Create: `backend/app/services/retrieval.py`
- Create: `backend/app/services/llm.py`
- Create: `backend/app/services/qa_service.py`
- Create: `backend/app/routes/ask.py`
- Modify: `backend/app/main.py`

**Step 1: Write minimal implementation**

Implement:
- question validation
- question embedding generation
- FAISS top-k retrieval across saved indexes
- grounded answer generation using compatible chat completions

**Step 2: Run tests**

Run: `backend/.venv/bin/pytest backend/tests -v`
Expected: PASS
