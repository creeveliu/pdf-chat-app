# Streaming Answer Design

**Status:** Implemented on 2026-03-21

**Goal:** Add answer streaming to the existing PDF chat flow so the frontend can render assistant text incrementally while preserving the current `document_id` scoping, retrieval behavior, and citation metadata.

## Context

The current product already supports:
- PDF upload and deduplicated indexing
- scoped question answering by `document_id`
- chat-style rendering with assistant citations and source contexts

The missing piece is response streaming. Today the frontend waits for the full `/ask` JSON body before rendering the assistant reply, which makes long answers feel stalled.

## Approaches Considered

### Option A: Replace `/ask` with a streaming response

Pros:
- single API surface

Cons:
- breaks the current JSON contract
- forces frontend and tests to migrate at once
- makes compatibility and rollback harder

### Option B: Add a parallel `/ask/stream` SSE endpoint

Pros:
- preserves the current `/ask` behavior
- keeps the protocol explicit
- lets the frontend adopt streaming incrementally
- fits well with progressive text deltas plus a final metadata payload

Cons:
- maintains two answer endpoints

### Option C: Stream plain text only and fetch citations separately

Pros:
- very small backend change

Cons:
- splits one logical answer over two requests
- makes error handling and UI state more awkward
- delays citations until a second round trip

## Decision

Use **Option B**: add `POST /ask/stream` that returns Server-Sent Events.

This keeps existing clients working and gives the frontend one continuous stream with:
- `start` event for message metadata
- `delta` events for incremental answer text
- `done` event for final `answer`, `contexts`, `citations`, and `top_k`
- `error` event for recoverable service errors surfaced after the stream starts

## Backend Design

- Keep HTTP handling in `backend/app/routes/ask.py`.
- Keep orchestration in `backend/app/services/qa_service.py`.
- Extend `backend/app/services/llm.py` with a streaming generator built on the OpenAI-compatible client.
- Reuse the current retrieval and citation-building flow so `document_id`, dedupe, and citation metadata stay unchanged.

Planned service split:
- `ask_question(...)` remains for synchronous `/ask`
- `stream_question(...)` performs validation, retrieval, and yields structured stream events

The stream contract will be newline-delimited SSE frames:

```text
event: start
data: {"question":"...","top_k":3}

event: delta
data: {"delta":"第一段"}

event: done
data: {"question":"...","answer":"完整答案","contexts":[...],"citations":[...],"top_k":3}
```

## Frontend Design

- Keep API helpers in `frontend/src/lib/api.ts`.
- Add a streaming helper that reads the SSE response body with `ReadableStream`.
- Keep page orchestration in `frontend/src/app/page.tsx`.
- Preserve the existing chat message model, adding only a small `isStreaming` flag for assistant messages.

UI flow:
1. User sends a question.
2. The page appends the user message and an empty assistant placeholder.
3. Each `delta` event updates that assistant message in place.
4. The `done` event fills in citations and contexts and clears the streaming state.
5. Errors append a system message and remove or finalize the placeholder safely.

## Error Handling

- Validation and document selection failures should still return normal HTTP errors before the stream begins.
- Errors after the stream starts should emit an `error` event with a user-safe message.
- If the frontend receives malformed SSE data or the connection closes before `done`, it should surface a clear failure state instead of pretending the answer completed.

## Testing

Backend:
- add endpoint tests for `POST /ask/stream`
- verify event order and final payload
- verify question validation and document scoping still work

Frontend:
- add API tests for SSE parsing
- add UI tests that confirm assistant content updates progressively and ends with citations

## Non-Goals

- Do not change upload or indexing behavior
- Do not introduce cross-document retrieval
- Do not redesign the chat layout beyond the states needed for streaming

## Result

The repository now includes:
- `POST /ask/stream` SSE support with `start`, `delta`, `done`, and `error` events
- frontend streaming rendering with incremental assistant message updates
- final citation/context hydration from the stream `done` payload
- auto-follow chat scrolling that re-enables on send and yields to manual user scrolling
