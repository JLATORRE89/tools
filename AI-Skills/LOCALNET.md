# Localnet skill catalog

The catalog is installed on localnet and updates automatically from Windows. Its DNS skill can use the existing operator host through a dedicated SSH connection. Setup and verification completed on 2026-09-09.

## Paths and agent discovery

| Item | Path on localnet |
| --- | --- |
| Catalog | `/ai/tools/AI-Skills/README.md` |
| Cloudflare DNS skill | `/ai/tools/AI-Skills/cloudflare/dnsSKILL.md` |
| Jason's Claude Code instructions | `/home/jason/.claude/CLAUDE.md` |
| Jason's Codex instructions | `/home/jason/.codex/AGENTS.md` |
| Shared project instructions | `/ai/AGENTS.md` |
| Tools project instructions | `/ai/tools/AGENTS.md` |
| Task notes | `/ai/tools/TASKS.md` |
| Sync state and backups | `/home/jason/.local/state/ai-skills-sync/` |

The instruction files point to the short catalog. Agents load matching skill files and references when needed. Start a new session to pick up changed startup guidance. This configures Jason's standard profiles; other users, profiles, or containers need their own references and filesystem access. The custom `dnsSKILL.md` filename uses explicit file loading rather than native skill-picker registration.

## Automatic synchronization

- Task: **AI-Skills Sync to localnet** in Windows Task Scheduler.
- Schedule: every **15 minutes**, plus login. Runs while Jason is signed in and Windows can reach localnet. Missed/offline attempts retry at the next trigger.
- Background executable: `C:\Python314\pythonw.exe`; no console window or stored account password.
- Source: this Windows `AI-Skills` library. Add a vendor skill and its catalog row here; cataloged vendor folders and supporting files are included automatically.
- Linux adaptation: shared-library paths and the DNS operator reference paths are translated. A Markdown skill containing another Windows drive path stops publication until its Linux adaptation is added to `scripts/sync_localnet.py`.
- Conflict handling: independently edited or deleted managed files on localnet stop the sync. Review and merge the change into Windows, or restore the intended synchronized contents on localnet, then rerun. There is no automatic force-overwrite mode.
- Removal: files removed from the Windows snapshot are removed only if previously managed and unchanged on localnet. Unrelated remote files remain intact.
- Backups: changed or removed files are saved under `~/.local/state/ai-skills-sync/backups/<timestamp>/` before updates. The current successful hashes are in `manifest.json`.
- Windows status: `%LOCALAPPDATA%\AI-Skills\last-sync.json`; rotating log: `%LOCALAPPDATA%\AI-Skills\sync-localnet.log`.

Run or preview a sync from Windows:

```powershell
C:\Python314\python.exe C:\Projects\tools\AI-Skills\scripts\sync_localnet.py --preview
C:\Python314\python.exe C:\Projects\tools\AI-Skills\scripts\sync_localnet.py
```

Reinstall the task, if needed, with a process-only execution-policy setting:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Projects\tools\AI-Skills\scripts\install_sync_task.ps1
```

Inspect or pause the schedule:

```powershell
Get-ScheduledTaskInfo -TaskName 'AI-Skills Sync to localnet'
Disable-ScheduledTask -TaskName 'AI-Skills Sync to localnet'
Enable-ScheduledTask -TaskName 'AI-Skills Sync to localnet'
```

## DNS operator connection

Localnet's `/home/jason/.ssh/config` now defines `emailreseller` using the existing operator endpoint and Jason's account. It uses a dedicated Ed25519 key at `/home/jason/.ssh/id_ed25519_emailreseller_localnet`. The private key was generated on localnet and remains there. Only its public key was added to the operator account; existing authorized keys were preserved.

The authorized-key entry uses OpenSSH `restrict`, disabling forwarding, PTY allocation, and user SSH startup scripts. It still provides command access as the existing Jason account; it is not a DNS-only operating-system account. The server's host key was obtained through the workstation's already trusted connection and pinned on localnet with strict host-key checking.

The Cloudflare token remains on the operator server at `~/.config/email-reseller/cloudflare-api-token`. Its file and parent permissions were verified as `0600` and `0700`. A login from localnet and a read-only Cloudflare zone-list request succeeded. Check authorization and access to the specific requested zone before a DNS change; this setup did not modify DNS records or token permissions.

Connection check from Windows:

```powershell
ssh localnet 'ssh emailreseller id -un'
```

SSH rollback records:

- Operator host: `/home/jason/.ssh/authorized_keys.before_localnet_20260910T020334Z`.
- Localnet: `/home/jason/.ssh/known_hosts.before_emailreseller_20260910T020351Z`.
- Dedicated public-key comment: `jason@localnet-emailreseller`.

If revoking this connection, remove only that public-key entry after checking for concurrent changes. Preserve unrelated keys and known-host entries. Do not restore whole historical files over newer edits.

## Validation

All 10 sender/receiver tests passed on Linux, covering path adaptation, newly cataloged vendors and assets, repeat runs, backups, local-edit conflicts, managed removals, invalid paths, checksums, missing links, and symlinks. The first live sync published the catalog and DNS skill with read-back verification and backups. The initial `INSTALLATION.json` records the earlier installation; `manifest.json` tracks the current synchronized files.

The actual Windows scheduled-task run also completed successfully with `LastTaskResult = 0`; its repeat sync found no document changes. The registered repetition interval was verified as `PT15M`, with a separate login trigger.
