

2026-09-23 railroad Chance recovery: live Halloween CHANCE / HEAD TO THE NEAREST RAILROAD IF YOU DARE card blocked at 95/60 dice. Specific white-card geometry plus exact OCR now precedes generic popup/purchase handling in both loop paths; two guarded center taps maximum, retries reset only after unobstructed screen. Unknown/purchase text is rejected; existing purchase/focus protections remain. 93 tests passed on workstation and Localnet. Live first tap advanced to match-3, which completed and collected its reward automatically. Single loop verified. Source, localnet-bin and both installed scripts SHA256 87d6598c0eaf3ee716a78a11c380ec88357c69c3b3d984495996f03cf07a83f1. Backup: ~/.local/state/monopoly-chance-backup. This handles the verified railroad card, not all future Chance designs.

2026-10-04 side free-item task: user requested checking side icons and automatically
using only free items. Added standalone high-confidence FREE icon scanning, a
separate free-gift button gate, price/lock/conditional/purchase rejection, bounded
claims and per-icon cooldowns, in both rolling and dice-wait paths. Existing shop
auto-polling remains disabled; general reward/purchase/focus protections preserved.
113 offline tests passed. Current source and executable mirror synchronized.
Live Pi deployment/font/layout verification pending its current SSH target;
the old localnet supervisor is inactive with no phone attached. No service or
real game was restarted/tapped during this source-only implementation.

- 2026-10-01 started: Install current assistant on the general Raspberry Pi with ARM dependencies, desktop launcher and monopoly shell command. Preserve localnet deployment and gameplay behavior; validate the deployed regression suite and service lifecycle.

- 2026-10-01 completed: General Pi desktop installation includes ARM ADB 34.0.5, Tesseract 5.5 with English, Pillow 11.1 and USB rules. install_pi.py preserves gameplay source except the deployment ADB path; 93 tests pass on ARM. Desktop launcher validated and visually inspected, trusted/executable, Bash alias confirmed. User systemd start/stop and repeat-start single PID verified. Runtime file logging used because initial user-journal query returned no records. Assistant currently running in waiting_for_device; no phone attached, so live gameplay/OCR performance remains unverified. Existing localnet service unchanged.

- 2026-10-02 in progress: Pi slow/stuck report traced to per-crop Tesseract process/model startup, quadratic button/raid clustering, and intermittent strict multiplier OCR failures. Added opt-in persistent OCR with state clearing and bounded recognition; same grid-neighbor semantics with direct lookup. 98 tests pass on Windows and Pi; identical saved-screen detector outputs at 16.132s versus 4.053s. Pi deployed with backups; live reward/Quick Wins recovery underway. Localnet runtime unchanged; workstation executable mirror synchronized.

- 2026-10-02 completed: Deployed final Pi assistant ff6cf82ede001451680ab495d01a559889fcb0b4e622186569cab39423090566. 101 tests pass locally and on ARM. Live verification: cleared Spooky Express reward, all three Quick Wins completed, BUILD opened/acted/closed successfully at 08:16:48-08:17:09, then resumed x10 rolls at 08:17:51 and 08:18:03. Screenshot shows actual rolling dice, 121/60 remaining and cleared BUILD badge; cash 1,126,220 after building. Observed consecutive ordinary rolls 12 seconds apart versus about 30 seconds previously; animation/OCR uncertainty can still pause. Existing exact reward/multiplier/focus/purchase guards retained. Pi service left running; localnet runtime unchanged.

- 2026-10-02 08:19 started: User requested one-hour full log/minigame/recovery review and evidence-led repairs for low-power devices. Audit window through 09:19 Eastern; inspect all historical localnet logs and current Pi, preserve purchase/focus guards, benchmark and test repairs, and observe live behavior.

- 2026-10-02 08:30 completed early at user direction: Reviewed 15 log files / 33,850,547 bytes including Pi snapshot. Archived and cleared the active Pi log and all 14 historical localnet Monopoly logs per user request, at 08:27. Deployed d50c06f8220baee511c470779d4c747b095ff9e5c0d034c578ed818b7f039585 on Pi: exact-frame multiplier cache plus preferred crop ordering, faster passive popup observation, bounded diagnostic snapshots, and performance counters. 105 tests pass on Windows and Pi. Live audit observed rolling, railroad Chance advancement, raid target/reward, purchase close and guarded popup recovery. End screenshot verifies normal GO board at 0/60. User shortened the hour to stop at GO; extra monitor stopped, assistant left active for replenishment. Review identifies remaining match-3 mid-sequence screen revalidation and repeated raid target-timeout hardening opportunities; these were not changed or live-validated before the requested stop. Historical unknown-popup layouts cannot be classified without screenshots. No new minigame universality claim. Localnet runtime remains previous version; workstation mirror synchronized.

2026-10-02 Halloween minigame repair started: Pi loop paused; five house rings visible, long player name wraps Board to second line and single-line OCR rejects event, causing false purchase classification. Added bounded block-OCR fallback using observed title crop.
2026-10-02 Halloween repair complete: 106 tests pass locally and Pi; deployed via existing Pi installer with backup, installed SHA256 ed5e3c85afa1a6ec6484f5d5b5900315861a472f15c04f413424ebf6ec28ce23. Three house choices advanced live. Manually dismissed observed one-time Win Win tutorial; ordinary board returned, then closed actual Midnight Sweets offer via observed X. Spooky Express 40-dice COLLECT reward visible. Local source and localnet-bin mirror synchronized; localnet runtime not changed. General tutorial support not added.
Final live verification: automatic COLLECT at 18:22:19, board visibly returned with 61/60 dice (was 21/60), Pi service active. One-time Win Win tutorial was manually advanced, not automated.

2026-10-03 BUILD false positive repaired: main-board GO sparkles triggered green card-icon fallback, causing close/Back/quit-cancel loop. Added dice-counter plus at least two distinct main-board navigation label exclusion before BUILD checks. 107 tests pass Windows/Pi. Pi installed hash 690ff1ef2c81b8ef4ab4828f3d3a912ee50d206dc259e87a98d0f232d5ffeeaa. Source mirror synced; live actual BUILD visit and return succeeded, multiplier probing resumed.

## 2026-10-04 Monopoly side-free update deployment
Deployed to rpi3 (jason user monopoly-assist.service), not the inactive localnet supervisor. All 113 tests passed on the Pi. Runtime SHA-256: 575399a13d09b62ce52bd269bf55d7d0ea281a750956b2bd18db6a28c3ad5266 (only ADB path adapted to /usr/bin/adb). Rollback: ~/.local/share/monopoly-assist/backups/20261004T210357Z. Confirmed active MainPID 155812 and exactly one assistant loop. Live screenshot showed the main board with zero dice and no side icon labeled FREE; actual free reward collection remains unverified. Initial staging encoding error was caught by tests and rolled back; corrected UTF-8 staging passed.


## Blocks Boutique (2026-10-04)
Observed through a 15-second ADB video and fresh 1080x2340 captures. Drag blocks
from the drawer onto the 8x8 grid. Complete rows/columns to clear blocks and
collect recipe materials. Each accepted placement uses one event token.
The tutorial's 3x3 placement cleared three columns: materials 7 -> 4,
tokens 13 -> 12. Two automated 2x3 placements then collected the remaining
materials (4 -> 2 -> complete), tokens 12 -> 11 -> 10. RECIPE COMPLETE showed
150 dice; its observed COLLECT control was pressed.

The handler runs before generic popup/build/roll detection in both loops.
Require bright RECIPE/MERCH ITEM book, four blue-frame anchors, known cell
colors, readable token count and fully observed connected drawer shapes.
Enumerate legal placements, prioritize collected materials and completed
lines, then remaining piece mobility. Use the fresh piece bounding-box center;
the calibrated destination places the ghost approximately 400px above the
finger. Always recheck exact game foreground before DOWN/MOVE and release UP
even on errors. After each drag, require predicted board and one-token reduction
before further placement; unexpected outcomes pause for review. Completion
animations/rewards pass to existing separately gated reward handling.

Zero tokens uses guarded Back; never buy refills. Unclear shapes, unreadable
cells/counts, changed layout, unchanged frame or failed placements pause rather
than guessing. Initial rectangle support was extended to observed connected L/T shapes and
material-bearing pieces; later mechanics remain unverified. 124 offline tests pass,
including a real captured grid fixture and focus/release safety regressions.

Follow-up: prize-cabinet NEXT is recognized before generic BUILD detection; live transition reached recipe 2 with 10 tokens. Two further predicted placements verified 10 -> 9 -> 8 tokens, including a T shape. See BOUTIQUE_WALKTHROUGH.md.

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

## 2026-10-06 In progress: board sparkle false BUILD detection and synchronization
Pi assistant was active but repeatedly classified the main board as BUILD. Paused the Pi user service for captures. Windows source matches the Pi runtime apart from the host-specific ADB path; LocalNet is stale and remains inactive. Reviewing a 15-second recording and sequential screenshots before a scoped detector correction, regression checks and synchronization. Existing Boutique autoplay stays disabled.

## 2026-10-06 Monitoring updates: sparkles and Color Wheel

Corrected false BUILD detection from GO sparkles with independent four-label
board navigation and a text-only footer OCR fallback. A 15-second recording
and five sequential captures produced 20 normal-board frames: old detector
classified all 20 as BUILD; corrected detector classified none as BUILD.

Live monitoring then exposed a genuine BUILD menu classified as Color Wheel
from green scenery. Wheel handling now requires the complete event title,
SPIN label, and a readable positive spins-left count. The current large title
needs separate enlarged bright-letter masks for COLOR and WHEEL; complete
words are required without guessed character repair. The real wheel capture
is accepted; BUILD and normal-board captures are rejected. Price-bearing
buttons and zero/unreadable counts remain blocked. Live free SPIN completed
and returned to the board. Normal BUILD close, rolls, rewards, and Quick Wins
were observed. Boutique autoplay remains default-off; unfinished/new layouts
are not assumed supported.

131 regression tests passed on Windows, rpi3, and LocalNet. Source, Windows
localnet-bin mirror, and both LocalNet runtime copies match byte-for-byte;
Pi differs only in the ADB executable path. Stage as UTF-8 with LF endings.
Pi user service remains active; LocalNet fallback supervisor remains inactive.
Backups: Pi ~/.local/share/monopoly-assist/backups/sparkle-fix-*,
wheel-title-fix-20261006, wheel-layout-fix-20261006; LocalNet
~/.local/state/monopoly-sync-backups/.

Normalized source SHA256: 6b54037e3c7bf0fca357b36a590b3ff5c63d169493914256b0cf6ee9626df19e

20-minute live watch completed: October 6, 2026, 10:52:10 PM to 11:12:10 PM America/New_York, including bounded pauses to validate the fixes. Normal play remains enabled; final service/hash verification follows.

### Final follow-up after the 20-minute watch
Confirmed-board navigation now short-circuits Color Wheel outlined-title OCR during multiplier checks. Live board classification measured 0.652s; the saved real wheel remained accepted and the saved BUILD menu rejected. 132 tests passed on all three hosts. Additional validation continued after the watch; Pi normal play remains active. Final normalized source SHA256: 48a1da7dabcc8900dbba3d13af788a86c213468ef4f136d1a2d7216d30c63821
2026-10-09 Halloween title-separator fix started/completed: current captured five-ring board OCR inserted a vertical separator before wrapped BOARD, missing the house handler and falling into BUILD/raid. Added strict separator/whitespace title predicate, preserving foreground, multi-ring and bounded-attempt checks. 134 tests pass Windows/Pi; initial system Python lacked Pillow, so reused existing GPU package venv without dependency changes. Active Pi rollback house-separator-20261009T201542Z. Live rings5->4 and treats0->9, then autonomous return to board and normal play verified; one loop PID462017. Device-connect idle monitoring enhancement requested next; in progress.

## 2026-10-09 Mini-game recovery and phone monitoring completed
Halloween wrapped-title fix is committed as 74a2b17; Spooky Express overview recovery is committed separately as 3bfc73d, with its introduction date in the subject/body and MINIGAME_HISTORY.md. Added a Git note to first tracked snapshot f229c71 with dated evidence for raid/heist, match-3, jail/bonus rolls, Color Wheel, Pick a Box, treasure, Halloween houses and Blocks Boutique. Historical commit dates were preserved. Boutique autoplay remains default-off.
Live house-choice recovery verified rings 5->4, treats 0->9, further automatic choices, return to board and normal play. New Spooky Express First Class overview (13 points, reach45) closed through its verified grey footer X; no upgrade/purchase action. 137 tests passed before phone monitoring; 141 pass after it on Windows/Pi/Localnet. Physical unplug/replug remains unverified; simulated missing/unauthorized/offline/multiple-device, device swap, foreground and unsupported-layout cases pass. Active Pi loop recognized the authorized phone, serial-bound commands and checked game focus before publishing a calibrated frame. One loop remains active; Localnet supervisor remains inactive. Source/localnet-bin and both fallback executables have identical hash cc5ddacfc644e881f4ad67fff7544b5f5fa4bfc8640f13262da6959358525bbd; Pi runtime differs only in /usr/bin/adb and hashes 318737c7c91faa0d30ad8f22b0b76e331e1cf13a93663132e0a267e6dca92041. Rollbacks: house-separator-20261009T201542Z, spooky-express-20261009T203115Z and device-monitor-20261009T204013Z under the Pi user's .local/state/monopoly-assist/backups. No new third-party dependencies.

## 2026-10-09 Manual multiplier mode completed
User requested preserving manual badge selections. Added persistent keep/max policy and `monopoly mode keep|max|status` launcher commands. Set the active Pi to keep; live log confirms x5 retained with no automatic badge taps/probe while play continues. Keep reads the actual verified badge, respects later changes, and interrupts automatic probes/last-die adjustments on policy changes. Explicit one-off multiplier-max remains separate; max mode preserves bounded observed discovery and cooldowns. No finger monitoring or guessed numeric preference. Corrupt preferences fail to keep mode. Game-imposed insufficient-dice reductions remain possible.
146 tests pass Windows/Pi/Localnet. Current source/mirror/fallback hash bf74e43a1d91447cd3b8a6076cea42274461f6f29255c91d408093b0e4092ce0; Pi differs only by ADB path and hashes 1412505efb34ae07d4da6f954b056b1c289dc607a3074b8d7d2d58e840681519. Rollback manual-multiplier-final-20261009T211215Z; prior full launcher/preferences rollout backup manual-multiplier-20261009T210902Z. Active single Pi loop remains enabled; Localnet fallback inactive. Added skill guidance and source installer shortcut case. New dated commit follows the user-requested repository snapshot 29e591d. No remote push.

## 2026-10-09 Space-themed raid recovery completed
The observed space-themed raid stalled because a white background cross was treated as a target. Detect measured red ring reticles first; require angular ring coverage for white targets too, rejecting crosses and filled squares. Raid support was documented September 6, 2026; this is a variant fix, not a new mini-game introduction. Existing foreground, purchase, bounded-action and multiplier guards remain intact.
149 tests passed on Windows, Pi and Localnet. Live guarded recovery selected the actual red target, detected/tapped COLLECT and returned to the normal board. The single Pi user service resumed normal play; keep mode preserves the observed x5 badge. Rollback: ~/.local/state/monopoly-assist/backups/space-raid-20261009T213034Z. Source SHA256: ae49842cffb83e70757e8f66b409adc6d2358edee9e783b7d9ebb1b80d7f8665; Pi changes only the ADB path and hashes 2cf996d4f6432342b26ba652fa4c847f586a4c4257e3836b19856a5574f816ba. Localnet fallback remains inactive.
