---
description: Create a technical plan for the current phase or task.
---
1. Analyze the current objective and phase requirements in `.gsd/SPEC.md` and `.gsd/ROADMAP.md`.
2. Break down the work into atomic tasks (atomic = 1-2 files changed per task, verifiable result).
3. Create or update `.gsd/PLAN.md` using the XML structure:
   ```xml
   <task type="auto">
     <name>Task Name</name>
     <files>path/to/file.py</files>
     <action>Detailed instructions for the task.</action>
     <verify>Verification command (e.g., smoke test or screenshot).</verify>
     <done>Expected verifiable outcome.</done>
   </task>
   ```
4. Update `.gsd/STATE.md` to indicate the plan is ready for execution.
