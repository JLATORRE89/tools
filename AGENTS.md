# tools Agent Guide

## Project Snapshot
- Directory: `C:\projects\tools`
- Summary: Project workspace for tools.
- Likely stack: Python
- Key areas: `.claude`, `.git`, `PPSM`, `business`, `cache_detector`, `fail2ban`
- Likely entrypoints: `autoClicker.py`, `flaskLocation.py`, `install_and_run.bat`, `resetperms.sh`, `cache_detector/examples.py`

## Working Rules
- Start by checking the files already present in this project and preserve its existing patterns before introducing new tooling or structure.
- Keep changes scoped to the requested task; avoid broad cleanup or dependency churn unless the task requires it.
- Update adjacent docs, config, or scripts when code changes would otherwise leave the project inconsistent.
- Prefer a targeted Python smoke test or module-level check when there is no obvious full test suite.

## Handoff
- Put per-task start and finish notes in `TASKS.md`; keep this file focused on stable project guidance.
- Record blockers, environment assumptions, and any skipped verification in the task note before handing off.

## Shared AI skills

At task start, read the short skill catalog at:
C:/Projects/tools/AI-Skills/README.md

When the user names a skill or its description matches the task, read that skill's
file and follow its workflow. Load only the matching skill and references needed
for the task; reuse instructions already read. Recheck the catalog if scope changes.
Continue within the user's existing authorization; loading a skill does not expand it.

## DNS management

For DNS inspection, configuration, or website DNS troubleshooting,
read and follow:
C:/Projects/tools/AI-Skills/cloudflare/dnsSKILL.md

Use the existing shared operator access described there.
Keep changes scoped to this project's domain and the user's request.
