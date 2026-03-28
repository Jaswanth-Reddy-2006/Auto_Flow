---
description: Map the current codebase architecture and dependencies.
---
1. Run `action_run_command` with `tree /f` or use `list_dir` recursively to map the project.
2. Identify core components (Backend, Frontend, Agent, Tools, State).
3. Update or generate `.gsd/ARCHITECTURE.md` with a fresh mermaid diagram and component breakdown.
4. Ensure all new files are tracked and logically grouped.
5. Identify any "unnecessary data" (leftover tests, temp files) and flag for deletion.
6. Verify against `.gsd/SPEC.md` for architectural alignment.
