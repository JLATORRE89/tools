# Deployment and completion checks

## Locations and scope

- Source package: `gpu_video_api_package` in the projects workspace. Build a
  wheel from the reviewed Windows source, excluding private state and secrets.
- WebUI environment: `${SERVICE_USER_HOME}/openvino-env`; service `open-webui`.
- GPU worker: `/opt/gpu-worker/venv`; inspect its installed service name.
- Managed model: `${SERVICE_USER_HOME}/genai-env-2026.4`; `openvino-api`.
- ComfyUI: `${SERVICE_USER_HOME}/ai/comfyui-venv`; inspect `comfyui.service`.
- WebUI secrets/config: `/etc/gpu-webui.env`. Worker config:
  `/etc/gpu-worker.env`. Preserve ownership and permissions.
- Account portal: `/gpu-account`, native account APIs `/api/v1/gpu-*`.
- Native WebUI DB is under its installed package `data/webui.db`; current
  `config` schema is key/value. Inspect schema instead of assuming old columns.

## Review, install, verify

1. Read applicable AGENTS/RULES and inspect dirty files. Retain incoming source
   snapshot and a private backup of the installed package. For database changes,
   use SQLite backup rather than copying only a live WAL database file.
2. Compare remote work against its incoming snapshot and current Windows source.
   Merge only changed files. Preserve current TASKS notes and later patches.
   Do not copy credentials, private logs, database fixtures, caches or venvs.
3. Review callback/browser authentication, owner checks, resource admission,
   streaming bounds and privilege changes. Run package tests plus the actual
   browser flow. Synthetic HTTP requests with a bearer header do not prove an
   OAuth redirect works: Google redirects without WebUI's localStorage header.
4. Build with `python -m pip wheel . --no-deps -w <private-output-directory>`.
   Check wheel contents include new templates/scripts/docs, and exclude secrets.
   Upload the wheel over the configured SSH connection. Install it in each
   affected environment using that environment's pip; use `--no-deps` when the
   existing dependencies already satisfy requirements. Do not upgrade unrelated
   packages. Preserve the service user's ownership of its environment.
5. Restart only affected services. Account portal/backend changes require WebUI
   restart; template reads may be dynamic but package changes should use the
   restart for a consistent version. Google Drive-only changes do not require
   model, ComfyUI, worker or OpenClaw restarts.
6. Check service health, authenticated ordinary-user and admin status, anonymous
   denial, owner isolation and feature state. Open Account & Developer in the
   actual WebUI on desktop/mobile, including navigation inside its iframe.
   Remove only isolated test assets/keys and temporary session files.
7. Record hashes, tests, deployment state and remaining blockers in TASKS.md.
   On failure, restore the backed-up affected package/config, restart its service
   and verify health. Do not restore whole old databases over newer user data.

## Installed invariants

- `webui_addon.py` + `templates/account_nav.js` provide the Account & Developer
  dialog. `account-navigation.conf` uses `ExecStartPre` to restore integration
  after upgrades. Include them in every wheel. See package `docs/WEBUI_ADDON.md`.
- Owner quotas include native WebUI uploads. Compute uses durable admission;
  raw rendering endpoints must not become a bypass. An uncertain GPU lease is
  not safe to clear without confirming the associated backend work ended.
- Keep host CPU/RAM reservations and ComfyUI `--cache-none`. Do not raise limits
  to make a test pass. Per-subscriber GPU guarantees remain future work.
- Model labels may change; IDs and chat history stay stable. Verify real GPU
  execution and check that one model's system prompt/tools were not copied onto
  another. A Video Cutter tool wrapper is not an independent chat LLM.
- Drive stays unavailable until the operator supplies OAuth client/secret,
  registered HTTPS callback and separate vault key. Never invent these values.
  Browser callback GET serves a minimal shell, strips the code from history and
  performs an authenticated POST. State consumption must be atomic/single-use.
  Connect from the account iframe using top-level navigation. Protect OAuth
  callback query strings from log retention at the public proxy.
- B2 and Drive live verification requires an authorized real connection. Mock
  success is not provider success. Publishing does not delete the hosted source
  or refund its quota. Do not claim resumable retry unless implemented.

## Remote-agent handoff

Include source snapshot, scope, constraints, acceptance tests and changed-file
report requirements. The implementer writes status and completion evidence;
review independently before merging/deploying. A failed SSH attempt from localnet
does not establish that the ThinkPad is offline: the supervising workstation may
have an existing authorized connection. Ask it to perform the deployment when
necessary; do not invent credentials or weaken SSH host verification.

Shared skills use the managed `AI-Skills/scripts/sync_localnet.py` sender from
Windows. Preview first, merge reported remote conflicts, then sync and verify.
This publishes skills, not arbitrary application code or private environment
files. OpenClaw's native skill installation is a separate deployment step.

Shared GPU scheduling: see the application package's docs/GPU_SCHEDULING.md.
Chat/render lanes alternate eligible work with owner isolation and durable
memory reservations. Two slots per lane are ceilings, not four guaranteed GPU
jobs. The current host serializes heavy work. Keep parallel-safe flags disabled
until backend concurrency and memory release are proven. Never expire running
leases. WebUI internal Python Ollama calls bypass HTTP route middleware; keep
that inference adapter disabled until lifecycle admission is implemented.
Verify a real render-to-chat handoff, not just endpoint health. Queue waiting
is bounded and active renders are not preemptible. Preserve CPU/RAM limits.

CPU helper deployment: the worker now has two background threads, 16 accepted
helper jobs and one helper per owner alongside rendering. Only asset.inspect
and comfyui.prepare are admitted without GPU reservations. Render finalization
uses that pool after confirmed GPU cleanup; preserve uncertain admission holds.
Storage writes and GPU admission use separate locks. Never route CPU-labelled
inference, encoding, cutter or plugin work into the lightweight allowlist.
Verify a helper completes while a real GPU render remains running. Account MCP
adds prepare_render, inspect_asset and get_background_job; keep connection scope
checks and authenticated asset URLs. Existing HTTP transfers bypass GPU admission
already and retain their own limits; they are not counted as CPU helper jobs.

WebUI image requests: the addon recognizes explicit English image requests and
accepted concrete image alternatives even when the Image toggle is off. It keeps
the subject from earlier turns instead of rendering literal "yes" or "generate
it". Native ownership/plan/quota checks still apply. Successful attachments get a
server-confirmed local ComfyUI caption, not an LLM-generated claim about capability.
Native saved-chat progress includes stages and elapsed time; it is not reasoning
text or percentage completion. See application docs/CHAT_PROGRESS.md. The older
adapter's adult-checkpoint acknowledgement flow is separate and is not currently
exposed by the fixed-workflow account renderer. Never claim it was removed from
all source, or restored in the account route, without verifying that exact path.

## Workstation source/configuration snapshots

The sibling `AIStack` project holds the deployment inventory and restricted, Git-ignored localnet snapshots. Read `AIStack/README.md` and `AIStack/SYNC_REPORT.md` before reconciling files. `python AIStack/scripts/sync_localnet.py` uses the tools private environment and existing SSH alias, collects code/configuration read-only, exports WebUI executable registrations without chat/user tables, and verifies hashes. It does not deploy or overwrite application source. Exact private configs, vault keys and deployment manifests stay under its restricted `.private-state`; never copy them into skills or Git. Keep newer sibling project code when a deployed copy is older.

ComfyUI crash recovery now checks terminal render holds every ten seconds against
an empty backend queue and zero loaded models. See application docs/CRASH_RECOVERY.md
and deploy/comfy-recovery.conf for bounded service restarts and rollback. This is
positive execution/memory evidence, not lease expiry. Interrupted jobs and unknown
backend state still require operator investigation; never clear those by age.
