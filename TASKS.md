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

- 2026-09-15T22:27:00-04:00 - in progress: Investigate and fix Monopoly GO Assist getting stuck on three/four bottom crates. Reviewed project files, live phone screen, deployed loop state; Claude Code agent is implementing a scoped change. Live validation and deployment pending.

- 2026-09-15T22:44:00-04:00 - completed: Monopoly GO Assist Pick a Box fix implemented with Claude Code; removed false dimmed-popup gate, confirmed live tap at (539,1901), added bounded poll/retry and backoff resume. Staged detector true on crate fixture/false on board; 13 tests and Python compilation pass on Windows/localnet. Updated ${SERVICE_USER_HOME}/bin/monopoly-go-assist and /ai/monopolygo/RULES.md with backups, restarted supervisor (PID 184182, loop PID 184185), hashes match staged/local. Fresh automatic crate encounter pending; current phone shows genuine 0/50 rolls.

- 2026-09-16T20:05:00-04:00 - in progress: Add current-screen COLLECT support to Monopoly GO Assist. Implemented exact COLLECT OCR fallback, direct collect command, chained-popup integration, docs, and 4 parser tests; all 17 tests and Python compilation pass locally. Localnet SSH reaches port 22 but stalls during public-key authentication, so a bounded hidden retry deployer (C:\scratch\deploy_monopoly_collect_fix.ps1, log alongside it) is retrying for two hours; it will validate remotely, back up deployed files, install, invoke collect once safely, and restart the supervisor.

- 2026-09-16T20:53:00-04:00 - completed: Deployed Monopoly GO Assist COLLECT support to localnet after restoring SSH and mounting the configured /ai filesystem. Added exact-text fallback plus a modal-gated green-button search around GO_BUTTON for expired-event leaderboards at (538,1894), retained the y>=2100 detector for chained rewards, and added the direct collect command. All 19 tests and compilation pass locally and on localnet; deployed hashes match staging. Live validation tapped two center-band and two standard-band COLLECT screens, revealed the 172,000 reward, cleared the popup chain, and advanced to Bank Heist. Supervisor restarted as PID 15470.

- 2026-09-18 START: Diagnose live Monopoly Pick a Box/purple roll stalls; preserve existing edits. Found BUILD detection preempts specific handlers.

- 2026-09-18 FINISH: Monopoly box/purple roll priority fix deployed to localnet ~/bin/monopoly-go-assist and /ai/monopolygo/monopoly-go-assist. Existing changes preserved. Pre-fix local/live hash 69c8fe433472c6c40f6d91a0fd11ed58c3811f986dfbcd46818d3367915f9c32; no revert found. Live box screenshot matches box, BUILD, and color-wheel detectors. Box and purple roll now precede both in main loop and backoff. 20 tests pass on Windows/Linux (including four event/loop overlap scenarios). Live first and subsequent boxes cleared on first tap; normal play resumed. Purple jail priority tested offline; no fresh jail event observed yet. Supervisor restarted and running PID 731876. Deployed SHA256 bdaa09a563f8f6e203fd4f59988628afffd979b7f3a64243085aa54fe1b7f0f3. Remote backups ~/ai-backups/monopoly/<UTC timestamp>/{bin-before,source-before}. Current log ~/ai-logs/monopoly-go-assist-20260918.log.

- 2026-09-19 FINISH: Local Open WebUI image repair. Started existing stopped ComfyUI XPU service; forced Image-button requests through legacy image route per request, added submitted-prompt fallback and exception logging. Temporary model-wide override removed. Three regression cases pass, test1 direct API and full chat path generated images, user confirmed image display. Source/limits/rollback documented python/openwebui-image-repair/README.md. Existing video artifacts report ready; video not generated in this repair. OpenClaw local MCP connection in progress.

- 2026-09-19 START/FINISH: OpenClaw connected to localnet MCP using restricted SSH tunnel and five named ComfyUI adapters. Existing three script tools preserved. Probe8tools; image job ff48e6d4-0f8b-4050-a8a6-c00c9ef0ef72 completed; actual OpenClaw run e6b8da76-0705-4df9-9143-fa465c462035 successfully called localnet.list_comfyui_video_artifacts. Source/rollback/limits python/local-bin-mcp/OPENCLAW.md. No gateway restart; native MCP runtime reloaded. Local AI Stack found in WebUI skill table and explained, unchanged.

- 2026-09-19 FINISH: Organized ComfyUI, OpenClaw, Telegram and Open WebUI skills; installed canonical comfyui-render in OpenClaw and synchronized the 10-document localnet catalog. Private deployment values now resolve from ignored .env via CONFIGURATION.md and scripts/repo_env.py; localnet copy provisioned separately with mode 600. Existing gitignore preserved and extended.
- 2026-09-19 FINISH: Fixed local Qwen native tool calling at the OpenVINO API and enabled OpenClaw supportsTools after live API/replayed-result and actual Telegram-session MCP inventory calls succeeded. Parser tests pass (4); reusable helper and integration patch under python/openvino-tool-calling. Global model/Telegram credentials and pairing unchanged. Fresh Telegram inbound-to-reply verification remains unobserved.
- 2026-09-19 FINISH: Actual OpenClaw MCP video job 976f0225-9bdd-4ab7-a07b-864396b68b03 completed in 105.34s. ffprobe confirms H.264, 256x256, 17 frames, 2.125s. First frame is visually distorted: functional pipeline test, not a visual-quality acceptance. No duplicate render submitted.
- 2026-09-19 FINISH: Monopoly blue SPIN was misdetected as quit dialog. Added OCR confirmation; 21 tests passed Windows/Linux, deployed both copies with backups, and live wheel cleared followed by normal play. Supervisor resumed; credentials and game policy unchanged.
- 2026-09-19 FINISH: Reviewed securityAudit.md. Hardened catalog sensitive-file rejection and nested/encoded Timezones request guard; 13 catalog tests pass Linux and 3 request-guard tests pass. Two discovery logs and archive removed from index, local copies retained. Known-private-value audit passes. Source Timezones patch not production-deployed; Git history not rewritten. See securityAudit.md for exact scope and limits.

- 2026-09-19 START: Create a reusable remote-development skill for Open WebUI. Read-only inspection found desktop VS Code and installed WebUI terminal router support; browser editor/backend choice pending. No remote editor installed or access widened.
- 2026-09-19 FINISH: Created and validated AI-Skills/openwebui/remote-development with setup choices and explicit backend/access boundaries; private-config audit passed and 12-document catalog synced. Skill instructions are available in the shared catalog. Browser editor service and WebUI workspace connection are not deployed; awaiting user interface preference.

## 2026-09-19 — In progress: Telegram local-model speed and weather accuracy
- Inspect search failure, ambiguous postal-code resolution, and elapsed tool/model time; preserve credentials and unrelated sessions.

## 2026-09-19 ? Completed: Telegram weather path and model speed
- Diagnosed an unavailable search provider, ambiguous unqualified postal-code
  lookup, and a malformed tool-call retry. Added country-aware get_weather MCP
  tool and short cache; US ZIP default plus clarification on ambiguity.
- Installed/validated local-weather skill for main; only the authorized Telegram
  sender's unavailable web_search tool is denied. Gateway hot reload applied,
  MCP reload/probe finds 12 tools. No gateway restart, token/pairing change or
  session reset. Existing localnet model selection and 300-second timeout kept.
- Added complete-call generation stop and OpenVINO compiled-model disk cache;
  GPU residency policy remains unload-between-requests. Five protocol tests and
  three weather tests passed. Correct location and weather measurements were
  returned in actual native tool-call/result replay. Warm-cache model phases
  measured 3.68s + 5.19s; weather lookup about 1.1s. Before cache, about 49s+15.5s.
- Initial live model test hit shared AI memory pressure after the video smoke;
  test-only idle render state cleared, services restored, memory safeguards kept.
- No fresh user-originated Telegram turn was timed during this verification.
  The old generic search provider remains unconfigured outside this scoped rule.
- Read installed OpenClaw Host Desktop and Cloud Worker Desktop docs for requested
  explanation; left both desktop toggles unchanged.
- New skill synced to localnet catalog; private-configuration audit passed.

2026-09-19 FINISH: Reviewed localnet handoff merged into Monopoly source and localnet-bin copy. Primary fixes prevent stale post-probe taps and unsafe failed-probe fallback; 43 tests pass, live script deployed. Added Local AI Stack deploy and Monopoly skills, deployment feedback, and updated OpenClaw/WebUI references. Managed sync published 18 files (8 changed) with backup/readback; private config audit passes. Claude/Codex startup guidance on localnet reads the persistent feedback. Telegram helper deployed to ThinkPad and real owned PNG download hash/0600 verified; fixture removed.
2026-09-19 VERIFY: Added integrated caller/probe regression; final Monopoly suite 44 tests passes. Persistent feedback includes neutral access wording and user-focused storage copy.
2026-09-19: Updated deployment and ComfyUI skill instructions for approved CPU helpers, confirmed GPU release before output storage, scope-safe MCP usage. Validated skill and private config audit; synced reviewed instructions to localnet and native gateway skill. Application details in gpu_video_api_package/TASKS.md.
2026-09-19: Updated ComfyUI delivery helper/skill for WebP/WebM signatures and document delivery. Compiled/validated/audited and synced to localnet and native OpenClaw gateway. Retained review samples documented in application TASKS.
2026-09-19 START: Document the tested scoped onoff4 chat edit command and sync the ComfyUI skill.
2026-09-19 FINISH: Documented scoped clothed onoff4 WebUI edit command; private audit passed and managed skill sync verified.

2026-09-20 PROGRESS: Optional Brave image-search JSON installed disabled at /etc/gpu-product-search.json; private key reference only. Search and importer 20 tests passed; live authenticated 422/unauthenticated 401 and browser unavailable message verified. Scoped WebUI wheel 8dabeb059614a55e38cc6b8ea12e7989cf3f08cc0b5977f4f9a7c923c5aefbee deployed. Worker Pillow dependency fixed. FLUX2 Klein two-reference mannequin render 28386dfb-4ac0-411a-89c8-c54ab02f0de6 completed and visually reviewed; 19250-byte WebP. Two-reference mannequin binding enabled. Search provider key, additional reference counts, person try-on and billboard acceptance remain outstanding; do not report feature complete. Selected garments persist across searches. Reviewed deployed API docs/examples/config copied into tools skill and catalog sync verified. Host reservations unchanged.

2026-09-20 completed: Added POST /api/metadata/query and /meta/api/metadata/query with X-License-Key auth, owner-only queries, invalid/expired license rejection, cloud-sync consent, bounded pagination and safe metadata fields. No notes/local paths/license IDs returned. Deployed scoped endpoint to MuCache with backup web_app.before-metadata-query-1789921403.py and graceful Gunicorn reload. Eight metadata/privacy tests pass. Local AI Stack adds AES-GCM per-owner credential vault, HTTPS verify-before-save/disconnect/query, Account settings UI and Search my MuCache. Three vault/route tests and live browser checks pass; public endpoint 401/403 and invalid-key-not-saved verified. WebUI wheel 90c7e42cc4de51ad9074074380d0a672f3198e0e42a510835462b71c6671d956. Config /etc/gpu-worker-workflows/mucache.json, dedicated protected vault key outside JSON. No real user license was used; valid customer query remains unverified live. Does not fetch uncached metadata or bypass retailer blocks.

2026-09-20 START Monopoly multiplier OCR stall: inspect live badge, add verified OCR fallback, regression test and scoped deployment.
2026-09-20 DONE Monopoly: matching live/source hashes ruled out revert; two-crop consensus OCR repairs x1 and purple x5. 47 tests pass; bounded live probe confirmed x5 and supervisor resumed repeated rolls. Both live scripts backed up and source mirror synced.
2026-09-20 FOLLOWUP Monopoly later lost its ADB device after verified rolls; supervisor continues retrying. Local workflows guide and updated maintenance instructions synchronized to skills.

- Start 2026-09-20: Verify reconnected Monopoly phone; calibrate remaining x5 OCR crop failure.
- Done 2026-09-20: Reconnected phone authorized and visible. Added inner badge crop after captured x5 failed both previous crops; exact color/mask consensus retained. 47 tests pass; source/mirror and both live scripts synchronized with backups. One supervisor loop restarted; live log confirmed settled x20 and single roll. Multiplier can change with remaining dice/events; bounded re-probing remains active.

- Start 2026-09-20: Stop repeated multiplier tap loop; verify actual dice consumption, not tap log. Increase animation settle from 0.4s to 2s based on live observed cycling.
- Done: 2s multiplier settling and consensus-first reading deployed; 47 tests pass including x1/x4 conflict regression. Live verified dice 14 to 13, subsequent max x3 settled and held without further badge taps, then raid target and reward handled. Previous claim based only on tap logs was insufficient; now verified board/dice change. Source and both live copies synchronized.

- 2026-09-20 start: Recurrent multiplier loop traced to loose digit fallback accepting 4 after strict OCR failure; remove fallback, rate-limit probes.
- Done: strict consensus-only multiplier reading and 60-second re-probe cooldown deployed to both live copies, hashes match; 43 regression tests pass (obsolete loose-parser cases replaced by rejection regression). Over a minute of live checks: x3 retained through consecutive rolls and BUILD handling; dice fill fell 0.37 to 0.15 without repeated multiplier taps. Skill synchronized to localnet. Longer-term/event coverage remains unverified.

## 2026-09-20 Account ComfyUI/search documentation
Started and completed: synchronized reviewed account editor and product-search operational documentation into Local AI Stack deploy skill. No credentials included. Provider activation remains blocked by missing API key.

## 2026-09-20 Localnet source/configuration snapshot
Completed: added AIStack sibling inventory and protected 2,292-file snapshot; source reconciliation retained newer tools/GPU/Cutter code. Added snapshot instructions to deployment skill. No secrets published or service changes made.
`nStarted Monopoly performance repair: inspect live empty-dice false positive, remove repeated frame decoding, benchmark and verify deployed loop.
Completed Monopoly performance repair: 46 tests passed; atomic cached frame reads and low-dice fix deployed to both live copies; pixel-check benchmark 512.22ms to 6.43ms, backoff polling 300s to 15s. Verified actual x3 roll, dice consumption and cash increase. Overall 20x gameplay not established; game currently has zero dice. Backups retained; other event paths not all replayed live.
Follow-up complete: empty-dice check precedes multiplier probes, preventing zero-dice cycling. 47 tests passed; final deployed hash a046d5a7a6c8f2ff2f7bca310e7ffbb639f1e22c2a628c9a2011150f4fb72fba.
Started workstation Monopoly tool follow-up: verify deployed/source parity and update current maintenance handoff and test entry point.
Completed workstation Monopoly follow-up: both executable copies match both deployed hashes; updated both handoffs and maintenance skill with current empty-dice and performance rules. Fixed direct test entry point so it runs all 47 tests, matching unittest discovery. Both invocation modes passed; private configuration audit passed. No service restart needed.
Started build-menu recovery repair: live menu missed by detector and repeatedly reopened during dice backoff; inspect geometry, add regression coverage and verify return to rolling.
Completed themed BUILD recovery: footer detection fixes captured Little M room false negative; bounded verified close, per-card screen checks, 30s visit cooldown, and backoff resumes dice before BUILD. 52 tests pass locally and on host; four source/live script hashes match ea65dc659d386cdbe24b7bf2edb3e43f582fba75722467017aab6fa185c55d9c. Live stuck menu closed first attempt; gameplay resumed and reached jail Roll Doubles event. Local mirrored source/docs/skill updated; backups under ~/.local/state/monopoly-build-backup. Not all themes replayed live.

- Monopoly purchase-loop guard deployed 2026-09-22: no automatic shop visits or blind unknown-modal taps; detected offer closes bounded; 56 tests passed. See python/monopolyAssistant/CODEX_HANDOFF.md.

- Purchase-sheet follow-up complete: cancelled observed billing sheet, deployed foreground tap guard, reward text checks and higher orange-X detection. 60 tests pass; live offer closed first attempt; one loop monitoring zero dice.

2026-09-22 full-log audit: reviewed all 12 logs; 70 regression tests pass locally and on Localnet. Removed residual blind popup taps from dice backoff; validated raw captures and portrait dimensions; isolated per-process frame/OCR files; continuous mode waits through disconnects and missing game focus rather than crashing. Failed BUILD closes have a 60s cooldown. All messages are timestamped with classified state intervals. A loop lock prevents duplicate automation. See LOG_AUDIT_20260922.md for counts, evidence and limitations. Deployed hash 08f2c31c201dd3a69b54b1f1f7ee652066c55f9e63a82e55b145b6a326b41fe8. Phone disconnected at deployment: one loop waiting safely; actual gameplay/reconnect still needs live verification. No blind unlock swipes: bring the unlocked game to foreground after reconnecting.

## Live follow-up and navigation recovery (2026-09-22)
The phone reconnected and the deployed loop resumed without a restart. Pick a Box was cleared live. Further inspection found an actual 1/60 pill whose blue fill occupied x376..379, y2157..2179, outside the former scanline. A contiguous 3-by-5 blue edge patch now recognizes this last die; saved 0/60 capture still returns zero. Bounded building during true dice waits is restored after event/dice checks, using existing visit budgets/cooldowns.
Unknown dimmed popups now get at most two guarded Android Back attempts after a 15-second settling period; no blind center taps. Failed BUILD closes try one guarded Back before cooldown. Back requires exact game foreground and cannot operate on billing/other apps. These recovery paths do not authorize purchases or guarantee every future dialog is dismissible.
74 tests pass on workstation and host. Deployed/source hash: 4665dcc855a933ad82e882decc0b079f28c4b1d17c262423625a7e9a4ec951b7. Live run recognized the saved last die, settled at observed x3, issued GO, opened BUILD, spent banked cash on upgrades and closed BUILD on the first attempt. Back-fallback paths are regression-tested; their live failure conditions were not artificially induced. Earlier disconnected-device verification limitation is resolved by actual automatic reconnect, but permanent hardware availability and future game UI compatibility cannot be guaranteed.

Last-die multiplier correction: live game permitted selection of x3 with only 1 die, then reset to x1 on GO, causing the bot to probe x3 again. Confirmed rounded-edge last-die detection now selects x1 without a maximum probe. The live run then entered a raid and selected its target. 76 tests pass locally and on host; final hash 0ef49b4049bde0e3bb7a1301f6ef7fa0b2846428e17ff75976c65890f5c1059c. This supersedes the intermediate hashes above. Preserve maximum discovery for ordinary dice availability and the confirmed last-die x1 exception.

## Quick Wins gift-box decisions (2026-09-23)
1. On the unobstructed board, detect the red badge at the bottom-left WINS icon. Check during ordinary play AND dice backoff; do not require a roll-count tick threshold. Reopening has a five-minute monotonic cooldown.
2. If already inside verified Quick Wins, resume its reward chain immediately. Recognize QUICK/WINS, MILESTONE REACHED, QUICK WIN COMPLETE, or the combined WEEKLY PRIZE/FILL THE BAR footer (stylized title OCR can be blank).
3. On these verified screens, find a green button and require an exact normalized COLLECT, TAP TO CLAIM, CLAIM or GO label before tapping. A second inset crop excludes the button rim when OCR adds spurious letters. Reject prices, FREE, and unknown labels.
4. Wait three seconds after a claim. Refresh and reverify; tolerate short animations with three additional checks. Claim up to twelve buttons per visit; never tap through an unverified screen. Verified Quick Wins precedes the broad orange-color purchase detector because celebration confetti can trigger it.
5. When no verified claim remains, use guarded Android Back only if still inside verified Quick Wins. Return control to event handling, rolling or dice waiting. Actual purchase dialogs and unrelated screens are not part of this handler.
6. On a disconnect, continuous mode keeps its existing safe reconnect behavior. Never interpret missing capture data as another claim target.

79 regression tests pass on workstation and Localnet. Live claims verified the 2,770,000 cash milestone, a 20-dice reward and chained daily rewards. Source/live SHA256 d6b0e6a12c8c930e05de24cf71f7d9ff9f7b401711abcbdd48b27803e0a6e9f3. Workstation mirror synchronized. No purchase buttons were used.

Quick Wins final live verification: all three daily tasks claimed, milestone/chain completed, gift badge cleared, returned to board. Dice increased 0/60 to 30/60; cash 264,544 to 3,727,544; event hammers 72 to 84. Fixed generic TSV fallback mistaking task text 'Collect 1 Sticker' for a button: COLLECT must stand alone on its OCR line. If guarded Back leaves the verified completed Wins page open, tap its observed close X (540,2245), never a guessed button outside that verified screen. 80 tests pass locally and on host. Final deployed/mirror hash 4dfebc5b6d8b04cfab314e7922640f0ce637b32e3654917302bfa0e02a02a2af supersedes the intermediate hash.

## Treasure digging event (2026-09-23)
Recognize LEVEL n/18 plus blue display case before generic popup, BUILD or roll handling, including during dice backoff. OCR the remaining hammer count; no tile tap if unreadable or zero. Detect compact blue-star connected components within the dig grid, refresh after every tile, and permit at most two attempts per tile per level. Current strategy chooses center-near tiles; it is not an optimal hidden-object solver. Recognize TREASURES FOUND and verify the COLLECT label. At zero hammers, guarded Back then verified event close returns to ordinary play. Tutorial was advanced manually from its highlighted tiles; automated tutorial parsing is not claimed.
Live: first treasure uncovered with two hammers, level 1's 50-dice reward collected; level 2 grid (15 tiles) and remaining 82 hammers correctly detected. Handler deployed in both loop paths; 83 regression tests pass locally and on Localnet. Hash a2b61a5010da11f7dfb7f2b0577b6ab0fce6c1cba0639e588e12de0fc89891d4. Workstation mirror synchronized. Unknown future tile designs wait without blind taps.

Treasure exit watchdog (2026-09-23): live level 5 introduced gold-star tiles the current blue-star detector did not recognize, exposing an unbounded wait. Exit now triggers at zero hammers, 45 seconds without a level/hammer-count change (including unreadable counts or a stuck reward), or a 10-minute visit limit. Exit taps only the verified event's observed close X, re-captures to confirm departure, and bounds close attempts to two before guarded Back and a 30-second retry cooldown. No automatic re-entry is added. Gold-star tile solving is not implemented by this fix; the watchdog returns to normal play instead of waiting indefinitely. 86 tests passed locally and on Localnet. Deployed hash 92c381d9c6fd75c2d7e001d36eb52cab3c81f2a5c4e0ed688c8df7ac67377bfb.

2026-09-23: character-production shared skill validated and synchronized to Localnet. FPSGAME coding helper supports explicit skill loading; live authenticated local-chat review completed with that skill. Plan and first 512px conditioning baseline created in FPSGAME.

2026-09-23 Monopoly stuck investigation: supervisor alive, waiting_for_game_focus then waiting_for_device. USB Pixel present but ADB inventory empty. Restarted ADB server; existing authorized device returned. Screenshot confirmed required Google Play Monopoly update; installed via displayed Update button. Package reports 1.77.1, updated 19:12:50. Bot resumed reward collection; checking post-update screens before claiming normal play. No automation guards disabled.

Monopoly recovery verified: manually closed observed new-season and race introduction X controls after update; existing bot collected season rewards, dismissed purchase offer without buying, discovered/settled x20 and resumed rolls. Before/after screenshots show token movement, event progress 0/5 to 4/40, cash 4579064 to 4757064 and dice 394 to 384 with intervening rewards. One supervised loop remains running. No automation code changed; automatic app updates, ADB-server restart and the new introduction screens are not newly automated.

2026-09-23 Halloween house-choice recovery: the new event shield artwork falsely
matched the broad purchase-X detector. A specific handler now precedes purchase
handling in main and dice-wait loops. It requires a possessive Board title and
multiple calibrated circular house targets; continues remaining targets within the
same event, at most two attempts per position. Dim rings are recognized. Known
event animations stay out of the purchase path; verified collect labels can be
claimed. Exact game foreground guard remains. 91 tests pass locally and on host.
Live choices earned 30 treats; one-time tutorial/shield-info prompts and final
collect were manually advanced during validation. The bot then resumed ordinary
reward collection and multiplier probing. Not a general minigame solver or a
promise that unknown tutorial layouts are supported. Both live executables and
python/localnet-bin mirror synchronized; rollback in ~/.local/state/monopoly-house-backup.


## 2026-10-03 Computer Work browser tools

Started at user request: build managed browser automation tools for the Local AI stack. First milestone: authenticated owner/chat-isolated browser service, bounded page observations/actions/screenshots and Open WebUI adapter, verified against a local fixture. Authoritative implementation belongs in tools/python; integration/deployment documentation belongs in AIStack. Existing planned project/editor work remains separate.

- User specified the project folder: moved the new feature source to C:/projects/AIStack/computer_work. That folder is now authoritative for this feature; no existing tools source was moved or modified.

- Completed first Computer Work source milestone in C:/projects/AIStack/computer_work at the user-specified destination: managed Chromium service, native WebUI toolkit adapter, model instructions, local demo, setup guide and tested dependency versions.
- 11 tests passed (15.99s) with real Chromium coverage for browser actions, screenshots/password masking, owner/chat/cookie isolation, origin/redirect/subrequest/WebSocket blocking, stale/changed-element/navigation references, limits, idle reaping and service lifecycle. Screenshot visually inspected; source compilation and isolated wheel build passed; wheel contents checked for source-only modules/metadata.
- Package artifact is in computer_work/dist (ignored). Code/guide/tests remain in the project folder. No localnet service, account, browser profile, model registration or existing Local Code configuration was changed.
- Remaining milestone: isolated localnet installation, native human approval controls, a signed-in Computer Work chat evaluation, screenshot rendering/status UI, and authentication handoff. No claim of live WebUI availability or ChatGPT capability parity.

## 2026-10-04 Monopoly side-icon free items

Started at user request: inspect side icons and automatically use only free items.
Source implementation complete in python/monopolyAssistant, synchronized to
python/localnet-bin. Fresh verified-board side-strip OCR accepts standalone FREE
labels only; a separate gift/shape/local-label gate rejects prices, locks,
conditions, unknown offers and detected purchase dialogs. Bounded visits/claims
and cooldowns apply in normal play and empty-dice waiting. Existing purchase,
focus, multiplier and shop guards remain. 113 offline tests passed in 1.160s.
Source/mirror SHA256 10077ba67c6f5d380c436bc8c94459f28a399de772abf6136d3f4a56bc9e56ae.
Active Pi deployment and real layout/font/free-claim verification await its
current SSH target. Old localnet service is inactive with no ADB device; neither
it nor a game session was started or tapped. Side icons without visible FREE
text and mixed-price offers are outside the current conservative handler scope.

## 2026-10-04 Monopoly side-free update deployment
Deployed to rpi3 (jason user monopoly-assist.service), not the inactive localnet supervisor. All 113 tests passed on the Pi. Runtime SHA-256: 575399a13d09b62ce52bd269bf55d7d0ea281a750956b2bd18db6a28c3ad5266 (only ADB path adapted to /usr/bin/adb). Rollback: ~/.local/share/monopoly-assist/backups/20261004T210357Z. Confirmed active MainPID 155812 and exactly one assistant loop. Live screenshot showed the main board with zero dice and no side icon labeled FREE; actual free reward collection remains unverified. Initial staging encoding error was caught by tests and rolled back; corrected UTF-8 staging passed.

## 2026-10-04 Blocks Boutique deployed
Recorded a 15-second ADB walkthrough; completed recipe 1 and pressed its observed 150-dice COLLECT control. Implemented fresh-grid/shape reading, legal-placement planning, connected material-bearing shapes, exact foreground guarded drag/release, predicted-outcome checking, and specific prize-cabinet NEXT transition. 124 tests passed both on Windows and Pi. Pi runtime SHA256 70a3e34c92154714d7394ece92933eb5c9a3c4ff1f67cd9bbf030371e39ca8bd; backup ~/.local/share/monopoly-assist/backups/20261005T000905Z. Verified active user service, one loop PID 162348, and entry into boutique_blocks. Source mirrors match. See BOUTIQUE_WALKTHROUGH.md for observed mechanics and limitations. No paid refill or purchase was used.


## PAUSED by user: Blocks Boutique review (2026-10-04)
User requested stopping this work and reviewing it later. Pi monopoly-assist.service
was stopped for calibration and must remain stopped until work is resumed.
The new handler is deployed; 124 tests passed on Pi and Windows, but autonomous
execution is NOT fully verified. Recipe 1 completed and its 150-dice reward was
collected. Recipe 2 reached 8 tokens with verified 2x2 and T-shaped placements.
A later top-edge 2x3 placement failed without spending a token; the handler
correctly paused on its unexpected outcome. Manual held-touch calibration also
failed without spending. Latest screenshot still shows recipe 2 and 8 tokens.

Review next: resolve drag-preview alignment, including grab point, piece scaling
and vertical offset near the top edge. Do not blindly retry or change the 400px
offset globally: earlier placements worked, while the latest held previews were
red and overlapped existing cells. Consider recording the complete drag and
verifying the legal preview BEFORE releasing a piece. Retain exact foreground,
touch-release, predicted-outcome and no-purchase guards.

Evidence: C:/scratch/monopoly-tutorial.mp4 (15 seconds),
C:/scratch/boutique-held-fail.png, C:/scratch/boutique-held-corrected.png,
C:/scratch/boutique-corrected.png. Source guide: BOUTIQUE_WALKTHROUGH.md.
Runtime SHA256: 70a3e34c92154714d7394ece92933eb5c9a3c4ff1f67cd9bbf030371e39ca8bd.
Rollback: ~/.local/share/monopoly-assist/backups/20261005T000905Z.
Do not resume automatically or claim the mini-game is finished.

## 2026-10-04 Normal assistant resumed
User explicitly requested that the assistant remain usable and restart. Installed a default-off MONOPOLY_BOUTIQUE_AUTOPLAY gate: unfinished block placement requires explicit opt-in (value 1); a recognized Boutique board pauses for review. Existing normal board play, rewards and purchase guards remain active. 125 tests passed on Windows and Pi. Runtime SHA256 d9b66db63fd2fe4aea0d2cfe97320a1da572f6fb719adee97fd0124ba6988d15. Backup ~/.local/share/monopoly-assist/backups/20261005T002639Z. User service active PID 162661; live main board showed 159 dice and multiplier verification resumed. Earlier request to leave the whole service stopped is superseded; mini-game development remains deferred.

- 2026-10-06 completed: Monopoly Pi GO-sparkle/BUILD and Color Wheel recovery; 20-minute watch, 131 tests on Windows/Pi/LocalNet, synchronized runtime/source/docs. Pi active, LocalNet fallback inactive, Boutique autoplay remains disabled. See python/monopolyAssistant/TASKS.md.
- 2026-10-06 final follow-up: Added confirmed-board shortcut for Color Wheel OCR; 132 tests pass on all hosts. Final source SHA256 48a1da7dabcc8900dbba3d13af788a86c213468ef4f136d1a2d7216d30c63821. Pi active, LocalNet fallback inactive.
2026-10-09 Halloween title-separator fix started/completed: current captured five-ring board OCR inserted a vertical separator before wrapped BOARD, missing the house handler and falling into BUILD/raid. Added strict separator/whitespace title predicate, preserving foreground, multi-ring and bounded-attempt checks. 134 tests pass Windows/Pi; initial system Python lacked Pillow, so reused existing GPU package venv without dependency changes. Active Pi rollback house-separator-20261009T201542Z. Live rings5->4 and treats0->9, then autonomous return to board and normal play verified; one loop PID462017. Device-connect idle monitoring enhancement requested next; in progress.

## 2026-10-09 Mini-game recovery and phone monitoring completed
Halloween wrapped-title fix is committed as 74a2b17; Spooky Express overview recovery is committed separately as 3bfc73d, with its introduction date in the subject/body and MINIGAME_HISTORY.md. Added a Git note to first tracked snapshot f229c71 with dated evidence for raid/heist, match-3, jail/bonus rolls, Color Wheel, Pick a Box, treasure, Halloween houses and Blocks Boutique. Historical commit dates were preserved. Boutique autoplay remains default-off.
Live house-choice recovery verified rings 5->4, treats 0->9, further automatic choices, return to board and normal play. New Spooky Express First Class overview (13 points, reach45) closed through its verified grey footer X; no upgrade/purchase action. 137 tests passed before phone monitoring; 141 pass after it on Windows/Pi/Localnet. Physical unplug/replug remains unverified; simulated missing/unauthorized/offline/multiple-device, device swap, foreground and unsupported-layout cases pass. Active Pi loop recognized the authorized phone, serial-bound commands and checked game focus before publishing a calibrated frame. One loop remains active; Localnet supervisor remains inactive. Source/localnet-bin and both fallback executables have identical hash cc5ddacfc644e881f4ad67fff7544b5f5fa4bfc8640f13262da6959358525bbd; Pi runtime differs only in /usr/bin/adb and hashes 318737c7c91faa0d30ad8f22b0b76e331e1cf13a93663132e0a267e6dca92041. Rollbacks: house-separator-20261009T201542Z, spooky-express-20261009T203115Z and device-monitor-20261009T204013Z under the Pi user's .local/state/monopoly-assist/backups. No new third-party dependencies.

## 2026-10-09 Tools repository commit preparation
User explicitly requested committing this tools repository. Preserve all existing working content and the previously staged private-log/archive removals. Verified known-private-config audit, syntax of 21 changed/new Python files and JSON syntax; Mono141 tests, catalogue sender5 tests (receiver8 require Linux), sensitive-path3 tests, weather3 tests, OpenVINO protocol5 tests and actual installed WebUI image-prompt3 cases passed. Initial Windows image-prompt run lacked its host-only package path; rerun on Localnet passed without mutating live code. No dependencies upgraded, no source published or remote pushed.
2026-10-09 repository validation follow-up: all 13 catalogue tests also passed on Linux in isolated staging, including the eight Windows-skipped receiver cases. Known-private-config and Python/JSON syntax checks passed. Remaining repository snapshot committed at user request; no remote push or unrelated service deployment.

## 2026-10-09 Manual multiplier mode completed
User requested preserving manual badge selections. Added persistent keep/max policy and `monopoly mode keep|max|status` launcher commands. Set the active Pi to keep; live log confirms x5 retained with no automatic badge taps/probe while play continues. Keep reads the actual verified badge, respects later changes, and interrupts automatic probes/last-die adjustments on policy changes. Explicit one-off multiplier-max remains separate; max mode preserves bounded observed discovery and cooldowns. No finger monitoring or guessed numeric preference. Corrupt preferences fail to keep mode. Game-imposed insufficient-dice reductions remain possible.
146 tests pass Windows/Pi/Localnet. Current source/mirror/fallback hash bf74e43a1d91447cd3b8a6076cea42274461f6f29255c91d408093b0e4092ce0; Pi differs only by ADB path and hashes 1412505efb34ae07d4da6f954b056b1c289dc607a3074b8d7d2d58e840681519. Rollback manual-multiplier-final-20261009T211215Z; prior full launcher/preferences rollout backup manual-multiplier-20261009T210902Z. Active single Pi loop remains enabled; Localnet fallback inactive. Added skill guidance and source installer shortcut case. New dated commit follows the user-requested repository snapshot 29e591d. No remote push.
