# Streaming Answer Implementation Plan

**Status:** Completed on 2026-03-21

**Result:** The backend now exposes a compatible `POST /ask/stream` SSE endpoint, and the frontend consumes it to render assistant responses incrementally while preserving final citations and contexts. The chat layout was also tightened so the message area shows more content, the composer uses a light visual treatment, and scroll behavior follows new answers until the user manually intervenes.

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a new streaming ask endpoint and connect the chat UI so assistant answers render incrementally before citations arrive.

**Architecture:** Keep the existing synchronous `/ask` endpoint untouched and add a parallel SSE endpoint at `POST /ask/stream`. Reuse current validation, retrieval, and citation assembly in the QA service, extend the LLM service with a streaming generator, and parse SSE on the frontend so one assistant message is updated in place until the final metadata arrives.

**Tech Stack:** FastAPI, OpenAI-compatible Python SDK, pytest, Next.js App Router, React 19, TypeScript, Vitest

---

### Task 1: Add backend streaming tests

**Files:**
- Modify: `backend/tests/test_ask.py`

**Step 1: Write the failing tests**

Add tests for:
- `POST /ask/stream` returning SSE frames in `start -> delta -> done` order
- final `done` payload containing `answer`, `contexts`, `citations`, and `top_k`
- standard HTTP `400` behavior when the question is empty

**Step 2: Run test to verify it fails**

Run: `backend/.venv/bin/pytest backend/tests/test_ask.py -v`
Expected: FAIL because `/ask/stream` does not exist yet.

### Task 2: Implement backend streaming flow

**Files:**
- Modify: `backend/app/routes/ask.py`
- Modify: `backend/app/services/qa_service.py`
- Modify: `backend/app/services/llm.py`

**Step 1: Write minimal implementation**

Implement:
- an LLM text stream generator
- a QA stream generator that validates input, retrieves contexts once, emits deltas, and finishes with final payload metadata
- a FastAPI streaming route returning `text/event-stream`

**Step 2: Run backend tests**

Run: `backend/.venv/bin/pytest backend/tests/test_ask.py -v`
Expected: PASS

### Task 3: Add frontend streaming tests

**Files:**
- Modify: `frontend/src/components/ChatMessageList.test.tsx`
- Create: `frontend/src/lib/api.test.ts`

**Step 1: Write the failing tests**

Add tests for:
- SSE parsing in the API helper
- assistant placeholder content updating over multiple deltas
- final assistant message showing citations after stream completion

**Step 2: Run frontend tests to verify they fail**

Run: `cd frontend && npm run test -- --run`
Expected: FAIL because no streaming helper or progressive UI exists yet.

### Task 4: Implement frontend streaming flow

**Files:**
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/types/chat.ts`
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/components/ChatMessageList.tsx`

**Step 1: Write minimal implementation**

Implement:
- an SSE parser around `fetch`
- typed stream events and final payload
- assistant placeholder message updates during `delta`
- a streaming status state in the chat list

**Step 2: Run frontend tests**

Run: `cd frontend && npm run test -- --run`
Expected: PASS

### Task 5: Verify the full slice

**Files:**
- No additional files required

**Step 1: Run targeted verification**

Run:
- `backend/.venv/bin/pytest backend/tests/test_ask.py -v`
- `cd frontend && npm run test -- --run`
- `cd frontend && npm run lint`

Expected: PASS
