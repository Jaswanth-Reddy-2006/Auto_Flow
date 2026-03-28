# CANONICAL PROJECT RULES (PROJECT_RULES.md) - AutoFlow Cognitive Assistant

## 🎯 High-Level Context
- **Project Name**: AutoFlow
- **Stack**: FastAPI, LangChain, Ollama (Llama 3 8B), Playwright, Electron (Frontend)
- **Vision**: A local-first, privacy-driven automation layer for Windows.
- **Workflow**: GSD (Get Shit Done) — Plan → Execute → Verify → Done.

## 🔒 Mandatory Rules
1.  **Local Execution**: Never send user data to external cloud APIs for processing. Use `ChatOllama` for all reasoning.
2.  **Plan Before Action**: The agent MUST show a logical plan for tasks involving more than 2 steps.
3.  **Atomic Verification**: Every change must be verified.
    -   *Web Change*: Screenshot or Scrape.
    -   *File Change*: `ls` or `action_find_file`.
    -   *App Launch*: Check if process is running (if possible) or visually verify.
4.  **Data Hygiene**:
    -   Clean `outputs/` after tasks that don't require verification persistence.
    -   Keep `.gsd/` folder updated with current project status.
5.  **No Voice/Mic**: The voice/mic functionality has been decommissioned. Any future request for voice should be handled as a separate "Phase" in the Roadmap.

## 🛠️ Code Style & Conventions
- **Naming**: Use `snake_case` for Python functions and variables.
- **Tools**: All tool implementation must include clear docstrings as LangChain uses them for selection.
- **Error Handling**: Every tool must return a descriptive error message instead of throwing an unhandled exception.

## 🗺️ GSD Methodology Structure
- `.gsd/SPEC.md`: The single source of truth for project vision.
- `.gsd/ARCHITECTURE.md`: High-level system design.
- `.gsd/ROADMAP.md`: Timeline and feature tracking.
- `.gsd/STATE.md`: Decisions, blockers, and recent changes.
- `.gsd/PLAN.md`: Atomic tasks with XML-like structure (when in planning mode).

## 💰 Token Optimization (Search-First)
- Search before reading entire web pages or files.
- Use `action_web_inspector` for cleaned text before resorting to full `action_web_scrape`.

---
**Status: FINALIZED**
**Date: 2026-03-28**
