# PROJECT SPECIFICATION (SPEC.md) - AutoFlow Cognitive Assistant

## 🎯 Vision
**AutoFlow** is a private, local-first personal assistant designed for Windows. It provides a precision automation layer for high-impact desktop tasks (browsing, file management, app automation) without sending data to external cloud services. It is powered by local LLMs (Ollama/Llama 3) and aims for zero-latency, high-reliability execution.

## 👥 Target Audience
-   **Solo developers** using AI coding assistants who need consistency in their local workflows.
-   **Privacy-conscious users** who want an AI agent that monitors and automates their desktop without cloud dependencies.
-   **Power users** who need cross-app automation (Browser, File System, Office Apps).

## 🛠️ Tech Stack (Current)
-   **Backend**: Python (FastAPI).
-   **Agent Architecture**: LangChain + Structured Tool Calling.
-   **Local LLM**: Ollama (Llama 3 8B).
-   **Browser Automation**: Playwright (Async).
-   **Frontend**: Vite + Electron (Desktop wrapper).

## 🚫 Key Constraints & Rules
-   **LOCAL FIRST**: All AI processing must happen locally (Ollama).
-   **DATA HYGIENE**: Remove all unnecessary intermediate files/folders (screenshots, temp data) after task completion.
-   **STABILITY OVER FEATURES**: Prioritize robust execution of a few core tasks over a wide range of flaky features.
-   **NO VOICE (FOR NOW)**: Per user request, the voice and mic features are to be removed to stabilize the core automation loop.

## 🚀 Key Features (Phases)
### Phase 1: Stabilization & Voice Removal (Current Phase)
-   Remove all `vosk` and `sounddevice` dependencies.
-   Decommission voice-related endpoints in the backend (`/start_voice`, `/stop_voice`).
-   Remove voice/mic UI components from the frontend.
-   Implement the **GSD methodology** for all future development.

### Phase 2: Core Task Robustness
-   Improve agent reliability for browser navigation and file finding.
-   Implement a better "Search-First" content fetching system.

### Phase 3: Deployment & App Orchestration
-   Extend the agent's capability to "deploy platforms" (e.g., git push, triggering builds).
-   Ensure safe and reliable cross-app execution.

## ✅ Success Criteria
-   Zero "vosk" or "sounddevice" references in the codebase.
-   The UI only accepts text input and displays structured AI output.
-   Agent can successfully perform multi-step web and file tasks with high accuracy.
-   All development follows the GSD Plan-Execute-Verify loop.

---
**Status: FINALIZED**
**Date: 2026-03-28**
