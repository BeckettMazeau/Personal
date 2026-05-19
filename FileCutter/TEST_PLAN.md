# FileCutter Test Plan

This document outlines the testing strategy for the FileCutter application, focusing on the critical paths across the Backend, Frontend, and End-to-End (E2E) flows.

## 1. Backend Critical Paths
**Goal:** Ensure data integrity, correct triaging logic, AI evaluation stability, and strict adherence to safety protocols during file deletion.

*   **File Assessment (Tier 1 & 2):**
    *   Verify that `file_service.scan_directory` correctly identifies files, extracts metadata (size, creation date), and applies static rules (e.g., scoring `.exe`, `.msi` as 3).
    *   Verify that `ai_orchestrator.tier_1_evaluation` processes filename batches and correctly parses the LLM JSON response.
    *   Verify that `ai_orchestrator.tier_2_evaluation` correctly extracts text from documents (PDF, PPTX) and honors static text rules (e.g., "homework", "report" yield score 1).
    *   Verify robust error handling (timeouts, invalid JSON) when interacting with the local LM Studio instance.
*   **Deletion Logic (Safety Locks):**
    *   **CRITICAL:** Ensure `SecureDeletionManager.delete_files` ONLY uses `send2trash`.
    *   Verify that deletions fail if the provided `confirmation_token` does not match the `SERVER_SIDE_SECRET`.
    *   Verify that nonexistent files or invalid paths are safely skipped without throwing unhandled exceptions.
*   **Cache Integrity:**
    *   Verify that `AIOrchestrator` correctly calculates file hashes and retrieves previous assessments from the SQLite cache (`file_cache.db`).
    *   Verify that new assessments are properly inserted or replaced in the cache.

## 2. Frontend Critical Paths
**Goal:** Ensure the user interface is responsive, correctly reflects backend state, and provides smooth, accessible interactions for large file lists.

*   **Component Rendering:**
    *   Verify the `VirtualizedFileList` correctly renders list items and formats data (e.g., file sizes, confidence colors).
    *   Verify the `PreviewPane` handles different file types (images, PDFs) and displays appropriate fallbacks for unsupported types.
*   **Keyboard Navigation & Interaction:**
    *   Verify `ArrowDown` and `ArrowUp` keys successfully navigate the file list and update the active preview.
    *   Verify the `Space` key toggles the selection state of the currently active file.
    *   Verify the `Escape` key clears the current preview.
*   **Selection Logic:**
    *   Verify the "Quick Select" buttons (e.g., "All Level 3") accurately select the intended group of files.
    *   Verify the "Clear Selection" button deselects all items.
*   **Modal Behavior:**
    *   Verify the `SafetyLockModal` only allows confirmation when the exact string "DELETE" is typed.
    *   Verify the "Execute Cleanup" button is disabled if 0 files are selected.

## 3. E2E Critical Paths
**Goal:** Verify the complete integration of the frontend, backend, and simulated file system.

*   **Full Flow (Directory Scan to Confirmed Deletion):**
    *   Launch the backend and frontend servers.
    *   Simulate loading the initial file list (mocked via Playwright intercepts or real API calls).
    *   Interact with the UI to select files (using quick select or manual selection).
    *   Trigger the cleanup execution flow.
    *   Complete the safety lock modal.
    *   Verify the UI reflects the successful cleanup (alert dialog and cleared selection).
