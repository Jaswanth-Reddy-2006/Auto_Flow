# PROJECT ROADMAP (ROADMAP.md) - AutoFlow Cognitive Assistant

## 🗺️ High-Level Plan
The goal is to stabilize the current "AutoFlow" system by removing flaky voice features while reinforcing its core automation engine.

---

### 🛡️ Phase 1: Stabilization & Voice Removal
**Goal**: Remove all voice/mic dependencies and UI components to focus on core stability.
**Status**: 🔵 DONE

- [x] **Remove Voice Dependencies**:
    - [x] Uninstall `vosk` and `sounddevice` from `requirements.txt`.
    - [x] Delete `setup_vosk.py` and remove `vosk_model/`.
- [x] **Backend Code Refactor**:
    - [x] Remove `vosk` imports and audio configuration from `main.py`.
    - [x] Remove `/start_voice` and `/stop_voice` endpoints.
    - [x] Remove `audio_callback` and `record_audio_loop`.
- [x] **Frontend Code Refactor**:
    - [x] Remove Microphone/Voice UI buttons from the React frontend.
    - [x] Update state management to remove recording flags.
- [x] **GSD Methodology Rollout**:
    - [x] Initialize `.gsd/` folder (SPEC, ROADMAP, ARCHITECTURE).
    - [x] Finalize `SPEC.md`.

### 🏗️ Phase 2: Core Task Robustness
**Goal**: Improve the agent's ability to handle complex desktop and web tasks reliably.
**Status**: 🔵 DONE

- [ ] **Improved Search-First Logic**:
    - [ ] Implement `action_search` tool for more precise web content extraction.
    - [ ] Refine `action_web_inspector` for better "read" functionality.
- [ ] **File System Hardening**:
    - [ ] Improve `action_find_file` and `action_write_file` for multi-directory support.
- [ ] **Memory & Context Optimization**:
    - [ ] Refine `ConversationBufferWindowMemory` for better long-term task awareness.

### 🚀 Phase 3: Extension & Orchestration
**Goal**: Enable high-level "deploy my platform" style tasks.

- [ ] **Git & CLI Tools**:
    - [ ] Add `action_run_command` (safe, restricted) for CLI-based tasks (git push, npm build).
- [ ] **App-Specific Automations**:
    - [ ] Better handlers for WhatsApp Web, Outlook, and Office apps.

---

## 📊 Phase 3 Progress
- **Total Tasks**: 5
- **Completed**: 1 (CLI Tool Added)
- **Status**: 🟢 IN PROGRESS

**Current Phase**: Phase 3
**Last Milestone**: Phase 2 Complete
**Next Target**: Git & CLI Orchestration

---
**Status: UPDATED**
**Date: 2026-03-28**
