---
name: monopoly-assist
description: Diagnose and deploy the existing Monopoly GO automation, including stuck box/jail/blue SPIN screens and selecting the maximum available roll multiplier.
---

# Monopoly assistant

Source is `tools/python/monopolyAssistant`; read its RULES.md before edits.
Live copies are `${SERVICE_USER_HOME}/bin/monopoly-go-assist` and
`/ai/monopolygo/monopoly-go-assist`. The `python/localnet-bin` source copy must
also stay synchronized. Compare current files; preserve unrelated fixes.

Specific box/purple-roll handlers precede broad BUILD detection. Blue SPIN
must not match a quit dialog without OCR confirmation. Screen coordinates can
drift: inspect a current screenshot before recalibrating them. Never tap a
purchase dialog body; preserve the existing purchase-dismissal rules.

Discover the available multiplier by bounded observed cycling, not a hardcoded
x3 or x20. Stop on unreadable OCR or a blocking popup. A tap-count bound is not
proof of the maximum. After wraparound, settle at the observed maximum before
rolling. Never make an extra tap using the pre-probe reading: it can reset the
badge. Failed probes must not fall back to tapping through a popup. Re-probe
changed values and periodically check for a changed event/dice cap.

Run `python -m unittest test_monopoly_go_assist -q` in the source directory.
Test maximum discovery, stale-reading/reset regression, interrupted probes,
bounded termination, and existing box/jail/SPIN precedence. Deploy LF line
endings, back up both live scripts, stop only `monopoly-go-supervisor`, install
identical scripts, restart it, and verify a single running loop and hashes.
Run live readback when the board permits; do not report a higher live cap unless
observed. Record unobserved event paths separately from test results.

Unreadable x1/x5 badge OCR has a calibrated two-crop, color/mask consensus fallback. Preserve rejection of incomplete or disagreeing readings; never replace letters with guessed digits.

Wait for badge animation before OCR (currently 2s). Prefer complete matching color/mask consensus over single digit OCR; x1 has been misread x4. Verify actual board/dice/reward changes before reporting rolling resumed.

Never restore loose-digit OCR fallback for multipliers. Two full matching reads are required. Preserve the 60-second re-probe cooldown to avoid continuous cycling after uncertain OCR or a changed badge.

Performance maintenance: reuse the decoded screenshot across detectors and
invalidate frame/OCR caches after each capture or external file replacement.
Do not restore the old 3%-only empty-dice test: live 3/60 has only 2.79% fill.
The low-fill exception requires a contiguous 3-column, 3-row blue patch.
Empty-dice backoff checks every 15 seconds; animation and multiplier safety
waits remain. Benchmark claims must distinguish pixel checks from total play.

Check confirmed empty dice before multiplier verification. At zero dice,
monitor for replenishment without cycling the badge. Run all 47 regression
tests, including the empty-dice no-tap case and frame-cache invalidation.

Themed BUILD menus may defeat both header color and price OCR. Preserve the
named-city 0..30/30 footer fallback. Verify close with fresh frames, recheck the
menu before each card tap, and preserve visit cooldown/budget. Check returned
dice before considering BUILD during backoff. Current suite: 52 tests.

Purchase-loop protection: automatic shop visits are disabled; unknown dimmed
popups pause without blind taps, and detected orange-X purchase dialogs receive
at most two close attempts until the modal clears. Reward chains stop on detected
purchase dialogs. See monopolyAssistant/RULES.md; regression suite now 56 tests.

Billing guard follow-up: check exact game foreground before each tap, reject price/locked FREE buttons as rewards, and preserve high-position orange-X detection. 60 tests pass; actual Profit Herder offer closed live. See current monopolyAssistant/RULES.md for deployment and limitations.

Full-log audit follow-up: preserve validated raw capture geometry/payload, per-process private OCR/frame files, loop lock, foreground waiting, and 60s failed BUILD-close cooldown. Both main and dice-wait paths must reject blind popup taps. Never restore unconditional unlock swipes. Use STATE timestamps/heartbeats for future downtime reports; 70 tests currently pass. See monopolyAssistant/LOG_AUDIT_20260922.md.

Preserve last-die rounded-edge detection (3x5 blue patch) and bounded building during dice waits after dice/event checks. Unknown dimmed popups have at most two guarded Android Back attempts after settling; failed BUILD closes have one Back fallback before cooldown. Exact game foreground remains required. 74 tests pass; reconnect and BUILD return verified live. See audit follow-up.

Confirmed last-die edge case must use x1 rather than re-probing the selectable x3 that resets on GO. This exception is live-verified; 76 tests pass. Preserve normal max discovery when more dice are available.

Quick Wins gift badge must be checked during dice waiting as well as rolling, with a 5-minute reopen cooldown. Verified Quick Wins/milestone/completion screens precede orange-confetti detection and require exact reward-label OCR before claims. See RULES.md Quick Wins decisions; 79 tests pass.

Treasure digging precedes generic popup/build/roll handlers. Verify event, hammer count and blue-star tile components before one bounded action. Do not spend on unreadable counts or infer paid refills. See RULES.md treasure section; 83 tests.

Treasure event must exit at zero hammers, 45s without progress, or 10min per visit. Verify the close before assuming return; bound retries. Gold-star grids currently exit via watchdog instead of being solved. 86 tests; see RULES.md.

Productive treasure play has no fixed visit cap. Gold-star tile detection and separate color components are supported; retain 45-second stall exit, zero-hammer exit, and bounded tile retries. 87 tests. See latest RULES.md section; supersedes earlier gold-star limitation.

2026-10-09 maintenance: active host is the Pi user service documented in the source RULES.md; Localnet fallback stays inactive. Wrapped Halloween board titles accept only the observed separator before BOARD plus verified rings. Spooky Express overview recovery requires exact event/progress text and the measured grey footer cross; no upgrade/purchase body taps. Dated introduction evidence and Git comments are in MINIGAME_HISTORY.md.

Device monitoring distinguishes missing, unauthorized, offline, multiple/configured devices and permissions. Only an authorized selected serial with game foreground and calibrated geometry may receive input. Clear cached game state on device changes; do not enable debugging, unlock or launch the game remotely. Five-second idle polling; physical swap acceptance remains separately unverified.

Respect the user's persistent multiplier policy. Keep mode never automatically taps/probes the badge and preserves subsequent manual selections. Max mode retains bounded observed cap discovery and cooldowns. Use `monopoly mode keep|max|status`; current active Pi is set to keep by user request. Explicit one-off multiplier-max is separate. Game-imposed low-dice reductions can still occur. Current regression suite: 146 tests on Windows, Pi and Localnet.
