---
description: Execute atomic tasks from the current PLAN.md.
---
1. Verify that `.gsd/PLAN.md` exists and tasks are not yet completed.
2. For each task in a "Wave" (independent tasks):
   - Switch to EXECUTION mode.
   - Implement the code changes specified in the `<action>` block.
   - Commit the changes with an atomic commit message (e.g., `feat(phase-N): task name`).
3. After each task, run the `<verify>` command and capture evidence.
4. Mark the task as `[x]` in `.gsd/PLAN.md` and update `.gsd/STATE.md`.
