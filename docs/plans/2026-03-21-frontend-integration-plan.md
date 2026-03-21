# Frontend Integration Implementation Plan

**Status:** Completed on 2026-03-21

**Result:** The frontend now supports the full product flow in one page: PDF upload, upload status, indexing result display, question input, answer rendering, and cited context display. The page uses modular components, an isolated API client, environment-based backend URL configuration, and has been verified end-to-end against the running backend.

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Connect the existing Next.js frontend to the backend upload and ask APIs so users can upload a PDF, ask a question, and read the answer plus cited contexts from one page.

**Architecture:** Keep page-level orchestration in `frontend/src/app/page.tsx`, move HTTP requests into `frontend/src/lib/api.ts`, and split the interface into focused client components under `frontend/src/components/`. Use a single environment variable for the backend base URL and simple `useState`-driven local state for the product flow.

**Tech Stack:** Next.js App Router, React 19, TypeScript, Tailwind CSS

---

### Task 1: Build API and UI structure

**Files:**
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/components/UploadPanel.tsx`
- Create: `frontend/src/components/QuestionPanel.tsx`
- Create: `frontend/src/components/AnswerPanel.tsx`
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/app/globals.css`
- Create: `frontend/.env.example`

**Step 1: Implement minimal component boundaries**

Create:
- upload panel for file selection, upload action, and upload metadata
- question panel for text input and ask action
- answer panel for answer text, contexts, and errors

**Step 2: Connect API client**

Add wrappers for:
- `POST /upload`
- `POST /ask`

**Step 3: Verify with lint/build**

Run:
- `cd frontend && npm run lint`
- `cd frontend && npm run build`

### Task 2: Verify end-to-end in browser

**Files:**
- No additional files required

**Step 1: Start backend and frontend**

Run local servers.

**Step 2: Upload a real PDF and ask a question**

Verify:
- upload status transitions render
- ask state renders
- answer and contexts show up
