# ARCHITECTURE DECISION RECORDS (DECISIONS.md)

## 💾 Decisions
- **2026-03-28: GSD Adoption**: Transitioned to the Get Shit Done (GSD) methodology for project management.
- **2026-03-28: Voice Removal**: Decommissioned `vosk` and `sounddevice` to prioritize core automation stability.
- **2026-03-28: Proactor Loop Fix**: Moved `asyncio.set_event_loop_policy` to the top of `main.py` to fix Playwright subprocess execution on Windows.
- **2026-03-28: Phase 3 Start**: Initiated "Extension & Orchestration" phase, adding `action_run_command`.
