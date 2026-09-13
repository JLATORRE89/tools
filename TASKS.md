# tools Task Notes

Per-task start and finish notes for this specific project live here so `AGENTS.md` can stay focused on stable guidance.

## Project Context
- Directory: `C:\projects\tools`
- Summary: Project workspace for tools.
- Main working areas: `.claude`, `.git`, `PPSM`, `business`, `cache_detector`, `fail2ban`

## Usage
- Add an `in progress` note before substantial investigation, edits, or command execution.
- Add a `completed` note when the task is done, including outcome, verification, and any remaining caveats.
- Keep entries concise and specific enough for another agent to resume work without re-reading the whole repo.

## Current Session
- No project-specific task notes recorded yet.

- 2026-09-09T16:35:37-04:00 ? in progress: Copy the shared Cloudflare DNS skill into `AIskill/SKILL.md`.
- 2026-09-09T16:35:37-04:00 ? completed: Created `AIskill/SKILL.md`; verified byte-for-byte equality with the original skill. Original retained. Documentation-only change; no runtime tests needed.

- 2026-09-09T16:36:34-04:00 - in progress: Organize the DNS skill under `AI-Skills/shared-cloudflare-dns/SKILL.md`.
- 2026-09-09T16:36:34-04:00 - completed: Renamed and moved `AIskill` to `AI-Skills/shared-cloudflare-dns`. Verified the skill content is unchanged and the old folder is gone.

- 2026-09-09T16:48:14-04:00 - in progress: Move the DNS skill to the requested `AI-Skills/cloudflare/dnsSKILL.md` path.
- 2026-09-09T16:48:14-04:00 - completed: Moved the skill to `AI-Skills/cloudflare/dnsSKILL.md`, removed the empty former folder, and verified the contents are unchanged.

- 2026-09-09T21:38:07-04:00 - in progress: Add a vendor skill catalog and on-demand loading guidance to project AGENTS.md files. Preserve the DNS skill and existing project instructions.
- 2026-09-09T21:39:26-04:00 - completed: Added the AI-Skills catalog and on-demand loading guidance to 114 project-root AGENTS.md files. DNS references now use `AI-Skills/cloudflare/dnsSKILL.md`. Verified every reference, exact intended edits, and unchanged DNS skill content. Original project instructions backed up in `C:\scratch\shared-skills-project-instructions-20260909.json`. Documentation-only validation; no agent run or DNS action performed.

- 2026-09-09T21:54:07-04:00 - in progress: Create the shared skill catalog on localnet, adapt DNS references for Linux, and configure local agent discovery.
- 2026-09-09T21:55:40-04:00 - completed: Installed and verified `/ai/tools/AI-Skills` on localnet, including Linux DNS guidance and Jason's Claude/Codex catalog references. Documented setup in `AI-Skills/LOCALNET.md`. Skill validation and all local links passed. DNS operator SSH alias remains unavailable on localnet; automatic sync is not configured.

- 2026-09-09T22:02:53-04:00 - in progress: Configure dedicated localnet SSH access to the existing DNS operator and automatic Windows-to-localnet skill catalog synchronization.
- 2026-09-09T22:14:11-04:00 - completed: Dedicated localnet-to-emailreseller SSH connection verified; read-only Cloudflare zone access returned HTTP 200 with the existing token retained on the operator server. Added automatic catalog sender/receiver and Windows scheduled task (15 minutes plus login, hidden, Interactive). All 10 tests passed on Linux; first live sync and actual scheduled execution succeeded (LastTaskResult 0); repeated sync made no document changes. Backups, conflict handling, Linux path adaptation, and operating instructions documented in `AI-Skills/LOCALNET.md`. No DNS records or application submissions changed.
