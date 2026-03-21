# Upload Drag And Drop Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add drag-and-drop PDF selection to the existing upload card without changing the backend upload flow or current document-scoped chat behavior.

**Architecture:** Keep the upload request flow in `frontend/src/app/page.tsx` and extend `frontend/src/components/UploadPanel.tsx` so the existing upload card becomes a drop zone. The drop action should only update the selected file and visible upload hint; actual upload continues to use the existing button and `uploadPdf` call.

**Tech Stack:** Next.js App Router, React 19, TypeScript, Vitest, Testing Library

---

### Task 1: Cover drag-and-drop selection with a failing test

**Files:**
- Modify: `frontend/src/app/page.test.tsx`

**Step 1: Write the failing test**

Add a test that renders `Home`, dispatches `dragOver`, `drop`, and `dragLeave` on the upload card, and asserts that the dropped PDF filename appears in the card.

**Step 2: Run test to verify it fails**

Run: `npm test -- --run frontend/src/app/page.test.tsx`
Expected: FAIL because the upload card does not yet respond to drag/drop events.

### Task 2: Implement upload-card drag-and-drop support

**Files:**
- Modify: `frontend/src/components/UploadPanel.tsx`
- Modify: `frontend/src/app/page.tsx`

**Step 1: Add minimal drag state and handlers**

Track whether the upload card is actively being dragged over in `page.tsx`, pass the state and handlers into `UploadPanel`, and use dropped files to call the existing `setSelectedFile`.

**Step 2: Update the upload card UI**

Make the label accept `dragOver`, `dragEnter`, `dragLeave`, and `drop`, prevent default browser navigation on valid drags, and show an active visual state plus concise helper copy.

**Step 3: Keep current upload semantics**

Do not auto-upload on drop. Preserve the existing upload button, status messaging, and backend API contract.

### Task 3: Verify behavior

**Files:**
- Test: `frontend/src/app/page.test.tsx`

**Step 1: Run targeted tests**

Run: `npm test -- --run src/app/page.test.tsx`
Expected: PASS

**Step 2: Optional wider confidence check**

Run: `npm test -- --run src/components/ChatMessageList.test.tsx src/lib/api.test.ts`
Expected: PASS
