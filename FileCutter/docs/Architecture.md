# FileCutter System Architecture

## 1. System Overview
FileCutter is a local, AI-assisted file management application designed to triage, classify, and securely clear large directories. The system relies on a strictly decoupled client-server architecture to ensure that autonomous AI development agents can operate on discrete modules without cross-contamination. All AI inference is performed locally via LM Studio to maintain data privacy and operate within hardware constraints (specifically optimized for a 12GB VRAM environment).

## 2. Core Technology Stack
* **Backend Server:** Python (FastAPI). Selected for asynchronous I/O capabilities and strict JSON schema validation via Pydantic.
* **Frontend Client:** React (Node.js). Selected for its ecosystem of virtualized list components, which are mandatory for rendering massive file directories without UI latency.
* **AI Inference Host:** LM Studio. Accessed exclusively via local HTTP REST requests.
* **File System Operations:** Native Python `os` and `shutil` modules for read operations, strictly limited to `send2trash` for all deletion operations.

## 3. Module Boundaries & Agent Responsibilities

### 3.1. Systems Engine (Backend)
* **Responsibilities:** Directory traversal, metadata extraction, hard-coded rule filtering (e.g., automatic flagging of `.exe`, `.msi`), and final execution of deletion commands.
* **Constraints:** Must operate asynchronously. Deletion logic must be contained within a single, isolated service class.

### 3.2. AI Orchestrator (Backend)
* **Responsibilities:** Prompt engineering, batch optimization, text extraction (e.g., PyMuPDF for documents), and REST communication with LM Studio.
* **Constraints:** Strictly read-only access to the file system. Must enforce structured JSON responses from the local LLM.

### 3.3. Application Interface (Frontend)
* **Responsibilities:** State management, virtualized list rendering, dynamic file previews, and user confirmation flows.
* **Constraints:** Must require explicit, multi-step user confirmation before transmitting any deletion payload to the backend.

## 4. Execution Pipeline

### Phase 1: Ingestion and Static Triaging
1.  The UI requests a directory scan.
2.  The backend asynchronously maps the target directory, extracting metadata.
3.  The static rule engine intercepts known temporary files and installers. These are immediately assigned a confidence score of 3 (Safe to Delete) without LLM intervention.

### Phase 2: Tiered AI Assessment
1.  **Tier 1 (Shallow Pass):** The AI Orchestrator batches filenames and metadata. The LLM evaluates the batch and returns an array of suggested actions and confidence scores (1-3).
2.  **Tier 2 (Deep Pass):** Files receiving an ambiguous score (<= 2) during Tier 1, specifically documents like PDFs, are passed to extraction libraries for content-based re-evaluation.

### Phase 3: State Aggregation
1.  The backend compiles the triaged lists into a unified JSON state map.
2.  The frontend consumes this payload and renders the checklist.

### Phase 4: Isolated Execution (Safety Protocol)
1.  The user reviews the flagged items and initiates the mass-deletion process.
2.  The user provides an explicit confirmation.
3.  The backend's isolated execution class verifies the confirmation and processes each file path exclusively through the `send2trash` library.
