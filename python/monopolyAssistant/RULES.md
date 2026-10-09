# Monopoly GO Automation Notes

## 2026-10-09 Manual multiplier preference

Persistent keep/max policy is stored in the user's private preferences file and
read at each multiplier check. Keep mode retains any readable current value,
including subsequent manual changes; no automatic badge tap or max probe is
performed. Unreadable OCR still pauses instead of guessing. Automatic probes
check for keep mode before each tap and stop when the policy changes. Automatic
maximum mode retains its previous bounded, observed discovery and cooldown rules.
The user requested keep mode on the active Pi. The game can still reduce a value
when insufficient dice are available. This policy does not observe finger input
or infer who changed the badge. The CLI preference requires no connected device.

## 2026-10-09 Authorized-device monitoring

The continuous service polls `adb devices -l` every five seconds while waiting.
It distinguishes no/configured/multiple devices, unauthorized debugging, offline
transport and missing permissions. Only one authorized device, or an explicitly
configured `MONOPOLY_DEVICE_SERIAL`, is eligible. It checks exact game foreground
before capture, validates the calibrated raw-frame geometry, and rechecks focus
before every input. All capture/focus/input commands are serial-bound. Device
changes clear old frame/OCR/multiplier and mini-game state; no stale cross-device
gesture is allowed. Debugging-disabled devices are not ADB-visible and remain
idle until debugging is enabled/approved on the phone. No automatic app launch,
screen unlock, authorization approval or recalibration is performed.

141 Windows and Pi tests pass, including simulated missing/unauthorized/offline/
multiple devices, device swap, other-app focus and unsupported layout. Live Pi
service detected the authorized phone and published only a validated game frame.
Physical unplug/replug on another phone remains unverified.

## 2026-10-09 Spooky Express overview

The observed First Class progress overview displayed 13 points and "Reach 45 to
upgrade". It replaced the board HUD and defeated generic popup recovery.
The specific handler precedes generic screen checks in both play and dice-wait
loops. Require complete SPOOKY and EXPRESS header words, REACH/TO UPGRADE text,
and the measured small grey cross in the footer. Tap only that detected cross,
recheck a fresh frame, and allow two attempts before a 30-second cooldown.
Never tap the upgrade body, buy points, or infer free upgrades from this screen.
137 tests passed on Windows and Pi; the live close returned to the main board.
The entry date is recorded separately in MINIGAME_HISTORY.md.

## 2026-10-09 Halloween title separator recovery

The current house-choice screen was repeatedly sent through BUILD and raid
fallbacks. Five calibrated rings were correctly detected, but title OCR returned
`AgileGopher42’s |` followed by `Board`, causing the whitespace-only title matcher
to fail. The title predicate now accepts the observed vertical separator and
whitespace between the possessive name and the complete word BOARD. It still
requires multiple ring targets and rejects misspelled words, prices and unrelated
text. Existing two-attempt bounds, foreground and purchase protections remain.

134 tests passed on Windows and the active Pi. A live guarded choice reduced
the available rings from five to four and increased treats from zero to nine.
The restarted single loop made subsequent choices, returned to normal board
play and resumed verified multiplier/roll handling. Boutique remains default-off.
See MINIGAME_HISTORY.md for dated support milestones and Git-note annotations.

## 2026-10-06 GO sparkle false BUILD recovery

The live main board was repeatedly treated as an open BUILD menu: its GO
sparkles satisfied the broad green-icon fallback while block OCR read
`WINS | BUILD | | ALBUM | FRIENDS` but omitted the visible dice fraction.
All four exact navigation labels in the existing bottom-footer crop now
exclude BUILD independently of dice OCR. If sparkle-heavy block segmentation
also misses a navigation label, read the calibrated text-only navigation row
(0,2200,1080,2260) with PSM 7 before considering green icons. Partial navigation still requires
the prior dice-fraction evidence; genuine BUILD city/progress and price
fallbacks remain. This is not a blanket exemption for green pixels.

Captured a 15-second video and five successive screenshots with different
sparkle patterns. The regression fails before the change; 127 offline tests
pass on Windows. Pi frame validation and deployment are recorded in TASKS.md.
Boutique autoplay remains default-off and its unfinished development deferred.

Active host: rpi3, user service `monopoly-assist.service`. LocalNet retains
synchronized fallback copies but its old supervisor stays inactive while the
phone is attached to the Pi. Windows source and localnet-bin mirror must match;
the Pi runtime differs only in its `/usr/bin/adb` executable path.

Live monitoring also exposed a false Color Wheel classification on a genuine
BUILD menu: its green scenery matches the historical single color sample.
That sample now only triggers a title check; exact COLOR WHEEL text is required
before SPIN handling. BUILD/scenery, Net Worth Gallery and unknown text fail
that check. 129 regression tests pass; legitimate live Color Wheel title OCR
will be verified when that event is encountered.

## Side-icon free items (2026-10-04, source implementation)

Both rolling and dice-wait paths check every five minutes, using a fresh capture
and verified main-board footer. Scan both side strips for high-confidence,
standalone FREE/FREE! labels; use their current OCR positions, never a stored
tap coordinate. Icons without a readable FREE label are not opened. Each icon
position has a fifteen-minute revisit cooldown; one icon is examined per visit.

Inside an offer, require a recognized DAILY GIFT/FREE GIFT/FREE REWARD context,
one exact FREE label, a matching green button shape and a second exact local OCR
read. Reject prices, locked/conditional labels, ads, unclear geometry and detected
purchase popups. Keep the general reward-label rule rejecting FREE unchanged;
this is a separate narrowly gated handler. Up to three freshly verified free
stages per visit, then existing guarded collection/one guarded Back. No purchase,
paid unlock, inventory spending, billing interaction or automatic shop polling.

113 offline tests pass. Live side-icon/font/layout verification and Pi deployment
are pending the current Pi SSH connection; localnet is inactive with no ADB device.
Mixed paid/free offer screens are deliberately skipped. This does not claim
support for every side event or for icons without visible FREE text.

## Raspberry Pi performance update (2026-10-02)

Optional in-process OCR (`MONOPOLY_INPROCESS_OCR=1`, `python3-tesserocr`)
reuses the English language model but clears recognition/adaptive state for
every image. Recognition is bounded to 30 seconds; timeout returns no text.
Exact reward labels, dual complete multiplier consensus, fresh focus checks,
and existing animation settling remain mandatory. CLI OCR remains the default
outside the Pi service. Green-button and raid connected components use direct
grid-neighbor lookup with the same two-grid-step neighborhood and thresholds.
Saved Pi reward-screen comparison: identical outputs for 13 detector calls,
16.132s baseline versus 4.053s optimized (includes first OCR initialization).
This is a detector benchmark, not a fourfold end-to-end gameplay claim.
98 regression tests pass, including native OCR state reset/timeout/fallback,
TSV coordinate handling, and two-step green-component connectivity.

Confirmed working rules and coordinates from live testing on the real phone
(device screen: 1080x2340). All screenshots via
`adb exec-out screencap -p`; all taps via `adb shell input tap X Y`.

## IMPORTANT: coordinates drift — recalibrate, don't trust blindly

The board camera pans/zooms constantly, and fixed HUD elements can still be
off from a first visual guess (we were wrong by 500+ px vertically on the
BUILD icon before correcting it). **Don't hardcode these forever.** The
reliable method that worked every time:

1. Take a screenshot (`adb exec-out screencap -p`).
2. Crop the relevant region and inspect it directly, OR color-match a
   distinctive element's RGB value with a small Python/PIL script
   (flood-fill / bounding-box on a tight color range, restricted to a
   narrow region of the screen to avoid matching similar colors elsewhere
   on the board).
3. Compute the center of the matched region and tap that.

Pure visual estimation from a description of a scaled-down image is
unreliable — every coordinate bug we hit this session came from that.

## Confirmed mechanics

### GO button (dice roll)
- Real button center (this session, this camera position): **(539, 1901)**.
  Earlier guesses of (538, 1574) and (538, 1346) were both wrong — landed on
  the pannable board instead of the button, causing silent failures that
  looked like "long-press doesn't work."
- **Single tap** (red/orange state, "GO / HOLD FOR AUTO"): one manual roll.
- **Long-press ~1-3s** (genuine held touch — see note below) transitions to
  **green "TAP TO STOP"** state = continuous auto-roll. Confirmed via a real
  manual hold; synthetic `adb input swipe` and `input motionevent DOWN/UP`
  at the *wrong* coordinates repeatedly failed. Once the coordinates were
  corrected, `input motionevent DOWN` + periodic `MOVE` keepalive + hold +
  `UP` **did** successfully trigger it synthetically.
- **Single tap while green** → stops auto-roll, reverts to red.
- Roll count is shown in the blue pill above the bottom nav (e.g. "86/30").
  It can exceed 30; that number is not a hard cap.
- **SUPERSEDED RULE (kept for history only, do not use):** the original
  agreed rule was "<2 remaining → single tap; >10 remaining → long-press
  for auto-roll." This required accurately reading an exact roll count,
  which OCR could never do reliably (see below) — the long-press/threshold
  approach was abandoned.
- **CURRENT RULE, confirmed via live play (2026-09-06):** always single-tap
  GO as long as the pill is not genuinely empty (0/0). Never long-press as
  part of automation. Only exception: if the pill reads empty, stop tapping
  and back off for a fixed interval before rechecking (see "Roll-count
  reading" below) rather than busy-polling or guessing the countdown timer.
  User's own words: *"as long as it is not 0/0, we can keep rolling single
  (not 3x)"* and *"if it is 0/0, we need to wait the remaining time."*

### Roll-count reading: OCR abandoned, color fill-ratio heuristic used instead
- Tesseract OCR was tried against the roll pill across ~10 preprocessing
  variants (tight crop, binarize+upscale, digit-whitelist, alternate `--psm`
  modes) and never reliably read the stylized bold-white-on-color pill font.
  Reading the "5 Rolls ready in HH:MM" countdown text was tried too and also
  produced garbled output on both attempts. **OCR is not usable for this
  element on this game.** (Multiplier badge OCR still works reasonably —
  see below — because that font/background is less busy.)
- Replacement approach, agreed with the user via an explicit choice between
  "call a vision-capable API," "use a local color heuristic," or "skip
  auto-detection": use a **local, fully-offline color-based fill-ratio
  heuristic** — scan a fixed horizontal line through the pill and measure
  what fraction of its width is still "filled" (blue) vs "empty" (dark
  olive/tan background).
  - Scan line: `y = 2152`, `x` from `380` to `703` (device 1080x2340).
  - A pixel counts as "filled" if `b > 200 and g > 140 and r < 220 and b > r`
    (i.e. distinctly blue, not the dark olive empty-track color).
  - `fill_ratio = filled_pixel_count / (703 - 380)`.
  - Calibration check: a real, visually-confirmed "17/30" reading measured
    ~60.7% fill; the naive expectation (17/30 = 56.7%) is close enough to
    validate the approach (the pill isn't perfectly linear/edge-padded, but
    it's consistent enough to classify "has rolls" vs "empty").
  - Empty/0-0 threshold: `fill_ratio < 0.03` → treat as genuinely empty.
    Anything at or above that → "has rolls," single-tap GO.
  - When empty, back off **60 seconds** before rechecking (a fixed backoff,
    not an attempt to parse the exact countdown — the countdown text also
    resisted OCR, and 60s was judged an acceptable, non-aggressive poll
    interval rather than something calibrated to the actual regen rate).
  - This whole calibration methodology (fixed scan line + RGB threshold +
    ratio, verified via a real known reading) is the general pattern to
    reuse for any other progress-bar-style element in this game if OCR
    fails on it again.

### Multiplier badge (next to GO button)
- Appears after a tutorial prompt; badge coordinates this session: **(725, 1740)**.
- Tapping is free (no cash/roll cost) and cycles: **x1 → x2 → ... → cap → back to x1**.
- **The cap is NOT assumed fixed at x3.** x3 was the only ceiling ever
  observed as of 2026-09-06, but nothing guarantees a live boosted-rewards
  event can't raise it - see "Multiplier max: bounded observed cycling
  (2026-09-19)" below for how the automation now discovers the real,
  currently-available cap instead of hardcoding one, and do NOT reintroduce
  a hardcoded cap assumption without live re-confirmation.
- Popup "ALL REWARDS x2 / x3" confirms the current multiplier level (also
  seen at higher values during boosted events, per the same popup pattern).

### BUILD (bottom nav, hammer icon)
- Icon center this session: **(256, 2137)** — NOT (257, 1591), which was a
  bad guess that silently did nothing (~550px off).
- Red badge (e.g. "5") is just a "things need building" indicator, not a
  stable anchor — anchor on the hammer icon itself instead.
- Opens a build menu (e.g. "LONDON 0/30") with 5 purchasable building cards
  along the bottom, each with an increasing cash cost. Buying one:
  - Deducts cash immediately (e.g. 29,343 → 27,543 for a 1,800 purchase).
  - Increments the city-wide counter (e.g. "LONDON 0/30" → "1/30").
  - Increments that specific building's star progress and raises its next
    purchase price (e.g. 1,800 → 2,400 for the same card).
  - Triggers a brief dust-cloud construction animation on the 3D city view.
- **Multiple building cards can be tapped in sequence without waiting** for
  each animation to finish (confirmed by the user).
- **To leave the build menu**: tap the **X** just below the city name
  (e.g. "LONDON 1/30"), a darker-tan/shade button. Coordinates this
  session: **(538, 2267)**. Confirmed working — returns cleanly to the main
  board with no cash/state side effects.

### Roll <-> Build cycle (the core loop)
1. Roll (manually or via auto-roll) on the main board to earn cash.
2. The BUILD hammer icon shows a red badge (e.g. "5") whenever there are
   purchasable/affordable building upgrades pending in the current city set.
3. Open BUILD, buy whatever is affordable/desired (can tap multiple cards
   back-to-back), then tap the **X** (538, 2267 this session) to close it.
4. Resume rolling. Repeat: roll until more purchases are affordable or the
   badge count changes again, then reopen BUILD.
5. This is the loop the local AI should run for "handle the basics":
   roll -> (periodically) check/open BUILD -> buy what's affordable -> close
   -> keep rolling.

### Raid / heist flow (opponent boards)
1. From the main board, landing on certain tiles opens an opponent's board
   (e.g. "Alfredo's Board", "SharpSun92's Board") with several glowing
   circular target reticles over specific buildings.
2. **Buildings already showing smoke/beam effects at their base should be
   avoided** — tap a target that looks clean instead.
3. Tapping a clean target triggers a crane/wrecking-ball demolition
   animation (fully automatic, no further input needed) which resolves
   into a cash reward and returns to the main board.
4. Separately, some tiles open a **"Match 3 to steal"** mini-game on a
   specific opponent's bank: a 4x3 grid of 12 face-down tiles. Flipping
   tiles reveals icons (coin, cash stack, ring, etc.); matching 3 of the
   same icon completes that reward category (shown highlighted at the top
   of the screen) and pays out automatically.
   - Tile grid coordinates from this session's layout (4 cols x 3 rows):
     x = 175, 420, 652, 895 / y = 1132, 1452, 1772 (12 combinations).
   - These were found via color-matching the tiles' yellow card-back color
     with a flood-fill blob detector, restricted to the grid's on-screen
     region — same recalibration method as above, needed again if the
     layout/resolution differs.

## Tooling already built (on localnet, ~/bin, auto-exposed to Open WebUI)

- `android-adb` — devices/install/uninstall/logcat/shell/home/back/recents/
  pair/connect/disconnect (guarded allowlist, no fastboot/bootloader).
- `android-gradle` — build/test wrapper for Android projects (task allowlist).
- `android-emulator` — start/start-gui/wait/stop/status for the AVD, with a
  live boot-progress bar and automatic on-screen-keyboard fix.
- `android-tap-record` — tap + before/after screenshot pair + JSONL log,
  for building a training dataset of interactions.
- `android-screen-record` — start/stop/loop/stop-loop/status screen
  recording via `adb screenrecord`, saves to `/ai/android-training-data/`.
- `monopoly-go-assist` — the "local AI handles the basics" script
  (`~/bin/monopoly-go-assist` on localnet, Python 3; mirrored at
  `C:\projects\tools\python\localnet-bin\monopoly-go-assist` on Windows).
  Current commands (`roll|multiplier|build|match3|loop|status`):
  - `monopoly-go-assist roll` — reads the roll pill's color fill-ratio (see
    "Roll-count reading" above), single-taps GO if not empty, otherwise
    prints a message and returns exit code `2` ("empty, back off") without
    tapping. Returns `0` on a normal tap.
  - `monopoly-go-assist multiplier` — OCRs the multiplier badge
    (`tesseract`, region `(685,1700,765,1785)`), taps it only if below x3
    (never triggers the x3→x1 reset). The multiplier-parsing regex was
    fixed this session: it no longer requires seeing a literal "x" in the
    OCR output (tesseract often drops it) — it now strips all non-digit
    characters and takes the first digit that is 1, 2, or 3. Confirmed live:
    raw OCR `'"x3'` → correctly parsed as `3`.
  - `monopoly-go-assist status` — reports the roll pill's fill ratio (with
    an EMPTY/has-rolls label) and the multiplier reading, no action taken.
  - `monopoly-go-assist build` — opens BUILD, taps all 5 card slots once
    each (harmless no-op if unaffordable), closes via the X. Fully wired in.
  - `monopoly-go-assist match3` — **confirmed working live** (real cash
    payout followed, 36,523 -> 42,093). Blind-flips all 12 tiles in the
    known grid with no memory/strategy — reveals everything in sequence
    rather than screenshotting after every single tile. This is
    deliberately "dumb": matches still happen by chance as pairs/triples
    line up, and it's much faster than checking a screenshot after each
    tap. Good enough for "handle the basics"; a smarter version would
    remember revealed icons and target known pairs, but that's not built.
  - `monopoly-go-assist loop` — ties everything together each tick: checks
    for (in priority order) the COLLECT reward popup, then the match-3
    mini-game, then the "Roll Doubles" bonus event, then falls through to
    normal roll+multiplier+badge-driven build. If `roll` returns `2` (pill
    empty), the loop sleeps a full 60s (`ROLL_EMPTY_BACKOFF_S`) before its
    next check instead of the normal 4s interval, so it doesn't busy-poll
    while waiting for rolls to regenerate. Runs until stopped (Ctrl-C).
    This is the actual "wire it all together" entry point.
  - **Badge-driven BUILD (2026-09-06, confirmed live, supersedes the
    original fixed ~15-tick interval)**: `is_build_badge_present()` scans
    a horizontal band (`BUILD_BADGE_Y=2069`, x in `270-360`) for the red
    badge's solid-red color (`r>180,g<90,b<90`) — calibrated against a real
    badge showing "1" (center ~(316,2069)). The loop opens BUILD the
    instant this badge appears, instead of waiting on a fixed schedule; a
    ~6min fixed-interval fallback (`tick % 90`) remains as a safety net in
    case the badge check ever misses. **Observed live**: the badge can stay
    lit across several consecutive BUILD open/close cycles (a persistent
    landmark/big-ticket item, not just per-roll upgrades) — this is
    expected, not a bug; the loop just keeps trying each tick until it
    clears.
  - **"Roll Doubles" bonus mini-event (2026-09-06, confirmed live)**: a
    limited-roll bonus round (title card "ROLL DOUBLES / Win [dice] x1",
    "N Rolls Left" footer) triggered by landing on certain tiles. It
    replaces the normal GO button and roll pill entirely with its own
    **purple diamond "ROLL" button** — without detecting this, `cmd_roll()`
    reads the (nonexistent) roll pill as empty and the bot gets stuck doing
    nothing, which is exactly what happened live before this fix (user
    report: "the current screen gets our AI stuck"). Detected via
    `is_bonus_roll_screen()` at `BONUS_ROLL_BUTTON = (535, 1845)`. Confirmed
    live: the loop tapped through a real "3 Rolls Left" event (4 taps
    observed) and correctly fell through back to normal play once the
    event ended.
  - **`is_bonus_roll_screen()` false-positive, two rounds of fixes
    (2026-09-06 night into 2026-09-07 morning)**: the original single-point
    purple check (`b>140, 90<r<200, b>g, b>r`) turned out too loose twice:
    (1) a raid-win celebration screen's confetti animation put a
    matching-purple stray piece on that exact pixel, causing repeated false
    detection on what was actually a COLLECT popup - fixed by checking a
    5-point cluster around the button and requiring 4/5 to match, on the
    theory that a large solid button covers a spread of points but a small
    confetti piece doesn't. (2) That fix wasn't enough: a *different* raid
    board's blue-grey industrial background theme (~188,189,199) uniformly
    satisfied the loose color test across the *entire* checked area (not
    localized noise, so the cluster/majority check didn't help), causing a
    long, unbroken false-positive streak that looked identical in the logs
    to a real stuck bonus-roll loop. Root cause: the check only required
    `b>g and b>r` (blue-ish), which passes for grey/blue tones with r≈g≈b,
    not just true purple. **Final fix**: also require a real "green valley"
    - `g < r - 20 and g < b - 20` - since the calibrated real button
    (161,117,194) has g meaningfully below both r and b, while grey-blue
    background tones don't. Confirmed live: the exact false-positive raid
    screenshot now correctly reads `bonus_roll=False, raid=True`, the real
    bonus-roll event still reads `bonus_roll=True`, and the loop was
    observed handling a real raid immediately after this fix deployed.
    **Lesson for future color-based detectors in this file**: a loose
    "greater than" color check (e.g. "b > g") is not the same as actually
    matching a color family - verify against a genuinely different-hued
    false-positive case (not just "no popup showing"), and prefer checking
    for a real hue signature (a channel *meaningfully* below/above the
    others) over simple pairwise comparisons.
  - **Phone screen lock / "stay awake" (2026-09-06)**: the phone's screen
    timed out and locked mid-session (observed directly — a screenshot
    showed the lock screen) despite being at 100% battery and on USB
    power/charge. Once locked, screenshots show the lock screen and taps
    don't reach the game, silently breaking automation. A plain
    `adb shell input swipe` (bottom of screen to top) was enough to unlock
    it live — **no PIN/pattern is configured**, so this is recoverable via
    adb alone. The durable fix is enabling **Developer Options → "Stay
    awake"** on the phone itself (keeps the screen on continuously while
    charging, which this phone always is for this setup) — this has NOT
    yet been toggled as of this writing; until it is, expect the phone to
    lock periodically during long unattended `loop` runs. `loop` does not
    yet auto-detect-and-unlock the lock screen; consider adding that as a
    safety net (same swipe-based unlock, gated on detecting the lock
    screen's dark background) if "Stay awake" isn't enabled or isn't
    sufficient.
  - **Match-3 mini-game is now fully auto-integrated (2026-09-06),
    confirmed live end-to-end**: while running `loop` unattended, it
    detected an active match-3 screen mid-game, played it via `cmd_match3`,
    and the tile matches actually completed a real "Large Heist" steal —
    **won 20,000 from a bankrupted opponent's bank**, confirmed by the
    on-screen "You stole from PlayfulBadger10 and won: 20,000" + COLLECT
    popup. Detection method: `is_match3_screen()` samples the same 12
    fixed grid points `cmd_match3()` taps, and classifies "gold card-back"
    color (`r>200, 170<g<240, 50<b<110`) — calibrated at 9/12 gold hits on
    a real match-3 screenshot vs 0/12 on the main board; the loop treats
    >=5/12 as "we're on this screen" (tolerant of some tiles already
    flipped, which show dark/icon colors instead of gold).
  - **COLLECT popup auto-dismissal (2026-09-06, confirmed live)**: after a
    match-3 win (and presumably other reward popups sharing this button —
    not yet confirmed for non-match3 rewards), a green "COLLECT" button
    appears and must be tapped to return to the main board; without this,
    the loop would sit reading the roll pill as false-empty (occluded by
    the popup) and back off for no reason. Detected via a single calibrated
    point: `COLLECT_BUTTON = (540, 2130)`, which sits in the solid-green
    area just above the white "COLLECT" lettering (the button's exact
    center, (540,2182), reads as white text, not green — don't use that
    point). Checked *before* `is_match3_screen()` in the loop, since the
    popup renders on top of the match-3 grid and would otherwise block it
    from ever being dismissed.
  - **Raid/heist target selection is now auto-integrated (2026-09-06,
    confirmed live)**: the loop caught a real raid (`is_raid_screen()`
    gates on the olive "SWITCH OPPONENT" button, calibrated point
    `(540,2230)` ± tol 20 color-match against `(201,189,121)` — reads as
    plain cream on the main board, no cross-over). Once on that screen,
    `find_raid_targets()` locates the glowing white circular reticles via a
    connected-components blob scan (step=3 grid sample, `y` in `300-2180`
    to exclude header/footer) looking for near-white (`r,g,b>235`) clusters
    with a roughly square bounding box in `100-200px` per side and `>=400`
    sample points — calibrated against a real 3-target screen where all
    three reticles independently produced ~150x150px / ~700-point clusters,
    cleanly distinct from sky/cloud/header/footer noise (which are either
    much smaller or wide-and-short rather than square). `cmd_raid()` taps
    the first found target; **does not avoid smoke/cooldown buildings**
    (still no reference data on what a "smoky" target looks like -
    all three in the calibration screen were clean) — this remains the one
    real gap. If zero targets are found, falls back to tapping SWITCH
    OPPONENT for a fresh board rather than getting stuck. Confirmed live:
    correctly found and tapped a real target, triggering "You attacked Jin
    and won: 7,200".
  - **Popup-chaining fix (2026-09-06, confirmed live)**: reward popups can
    chain — the raid win's COLLECT was immediately followed by a *separate*
    "CONGRATULATIONS! 80,000" event-reward COLLECT (same button/coordinates,
    different trigger — this is also almost certainly the "section
    mini-game" COLLECT button the user described, now confirmed to share
    the exact same detector). A single fixed-delay tap-and-move-on wasn't
    enough for either the raid-tap-to-COLLECT transition or the
    COLLECT-to-next-popup transition: a screenshot taken too early lands on
    an in-between animation frame matching no known screen, which the loop
    then misread as "roll pill empty" and used to justify a 60s backoff -
    even once, this ate a full minute that could have been spent collecting
    a live 80,000 reward. Fixed via `_drain_collect_popups()`: taps the
    current COLLECT, then polls (short sleep + re-screenshot, up to 6
    extra rounds) for another one before giving up, used both by the main
    loop's top-level COLLECT check and by `cmd_raid()` after tapping a
    target. **Known remaining rough edge**: even after this fix, one live
    run still logged a spurious "roll pill fill ratio: 0.00 ... backing off
    60s" immediately after a popup chain resolved, even though the roll
    pill was actually fine (129/40) moments later — a transitional-frame
    misread can still occasionally slip through right at the moment
    control returns to the main board. Low-impact (costs at most one 60s
    wait) but not fully eliminated; a more general fix would be polling
    for a *stable* recognized screen state (not just "not a collect popup")
    for a beat before falling through to normal roll logic.
  - **Fixes applied 2026-09-06** (superseding the original OCR-based roll
    logic described in earlier notes): replaced roll-count OCR with the
    color fill-ratio heuristic; simplified `cmd_roll()` to single-tap-unless-
    empty (dropped the old <2/>10 threshold + long-press auto-roll logic —
    long-press is no longer used anywhere in automation, only documented
    above as a manually-confirmed mechanic); fixed the multiplier regex to
    tolerate tesseract dropping the "x"; wired the empty-backoff return code
    into `cmd_loop()`; removed a dead `get_roll_level()` helper that
    referenced constants (`ROLL_RATIO_LOW`/`ROLL_RATIO_HIGH`) which no
    longer exist (renamed to `ROLL_RATIO_EMPTY`) — it was unused by any
    command but would have raised `NameError` if ever called.
  - **User-reported mechanics, status as of end of session 2026-09-06**:
    (1) the same green COLLECT button also appears after the "section"
    mini-game — **confirmed**: it's the same button/detector as the
    match-3 and raid-reward COLLECT popups (see popup-chaining note above);
    (2) when auto-roll (long-press GO) is active and a COLLECT button
    appears, the game automatically times out/auto-advances on its own -
    noted but not directly exercised, since automation only ever
    single-taps and never uses long-press; (3) a green "GO!" button appears
    when a board is "complete" (fully built out) - **still not calibrated**,
    no live screenshot of this screen obtained this session. Next step:
    get a live screenshot when a board actually completes and calibrate
    the same way everything else in this file was done - by sampling real
    pixel coordinates, not by assuming it shares an existing detector.
  - **Known remaining limitations / good next steps for whoever picks this
    up:** the 60s empty-backoff is a fixed guess, not derived from the
    actual regen countdown (countdown-text OCR failed too) — accepted as
    "good enough" for now (see 2h-backoff design below). `build` always
    taps all 5 card slots regardless of affordability/cash — safe (no-op
    on unaffordable), but not optimal (wastes a bit of time tapping cards
    you can't buy). Confirmed live 2026-09-06 that `build` genuinely works
    well though: one manual cycle at real prices (18K-42K per card) bought
    6 buildings and advanced a city counter from 17/30 to 23/30 in a single
    pass. Raid target selection now taps *a* target but still has no
    smoke/cooldown avoidance strategy. Match-3 has no memory/strategy
    beyond "flip everything."
  - **"BOARD COMPLETE!" screen now handled (2026-09-07, confirmed live)**:
    shown when a city is fully built out, with its own green "GO!" button.
    Visually similar to the COLLECT popup but **not pixel-identical** -
    its button sits ~25-30px higher (y band 2095-2220 vs COLLECT's
    2120-2245), and the shorter "GO!" text lands differently than
    "COLLECT" does, so `COLLECT_BUTTON`'s point (540,2130) hit white text
    here instead of green, and `is_collect_screen()`'s cluster check also
    didn't fire. Needed its own dedicated detector/point:
    `is_board_complete_screen()` / `BOARD_COMPLETE_BUTTON = (540, 2100)`,
    a solid-green band clear of the text, calibrated the same way (map the
    green/text pattern row-by-row, pick a clean band) and confirmed with
    zero false positives across every other known screen type. Checked
    right after the card-popup check, before COLLECT, in both the main
    loop and `_settle_before_long_backoff()`. **General lesson**: two
    screens that look alike at a glance (same green pill button style)
    can still differ by enough pixels that a shared detector misses one of
    them - verify with an actual screenshot and pixel map rather than
    assuming visual similarity implies coordinate compatibility.
  - **"SWITCH OPPONENT" is a sub-menu, not an instant refresh (2026-09-07,
    confirmed live)**: `cmd_raid()`'s no-targets-found fallback taps
    `RAID_SWITCH_BUTTON` expecting an immediate new board, but it actually
    opens a full "SWITCH OPPONENT / Target a different player" menu -
    REVENGE/FRIENDS tabs, one row per player, each with its own "GO!"
    button (Random Player, plus named players who recently targeted you).
    Nothing recognized this screen, so the bot got stuck there (user
    report: "it looks like we accidentally tapped switch opponent").
    Fixed via `cmd_raid()`'s fallback polling for this menu right after
    tapping SWITCH OPPONENT (same poll-don't-guess-a-delay pattern as
    everything else in this file) and tapping "Random Player"'s own GO!
    button, `RANDOM_PLAYER_GO_BUTTON = (847, 1060)` - avoids any judgment
    about which real player to target, and a fresh random opponent is
    exactly what the original fallback wanted anyway.
  - **`is_switch_opponent_menu()` top-level safety net REMOVED
    (2026-09-07) - it caused a real stuck-loop incident.** This was
    originally also added as a top-level check (in the main loop and
    `_settle_before_long_backoff()`) gated on the gold/tan "REVENGE" tab
    background color at `(330, 880)`. That color check turned out
    fundamentally unreliable: confirmed live, an ordinary panned view of
    the main board put a yellow property tile at that exact coordinate,
    which matched the same loose color range - and its false-positive
    pixel count (366) was actually *higher* than the real menu's true
    positive count (321) in the same sampled region, meaning tightening
    the density threshold could not have fixed it. This locked the bot
    into an infinite loop, repeatedly "detecting" the menu and tapping
    Random Player on a completely normal board, going nowhere, until
    caught live by the user. **Fix**: removed the check from both
    top-level call sites entirely. The function and its use inside
    `cmd_raid()` (polling right after *deliberately* tapping
    RAID_SWITCH_BUTTON) are unaffected and remain safe, since in that
    narrow context there's no ambiguity about what screen to expect - the
    danger was specifically in treating a coordinate that overlaps the
    pannable board as if it were a fixed HUD element. **General lesson
    reinforced**: any check point that falls within the board's visible
    play area (not a fixed header/footer/badge position) is unsafe for a
    top-level "run every tick regardless of context" check, no matter how
    good its calibration screenshot looked - it must only be evaluated in
    a narrow context where the caller already knows what transition is
    expected.
  - **`is_build_menu_open()` false-positived on a jail "ROLL DOUBLES"
    event, second incident of this exact bug class (2026-09-07)**: a
    jail-themed "roll doubles to get out" bonus event (visually similar to
    the regular Roll Doubles event, but with a police officer/prisoner
    scene) put a neutral dark grey (81,83,80 - no color tint) at
    `BUILD_MENU_CHECK_POINT`, which the original check (independently
    bounding r/g/b ranges, no tint requirement) matched anyway - identical
    root cause to the switch-opponent-menu incident above, just a
    different check point and different innocent screen content. Caused
    another real stuck loop: repeatedly "closing" a BUILD menu that was
    never open, tick after tick, while `is_bonus_roll_screen()` (which
    correctly recognized this exact screen as True the whole time) never
    got a chance to run because the false match short-circuited every
    tick first. **Fix**: tightened the check to also require a genuine
    olive/warm tint - `(r-b) > 15 and (g-b) > 10` - rather than just
    bounding each channel independently. The real badge (93,87,63) has
    r-b=30, g-b=24; the false positive (81,83,80) has r-b=1, g-b=3, a
    clean, reliable gap. **Lesson**: "independently bound each of r, g, b"
    is a weaker check than it looks - it accepts a wide swath of neutral
    greys that happen to fall in range on every channel. Any dark/muted
    color signature in this file should also assert a specific *hue*
    (a channel meaningfully above or below the others), not just an
    intensity range, or it will eventually match some unrelated dark UI
    element. This is the same lesson as the bonus-roll-purple fix earlier
    in this file, now confirmed to generalize.
  - **`is_switch_opponent_menu()` re-added as a safe top-level check, and
    a real "stuck for up to 2h" gap fixed (2026-09-07)**. The menu kept
    recurring live (confirmed stuck on it twice more after the earlier
    removal), since its only remaining path to resolution -
    `cmd_raid()`'s narrow post-tap poll - doesn't fire if the menu is
    reached some other way, or if the poll's short window (5 attempts,
    1s apart) elapses before the menu finishes rendering. Rather than
    leave it unhandled, fixed the ROOT problem instead: the color check
    now requires OCR confirmation of the literal "SWITCH"/"OPPONENT"
    title text (`SWITCH_OPPONENT_TITLE_OCR_REGION`) before returning True,
    using the color match purely as a cheap pre-filter (OCR only runs on
    the rare ticks where color already matched, so this isn't a per-tick
    performance hit). Confirmed live this correctly returns True on a real
    menu and False on every known false-positive case (the original
    yellow-board-tile incident, a raid screen, a jail roll screen) - it's
    now safe to run unconditionally every tick again, and has been
    re-added to both the main loop and `_settle_before_long_backoff()`.
    **Separately, and more importantly**: found and fixed the real cause
    of a raid sitting stuck for the better part of 2 hours live - a raid
    screen occluding the roll pill caused a false "empty" reading right as
    the loop entered its long backoff, and `sleep_keeping_awake()`'s
    periodic wake-ups only ever checked for card popups/BUILD/COLLECT, not
    raid/match-3/bonus-roll/switch-opponent at all. Added full handling
    for all four to the backoff-wait's periodic checks, matching what the
    main loop already does - this was arguably a bigger gap than the
    switch-opponent color bug itself, since it could silently strand any
    of these four screens for up to the entire 2h wait, not just this one.
  - **SAFETY-CRITICAL: real-money purchase upsells now handled
    (2026-09-07, confirmed live)**. When rolls hit 0, a "KEEP ROLLING! /
    420 dice $1.99, 675 dice $2.99, 1000 dice $3.99" popup can appear
    (and these can chain - a second, differently-designed "Racing
    Champion Starter Pack $2.99" popup appeared immediately after). This
    is a dimmed-board popup like Chance/Community Chest cards, so the
    generic card-popup handler's action (tap the card's *center*) would
    have been used on it by default - **which sits directly among the
    green $-price buy buttons on this specific layout**. No purchase was
    ever actually made (confirmed live - cash unaffected across both
    upserts), but this was pure luck of the center point's exact position,
    not a designed safety margin. Fixed with `find_orange_x_button()`: a
    dynamic search (NOT a fixed coordinate - two upsell designs seen back
    to back had their X buttons ~30-70px apart) for the small orange
    circular X close button, restricted to the top-right region with a
    minimum-cluster-size requirement (>=8 matching points) to reject stray
    single-pixel color coincidences (confirmed necessary: filtered out a
    real false-positive hit on the unrelated Invite Friends popup).
    Checked and handled *before* the generic card-popup branch everywhere
    (main loop, the backoff-wait's periodic checks, and
    `is_purchase_upsell_screen()` as a standalone predicate) - if this
    button is found, ONLY it is ever tapped, never the card body.
    **Critical implementation detail**: `find_orange_x_button()` must only
    ever be called after `is_card_popup_screen()` has already confirmed
    the board is dimmed - calling it unconditionally every tick
    false-positived against the (undimmed) main board's bright orange
    Farm Express event icon. All three call sites are structured as
    `if is_card_popup_screen(): x_btn = find_orange_x_button(); ...`
    nested, never a bare top-level call.
  - **Green "dismiss" buttons unified into one dynamic finder
    (2026-09-07)**: COLLECT (match-3/raid rewards) and BOARD COMPLETE's
    GO! were originally two separate fixed-point detectors, calibrated
    ~30px apart. A third variant - a "Net Worth Gallery" reward-reveal
    popup - placed its own green button at yet another slightly different
    Y coordinate, proving fixed points don't scale to however many popup
    designs this game has. Replaced both with `find_green_button()`:
    proper connected-components clustering (like the raid-target finder)
    over the bottom third of the screen, filtered to button-shaped blobs
    (wide, moderate height, size-thresholded) and picking the largest -
    NOT a naive "topmost matching pixel in the region" scan, which was
    tried first and incorrectly picked up an unrelated green element on
    one screen instead of the actual button. `is_collect_screen()` and
    `is_board_complete_screen()` are now both thin wrappers around this
    same finder (kept as separate names since the rest of the codebase and
    RULES.md refer to both), and the main loop's separate BOARD COMPLETE
    branch was removed as redundant. `_drain_collect_popups()` re-finds
    the button's position on every chained popup rather than reusing the
    first one's coordinates, since chained popups aren't guaranteed to
    share a position either.
  - **General lesson from this whole session's popup-handling work**: this
    game has many visually-similar-but-not-identical popup/card/button
    designs, and assuming any two "look the same" share exact pixel
    coordinates has been wrong repeatedly. Prefer dynamic
    search/clustering (with a minimum-size/shape filter to reject noise)
    over fixed coordinates for any UI element observed in more than one
    distinct context, and when a fixed point is still used, get it from a
    real screenshot of *that specific* screen, not by assuming it matches
    a previously-calibrated similar-looking element.
  - **BUILD menu could get permanently stuck open (2026-09-07, confirmed
    live, now fixed)**: `cmd_build()` tapped `BUILD_CLOSE_X` exactly once
    with no verification. Live overnight, that single tap failed to
    register, and since nothing else in the detection chain recognized
    "we are currently inside the BUILD menu" as a distinct state, the bot
    sat stuck there for the remainder of a 2h backoff wait - the periodic
    keepalive checks during that wait only look for a few specific known
    problem-screens, and the BUILD menu wasn't one of them (its red badge
    check is keyed to the *main board's* badge position, which doesn't
    apply once you're already inside the menu). Fixed two ways: (1)
    `cmd_build()` now verifies the close actually worked and retries up
    to 4 times before giving up for that tick; (2) added
    `is_build_menu_open()` as a top-level safety net (checked in the main
    loop, `_settle_before_long_backoff()`, and the backoff-wait's periodic
    checks) - detects the dark charcoal star-count badge that replaces the
    profile picture in the BUILD menu's top bar, calibrated point
    `(140, 180)`, color `(93,87,63)`, confirmed no false positives against
    every other known screen type. If ever found open unexpectedly, taps
    `BUILD_CLOSE_X` and re-checks next tick.

## Overnight/unattended-run hardening (2026-09-06)

The user wants to leave this running unattended overnight, which surfaced
several issues a short interactive test never would. In rough chronological
order of discovery:

- **`monopoly-go-supervisor`** (`~/bin/monopoly-go-supervisor` on localnet,
  mirrored on Windows) — a bash wrapper that runs `monopoly-go-assist loop`
  in a restart-on-crash while-loop with unbuffered, timestamped logging to
  `~/ai-logs/monopoly-go-assist-YYYYMMDD.log`. Commands: `start|stop|status`.
  **Always invoke via full path** (`~/bin/monopoly-go-supervisor`, not bare
  `monopoly-go-supervisor`) when running non-interactively over `ssh host
  "command"` — `~/bin` is not on `PATH` for non-interactive shells (most
  `.bashrc`s skip PATH setup outside interactive sessions), so the bare
  command name fails with "command not found" in that context even though
  it works fine from an interactive login shell.
- **2-hour empty-roll backoff (supersedes the earlier 60s design)**: per
  explicit user direction ("we want it to be able to have 10 rolls, so we
  wait 2 hours"), `ROLL_EMPTY_BACKOFF_S` is now `7200`, not `60` - let
  rolls bank up rather than waking for every single one. Because a false
  "empty" reading is now much more expensive to act on than it was at 60s,
  this required two new safety mechanisms (below).
- **`_settle_before_long_backoff()`**: before committing to the 2h sleep,
  polls for up to 25s (not just a quick 2-3s double-check) across *every*
  known screen type (card popup, collect, match-3, bonus-roll, raid) and
  the roll pill itself. Confirmed live this was necessary: a raid's intro
  crane/transition animation outlasted a short double-check gap, so both
  quick checks landed mid-animation and nearly triggered a wasted 2h sleep
  instead of handling a real raid with 3 targets. If anything recognized
  turns up during the settle window, the loop re-enters its normal
  per-tick handling immediately instead of sleeping.
- **`sleep_keeping_awake()` / `_keep_screen_awake()`**: the 2h backoff is
  not a blind `time.sleep()`. Every 5 minutes it (a) sends a WAKEUP
  keyevent + a short swipe to prevent/reverse the phone's screen timing out
  and locking (confirmed live: this phone has a real swipe-to-dismiss lock
  screen, no PIN, but plain wake-up alone isn't enough - an actual swipe is
  needed; a *short*, not edge-to-edge, swipe is used so an accidental camera
  pan is minor if the screen turns out to already be unlocked), and (b)
  checks for and handles the BUILD badge and card popups. This second part
  fixed a real gap reported live by the user ("we are missing the build
  part") - the original version blindly slept for the full 2h with no
  BUILD checks at all, even though building only needs banked cash, not
  rolls, so a badge appearing during the wait would just sit ignored for
  up to 2 hours. (Raid/match-3/bonus-roll are deliberately NOT re-checked
  during this wait - they need the main loop's fuller handling, and will
  be caught once the wait ends and normal per-tick checks resume.)
- **Phone screen timeout extended remotely**: `adb shell settings put
  system screen_off_timeout 1800000` (30 min) - no physical "Stay awake"
  toggle needed, this works over adb alone. Combined with the keepalive
  above, this should keep the phone from ever actually locking during
  normal operation.
- **Card popup detection (Chance/Community Chest/"any number of card
  types" per the user)**: `is_card_popup_screen()` does NOT match on a
  specific card's interior color (colors vary by card - a blue "CHANCE -
  Advance to nearest railroad!" card was the one seen live), but on the
  dimmed-board overlay ALL these cards apply: a point in the cash bar that
  reads bright cream (~241,235,220) normally reads very dark (~36,35,32)
  whenever a card popup is up. Calibrated and confirmed with zero false
  positives across every other known screen type. `CARD_TAP_POINT =
  (540, 1232)` (the card's center) dismisses it - checked with the
  *highest* priority in the main loop, since a card popup blocks
  everything else. Live logs show it correctly handling chains of several
  cards in a row plus an interleaved bonus-roll event, fully unattended.
- **ApplyPilot LLM client retry gap (found while running scoring alongside
  this work)**: `llm.py`'s retry logic only covered HTTP 429/503 and
  timeouts, not 500/502 or raw connection resets - both of which the local
  OpenVINO server threw intermittently under sustained sequential load
  (memory grew to an 11GB peak during one run). Fixed by adding 500/502 to
  the retryable status codes and a new `except httpx.TransportError`
  branch with the same backoff. The underlying OpenVINO server instability
  itself was NOT root-caused or fixed (just worked around via retries +
  restarting the systemd service) - worth investigating
  `openvino_openai_server.py` directly if this recurs.
- **AI stack services converted to systemd (openvino-api, local-bin-mcp,
  open-webui)**: these were previously plain `nohup`'d background
  processes started by `~/startAI.sh`, which do NOT survive a reboot - and
  this box rebooted multiple times during this session (network/power
  issues - "storm" per much earlier context). Ollama already survived
  reboots because it's a systemd service; the other three did not, which
  caused real, repeated interruptions (ApplyPilot scoring runs dying
  mid-way with "Connection refused" until manually restarted). Fixed by
  writing unit files to `/etc/systemd/system/{openvino-api,local-bin-mcp,
  open-webui}.service` (`ExecStart` pointing directly at each venv's
  binary, not relying on `source activate`) and `sudo systemctl enable
  --now` all three. **Confirmed live**: a subsequent real reboot brought
  all three back up automatically with zero manual intervention, verified
  via HTTP checks immediately after boot.
- **Background `ssh host "command &"` invocations can hang**: even with
  `disown`, a backgrounded process can keep an SSH session open
  indefinitely if it inherits the session's stdin/stdout/stderr file
  descriptors - redirecting each command's own output isn't enough if the
  *shell/subshell itself* wasn't also redirected. Symptom: the `ssh`
  command never returns even though the intended background work (e.g.
  `monopoly-go-supervisor start`) actually succeeded. Not yet fixed in
  `monopoly-go-supervisor` itself (workaround used this session: just let
  the command time out/background from the caller's side, then verify
  separately via `pgrep`) - a proper fix would redirect the whole
  background subshell's stdin from `/dev/null`, e.g.
  `( ... ) < /dev/null >> "$LOG" 2>&1 &`.
- **`pkill -f` / `pgrep -f` self-matching bug (recurring)**: seen multiple
  times again this session. Any pattern that appears in the *literal
  command line being run* (including the `ssh host "..."` wrapper text
  itself, or the pgrep/pkill invocation's own arguments) can match that
  same process, not just the intended target. Always prefer killing by a
  literal PID captured earlier over `pkill -f`/`pgrep -f` with a pattern
  when invoking remotely via `ssh host "command"`.

Reference copies of all of these live in
`C:\projects\tools\python\localnet-bin\` on the Windows side.

## 2026-09-07 fixes, part 2 (idle-poll speed, overnight reboot survival)
- **Main loop idle-poll interval dropped from 4s to 1.3s** (~3x, per
  explicit user request) - this is how often the loop re-checks screen
  state when nothing needs handling, so it now notices a newly-available
  roll, BUILD badge, or popup up to 3x sooner. The two tick-count-based
  fixed-interval fallbacks (`cmd_build()`'s ~6min safety net,
  `cmd_check_wins()`'s ~30min schedule) were rescaled (90->277, 450->1385)
  to preserve their original real-world cadence rather than silently
  firing 3x more often - not a correctness issue either way (extra
  redundant checks are harmless), just kept for clarity against the
  comments describing them.
- **`monopoly-go-supervisor` now also auto-starts at boot via systemd**
  (`/etc/systemd/system/monopoly-go-supervisor.service`, oneshot,
  `ExecStart=${SERVICE_USER_HOME}/bin/monopoly-go-supervisor start`, enabled via
  `systemctl enable`). This does NOT replace the existing bash supervisor
  or change how the user starts/stops/checks it day-to-day - the bash
  script's own PID-file guard means running `start` again (whether by the
  user or by this systemd unit after a reboot) is always a harmless no-op
  if it's already running. Added specifically because this box has a
  history of unexplained reboots (see openvino-api/local-bin-mcp/
  open-webui hardening above) and the bash supervisor alone has no way to
  come back after the box itself restarts, unlike an actual systemd
  service.
- **Diagnosed "it keeps stopping" (2026-09-07 evening)**: turned out to be
  three distinct, already-understood things layered together, not a new
  bug: (1) my own manual `stop`/`start` cycles while deploying fixes that
  day, (2) two genuine physical USB disconnects (confirmed via `lsusb`
  showing the Pixel device vanish entirely, not just an adb daemon wedge -
  see "Known device/session facts" below), which crash-loops the process
  every ~10s via `OSError: image file is truncated` until the cable is
  physically reseated, and (3) the `Backing off 7200s (rolls empty)`
  message being mistaken for the automation having stopped, when it's
  actually a normal, correct 2h wait for rolls to regenerate in real time
  - restarting the loop during this wait doesn't get rolls back any
  sooner, since regeneration is on the game's own real-world timer, not
  something polling frequency affects.

## 2026-09-08: is_quit_dialog_present() false-positived, gated behind
   is_card_popup_screen()
- User report: "it does not want to start now" - turned out to be
  running fine, but stuck repeatedly logging "Quit-game dialog detected
  (unexpected) - tapping CANCEL" on a completely ordinary, undimmed main
  board. Root cause: `QUIT_DIALOG_CHECK_POINT`'s bare color range
  (200<r<255, 150<g<210, b<110) matched a yellow-roofed building visible
  on that particular opponent's board at that exact screen point
  ((224,190,96), close enough to the real CANCEL button's (242,184,83)).
  Deliberately triggered a real dialog via `adb shell input keyevent 4`
  (BACK) to get a ground-truth reference rather than guessing - confirmed
  the real dialog always dims the board first (`CARD_DIM_CHECK_POINT`
  read (36,34,29) on the real dialog vs (241,235,220) on the false-
  positive board). **Fix: gated the color check behind
  is_card_popup_screen() first**, same pattern as find_orange_x_button()
  and is_pick_a_box_screen() above. Also checked whether the real
  dialog's green "QUIT" button could be mistaken for a COLLECT button by
  `find_green_button()` (checked FIRST in the main loop) - confirmed not
  a risk, since QUIT sits at native y~1590-1690, above
  find_green_button()'s default search band (y_start=1900).

## 2026-09-08: find_green_button() false-positived again, on a big flat
   lawn patch - default y_start raised 1900 -> 2100
- User report ("it feels like we have waited longer than 2 hours") led to
  discovering the supervisor was fully dead (not just sleeping) after an
  extended stuck-tap-loop episode: "Another chained popup detected -
  tapping green button at (152, 1908)" repeating on a completely plain,
  undimmed main board with no popup at all. The color+flatness fix from
  earlier the same week didn't cover this case: a big, PERFECTLY flat
  solid-color lawn patch measured stdev ~(2,3,2) per channel (flatter
  than a real button's ~11,8,13), so it passed the uniformity check too.
  Confirmed the same failure mode independently on a raid screenshot's
  lawn as well. **Fix: raised find_green_button()'s default y_start from
  1900 to 2100**, matching the documented real-button range (2100-2130)
  exactly - the original 1900 gave 200px of pure false-positive surface
  below the lowest real button ever observed, for no benefit. Verified
  against both flat-lawn false positives (rejected) and swept 2050/2080
  first (still let the raid one through) before landing on 2100 as the
  tightest safe boundary.
- Separately, also investigated why the supervisor had gone fully
  inactive (not just backing off) - found one confirmed, already-
  self-healing cause (a transient real USB reset/reconnect at
  11:25:10-11:25:11 per kernel log, causing a ~90s burst of crash-
  restarts that resolved on its own once the device re-enumerated) but
  could NOT find a definitive cause (no OOM-kill, no crash signal in
  dmesg/journalctl) for the supervisor process being completely gone by
  the time it was checked later that afternoon. Left as an open question
  - if it recurs, check `journalctl --since/--until` around the exact gap
  for anything unusual, and consider whether the terminal/SSH session
  that originally ran `monopoly-go-supervisor start` was itself closed in
  a way that got past `disown` (not confirmed, just not yet ruled out).

## 2026-09-08, same investigation: is_build_menu_open()'s OCR fallback
   also false-positived - made case-sensitive
- Immediately after the find_green_button() fix above, a new symptom
  appeared on a completely plain main board: "BUILD menu found open
  (unexpectedly) - closing it" cycling repeatedly. Cause: this game's
  tile price labels use an "M" currency prefix (e.g. "M1,000" visible
  on-screen), and tesseract garbled some board text into a stray "720m" -
  the OCR price-match regex was case-INsensitive, so that single
  lowercase 'm' fragment was enough to pass the (already-lowered-to-1)
  threshold from the fix earlier this week. Every genuine price observed
  so far ("446K", "112K", "76.6K", ...) renders uppercase - **fix: made
  the regex case-sensitive** (dropped `re.IGNORECASE`), which rejects
  this class of garbage match without needing to raise the match-count
  threshold back up (raising it would break the mostly-maxed-slots case
  that fallback exists for). Verified against all 6 known reference
  screenshots (this new false positive, the mostly-maxed and all-prices
  real cases, main board, raid, switch-opponent) before deploying.

## 2026-09-11: faster decision-making (raw screencap, check-ordering bug)
- User asked how to make decision-making faster. Measured actual per-tick
  costs rather than guessing (methodology matters here - the earlier
  interval_s speedup mattered far less than assumed): `screenshot()`
  (`adb exec-out screencap -p`) averaged ~1190ms, a single OCR call
  ~450ms, each redundant `Image.open()` ~46ms (and an ordinary tick was
  reopening the screenshot from disk ~8-10 separate times across the
  various `is_*()` checks). screenshot() alone dwarfed the 1.3s
  `interval_s` sleep - the idle-poll speedup from a few days earlier was
  a much smaller win than it seemed at the time.
- **Fix: `screenshot()` now captures raw (uncompressed) instead of `-p`
  (PNG).** Measured ~2.2x faster overall (~540ms vs ~1190ms average)
  even after re-encoding to PNG locally afterward to keep every existing
  `Image.open(SCREENSHOT)` call site unchanged - zero risk to any
  detection function, since they still just read a PNG from the same
  path. Counterintuitive but confirmed: raw transfers ~6x more bytes
  (10.1MB vs 1.58MB for a 1080x2340 capture) yet is still much faster,
  because the phone's own on-device PNG-encoding CPU cost dominates the
  `-p` approach's total time - USB bandwidth was never the bottleneck.
  Raw format: 16-byte header (width, height, format, extra - all uint32
  LE) then raw RGBA8888 pixel data, parsed via `struct` +
  `Image.frombuffer`. Verified against a real screenshot (colors and
  content both correct) before deploying. NOTE while testing this: don't
  point test scripts at the live shared `SCREENSHOT` path
  (`/tmp/mg_screen.png`) while the production supervisor is running -
  it's being overwritten every ~1.3s by the live loop, and a test read
  can catch a torn/mid-write file. Use an isolated path for any manual
  testing instead.
- **Separately found (not caused by the above, just surfaced by testing
  it) a real, pre-existing check-ordering bug in `cmd_loop()`**: the
  generic `is_card_popup_screen()` handler (center-tap + close-X
  fallback) was checked BEFORE `is_switch_opponent_menu()`,
  `is_match3_screen()`, `is_bonus_roll_screen()`, and `is_raid_screen()`.
  Confirmed live: the "ROLL DOUBLES" bonus event dims the board (so it
  also matches `is_card_popup_screen()`), and since the generic handler
  ran first, it swallowed the event every tick with an ineffective
  center-tap - stuck-cycling "Card popup detected... Still showing..."
  forever, never once reaching the dedicated bonus-roll branch below it.
  `is_color_wheel_screen()` and `is_pick_a_box_screen()` had already been
  correctly special-cased ahead of the generic handler for this exact
  reason; `sleep_keeping_awake()`'s parallel copy of this logic already
  had the correct order too - only `cmd_loop()`'s main-loop copy had
  drifted. **Fix: moved switch-opponent/match3/bonus-roll/raid checks
  above the generic card-popup branch**, matching color-wheel/pick-a-box
  and the already-correct order in `sleep_keeping_awake()`. General
  lesson: any screen with its own dedicated tap target needs to be
  checked before the generic dimmed-popup fallback, in EVERY place that
  fallback exists - it's easy for one copy of this ordering to drift out
  of sync with another when they're maintained separately.

## 2026-09-11: /tmp cleanup - cleanup_temp_images(), run at the rolls-
   empty checkpoint
- User asked to keep image space clean, tied to "when the roll count
  gets to zero." Investigated first rather than assuming the production
  script was the culprit: found 213MB / 169 files in /tmp, but confirmed
  the script itself only ever writes to 3 fixed, reused paths
  (`SCREENSHOT`, `_RAW_SCREENSHOT`, the OCR crop path at
  `/tmp/mg_crop.png`), all overwritten in place every call - it was never
  actually the source of any buildup. The pile was entirely leftover
  manual diagnostic screenshots and copies of this script made during
  debugging sessions this week. Did a one-time cleanup of that (deleted
  everything under `/tmp/mg_*`/`/tmp/mga_*` except the 3 production
  paths).
- Added `cleanup_temp_images()` as an ongoing defensive safety net
  anyway (matches what the user asked for, even though the script wasn't
  the actual cause): removes any `/tmp/mg_*`/`/tmp/mga_*` file that isn't
  one of the 3 known production paths, run once at the exact checkpoint
  the user named - when rolls hit empty and the loop is about to enter
  its 2h backoff (`cmd_loop()`, right where "Backing off ...s (rolls
  empty)" prints). Skips anything modified in the last 5 minutes, so it
  can never race a concurrent live debugging session's own diagnostic
  files. Verified against fake old/new files and the 3 real production
  paths before deploying.

## Known limitations - manual only, do not re-attempt automation
- **"Infinite Harvest" / "PICK A BOX" mini-event cannot be automated via
  ADB touch injection.** Five distinct techniques were tried against the
  three wooden crates and all failed to register, while the user's own
  physical touches worked every time: plain `input tap`, an instant
  `motionevent DOWN`/`UP` pair, `long_press()` (DOWN + periodic MOVE
  keepalive + UP) at 1.5s, `motionevent DOWN` + 1s wait + `UP`, and
  `long_press()` at 5.0s. Re-confirmed live 2026-09-07 with a plain tap
  immediately after a fresh `adb kill-server`/`start-server` cycle (to
  rule out the tap having silently failed due to adb-connection flakiness
  rather than a genuine UI issue) - screenshot before and after the tap
  were pixel-identical (aside from unrelated background character
  animation), confirming this is a real, repeatable limitation of this
  specific Unity UI element, not a fluke. The `show_touches` system
  setting was also tried as a diagnostic (`adb shell settings put system
  show_touches 1`) - confirmed enabled via `get`, but the touch indicator
  circle never appeared in any screenshot even with a 1s held DOWN event;
  inconclusive (likely just not captured by `screencap`'s timing, not
  proof the touch itself failed). **Conclusion: treat this event as
  manual-only.** When it appears, tell the user to tap it themselves
  rather than re-attempting any touch-injection variant - this has now
  been tried exhaustively enough that further attempts are not a good use
  of time without a fundamentally different approach (e.g. investigating
  whether the game requires a real multi-touch/pressure profile ADB can't
  synthesize).
- **Follow-up investigation (2026-09-07, same day): raw `sendevent` replay
  is also a dead end, definitively.** Captured a real touch via
  `adb shell getevent -lt /dev/input/event2` while the user tapped a box
  (device: `sec_touchscreen`, confirmed via `getevent -i`) - got a full,
  legitimate multi-touch sequence (`ABS_MT_TRACKING_ID`, `POSITION_X/Y`,
  `TOUCH_MAJOR/MINOR`, `PRESSURE`, ~220 events with natural jitter over
  ~300ms). Parsed it into a `sendevent`+`usleep` replay script preserving
  original relative timing, pushed it to `/data/local/tmp/`, and ran it
  against a live, freshly-reset box screen. Result: `sendevent:
  /dev/input/event2: Permission denied` on every single write. The device
  node is `crw-rw---- root input` and `adb shell id` confirms `shell` is
  in group `input` (gid 1004) - so the DAC bits alone should allow this -
  but SELinux denies the write anyway (this is a deliberate Android
  security boundary against exactly this kind of raw touch injection).
  `adb root` was also tried and refused outright: "adbd cannot run as
  root in production builds". **Conclusion: this is not a timing or
  technique problem like the higher-level `input`/`motionevent` attempts
  - it's a hard OS permission wall.** The only way past it would be
  rooting the phone, which is a materially bigger, riskier step (voids
  warranty, may wipe the device) that should never be attempted without
  the user explicitly asking for it first. Do not re-attempt sendevent-
  based replay against this or any other device without root.
- **Follow-up fix (2026-09-07, same day):** added `is_pick_a_box_screen()`
  (cheap `is_card_popup_screen()` gate + OCR-confirms "PICK" and "BOX" in
  the banner text at `PICK_A_BOX_OCR_REGION = (270, 1580, 700, 1660)`) so
  the loop recognizes this screen by name instead of falling through to
  the generic card-popup handler. Before this, the main loop and
  `sleep_keeping_awake()` both repeatedly center-tapped and X-fallback-
  tapped this screen every single tick forever (harmless - no purchase
  buttons here - but wasted cycles and log spam). Now it just prints once
  and waits 5s between checks until the user taps a box themselves and
  the screen naturally changes underneath it.
- **SUPERSEDED 2026-09-15 - both the "manual-only" conclusion above and
  the `is_card_popup_screen()` gate on `is_pick_a_box_screen()` turned out
  to be wrong.** New live evidence: a plain `input tap` at the calibrated
  `GO_BUTTON` point (539,1901) reliably completes the box-pick, and this
  screen never actually dims the board in the first place (so the gate
  silently suppressed detection through the normal loop this whole time -
  every prior "5 techniques failed" test was necessarily an ad-hoc tap
  issued outside this script, since the automation itself could never
  recognize the screen to attempt one). See the dated section near the
  end of this file ("2026-09-15: Pick a Box mini-event - manual-only
  conclusion overturned") for the full root-cause writeup and the current
  automated handling (`cmd_pick_a_box()`). **Do not reintroduce a
  dimmed-board gate on this detector, and do not re-mark this
  manual-only, without fresh live evidence.**

## 2026-09-07 fixes (build depth, build-menu reskin detection, stuck-loop
   false positive, tap speed)
- **`cmd_build()` now verifies the menu actually opened before tapping any
  card slots**, retrying the open tap up to 4 times and skipping the
  visit entirely (rather than tapping blind) if it never confirms open.
  Root cause: a single unverified open tap could silently miss (e.g. it
  landed at the same instant as an unrelated animation - caught live: a
  dice-roll "DOUBLES" overlay was covering the main board at the exact
  moment the BUILD tap fired), after which cmd_build tapped the 5 card-
  slot coordinates against whatever WAS on screen, then found the menu
  already "closed" (never having been open) and logged success having
  bought nothing - a silent no-op indistinguishable from a real visit in
  the logs. Confirmed live via user report: cash reached ~2 million with
  the BUILD badge still showing pending purchases ("I think it forgot to
  build").
- **`is_build_menu_open()` no longer relies solely on a fixed background
  pixel's color.** The game periodically runs fully themed event reskins
  (confirmed live: a "M. Industries" sci-fi factory skin) that recolor
  the menu's chrome - the calibrated olive-tint check point read a blue-
  teal (90,139,147) during this event, so the color check never matched
  even though the menu was genuinely open and sitting there ("so, the
  build menu is open. it is just hanging out."). Fixed with a skin-
  independent fallback: OCR the card-price row (`BUILD_PRICE_ROW_BOX =
  (0, 1950, 1080, 2110)`, full width, `--psm 6`) and require digit+K/M
  formatted price tokens - prices stay plain numeric text regardless of
  skin. Narrow per-slot OCR crops were tried first and produced garbage
  at this resolution; the full-width row crop works reliably. Also bumped
  the post-open-tap wait from 1.0s to 1.8s once it was clear the open
  animation consistently needs ~2s to fully render, which had been
  burning 2 guaranteed-fail retries (each with its own screenshot+OCR
  cost) on every single BUILD visit.
  - **Follow-up, same day, two more rounds:** the 3+ price-token
    threshold above was still not enough. Live incident: once 4 of 5
    slots were already maxed out (showing a green checkmark instead of a
    price), only 1 genuine price remained on screen - threshold lowered
    to 1+. That still wasn't enough: tesseract could not reliably read
    that one remaining price ("446K" repeatedly OCR'd as garbage like
    "AAKK"/"MKK" no matter how the crop was cropped/scaled/binarized/
    whitelisted - a genuine font-legibility limit for this game's bold
    rounded digits, not a crop-calibration problem). Real consequence
    both times: the menu sat open with a real, affordable item untouched
    while the loop concluded "never opened", skipped the visit, then
    misread the occluded roll pill as empty and entered a 2h backoff.
    **Final fix: detect the checkmark icons directly by color+density
    instead of reading text**, as a third fallback after color and OCR
    both fail. A maxed slot's checkmark and a purchasable slot's cash
    icon are both the same saturated green as a COLLECT button (see
    `_is_dismiss_green`) - but naively scanning for that hue re-triggers
    the exact grass/foliage false positive already fixed in
    `find_green_button()` below (confirmed live: a raid screen's grass
    sampled 1-6 stray matching pixels in this same row's y-band). The
    fix is density, not hue: a real checkmark/icon fills its slot
    solidly (measured live: 31-32 matching samples in a tight per-slot
    window), while stray grass only clips 0-6. Requiring 15+ matches
    within a narrow +/-20px column around each of the 5 known
    `BUILD_CARD_XS` positions cleanly separates the two. **General
    lesson: when OCR is the fallback for a UI element, don't assume it
    will always succeed just because the crop is correctly positioned -
    some fonts/sizes are genuinely unreliable for tesseract, and a
    color/density-based structural check can be more robust than text
    recognition for icons that always have SOME visual presence
    (checkmark vs price) even when their exact content varies.**
- **`find_green_button()` (used by `is_collect_screen()`, checked FIRST
  in the main loop, before every other screen type) false-positived on a
  raid board's background grass/foliage**, causing a genuine infinite
  stuck loop: repeatedly "tapping" a nonexistent COLLECT button on top of
  an active raid, forever (log showed hundreds of consecutive "Another
  chained popup detected - tapping green button at (896, 1908)" lines).
  Root cause: one sampled grass pixel, (131,180,105), independently
  passed `_is_dismiss_green()`'s hue check (g meaningfully above both r
  and b - the same signature a real button legitimately has) AND the
  grass patch was large/wide enough to pass the button-shape cluster
  filter. The existing hue-based fix pattern (used for badge/menu color
  checks earlier this session) doesn't generalize here because natural
  foliage genuinely shares the hue signature of a green UI button - shape
  and hue alone can't tell them apart. **Fix: reject the winning
  candidate blob if its matched pixels aren't color-uniform.** A real
  button's fill is a flat, near-solid color; grass/foliage is textured.
  Measured live: matched pixels within a genuine GO button had per-
  channel stdev ~(11, 8, 13), vs ~(28, 14, 21) for the false-positive
  grass patch - clear, reliable gap. Threshold used: reject if r_std > 20
  or g_std > 16 or b_std > 18. Rejection returns `None` outright (skip
  this tick) rather than falling back to a smaller candidate. **General
  lesson (new variant): when a false positive shares the same genuine hue
  signature as the real target, hue alone is insufficient - check color
  *uniformity/flatness* of the matched region instead, since real UI
  elements are flat-filled and natural textures (foliage, terrain, cloth)
  are not.**
- **Tap speed increased ~3x on the two purely-mechanical repeat-tap
  loops** (per explicit user request for overall speed): `cmd_build()`'s
  per-card-slot delay dropped from 0.5s to 0.15s, `cmd_match3()`'s per-
  tile delay dropped from 0.7s to 0.25s. Deliberately NOT applied to any
  delay that follows a tap which triggers a screen transition (popup
  dismissal, raid resolution, menu open/close, color wheel spin, etc.) -
  those were specifically tuned earlier this session to avoid misreading
  an in-between animation frame, and remain unchanged.
- **Operational note, not a code fix**: the adb daemon on localnet can
  wedge even while the phone stays physically connected and charging -
  symptom is `adb devices` returning an empty list while `lsusb` still
  shows the phone enumerated ("Google Inc. Nexus/Pixel Device (charging +
  debug)"). Fix is `adb kill-server && adb start-server`, which
  reconnected instantly. The supervisor's own crash-restart loop already
  handles the resulting `PIL.UnidentifiedImageError` (empty screenshot
  from a failed `adb exec-out screencap`) by restarting the inner loop
  automatically, but the daemon itself needed the manual kill/start cycle
  to actually recover connectivity.

## 2026-09-15: Pick a Box mini-event - manual-only conclusion overturned
- **User report**: 3-4 crates are shown at the bottom of the "Infinite
  Harvest / PICK A BOX" screen, and one of them is *always* positioned
  directly over the calibrated `GO_BUTTON` point (539,1901) regardless of
  how many crates are showing. Live screenshots captured for this fix:
  `mg_live_screen.png` (sealed crates, event just appeared),
  `mg_after_center_tap.png` (crates open/revealed - basket, empty,
  watering can - right after a tap at 539,1901), `mg_after_settle.png`
  (a few seconds later: the screen has auto-transitioned back to the
  normal main board, cash bar and GO button both visible again).
- **Root cause #1 - the loop never even recognized this screen.**
  `is_pick_a_box_screen()` was gated behind `is_card_popup_screen()` (the
  dimmed-cash-bar check used for Chance/Community Chest/purchase-upsell
  popups), copied by analogy from `find_orange_x_button()`'s gate when it
  was added on 2026-09-07 - but that gate was never actually confirmed
  live against a real Pick a Box screenshot, unlike every other gate in
  this file. Checked against `mg_live_screen.png`: this screen does not
  dim the existing UI at all - it fully replaces the top bar with
  different background scenery (no cash figure, no profile picture), so
  `CARD_DIM_CHECK_POINT` never reads dark here and the gate returned
  `False` on every real occurrence. Practical consequence, confirmed live:
  this screen also occludes the roll pill, so with the detector silently
  disabled, the loop fell through to `cmd_roll()`'s empty-pill check,
  read it as genuinely 0 rolls, and committed to the full
  `ROLL_EMPTY_BACKOFF_S` (7200s / 2h) backoff - the user found the loop
  sitting stuck on this exact screen for the entire window. This also
  means the 2026-09-07 "5 touch-injection techniques all failed"
  conclusion was drawn from taps issued directly at the crates from
  *outside* this script (ad-hoc diagnostic testing) - the automation's own
  detector had never once fired to attempt a real tap through the normal
  code path.
- **Root cause #2 (the actual overturned conclusion) - touch injection
  does work here; targeting was the problem.** While the loop was
  confirmed stuck in the 7200s backoff on this screen, a plain
  `adb shell input tap 539 1901` was issued manually - the exact same
  `input tap` primitive already tried and dismissed as non-working back on
  2026-09-07. Before/after screenshots confirm the tap registered and
  completed a box pick (`mg_after_center_tap.png` → `mg_after_settle.png`
  above). The most likely explanation: the 2026-09-07 attempts tapped
  coordinates read/guessed directly off the crates' own on-screen
  position, and those were apparently not precise enough to land inside
  this Unity element's real hit target (which may be smaller/more exact
  than the visible crate art suggests) - a targeting problem, not the
  "hard OS permission wall" the `sendevent`/SELinux investigation
  separately and correctly confirmed for *raw* touch replay. The
  high-level `input tap` primitive itself was never actually the blocked
  layer.
- **Fix applied**: `is_pick_a_box_screen()` no longer depends on
  `is_card_popup_screen()` - it now OCRs `PICK_A_BOX_OCR_REGION` directly
  and unconditionally every check (same cost profile as the
  already-unconditional multiplier-badge OCR in `_multiplier_action()`).
  This deliberately trades a small, bounded per-tick OCR cost for
  correctness, since an unverified color gate is exactly what caused this
  bug - a cheap pre-filter can be added later, but only if calibrated
  against a real live screenshot on the deployment host, never guessed.
  A new `cmd_pick_a_box()` taps `GO_BUTTON`, then polls (up to
  `PICK_A_BOX_POLL_ROUNDS` x `PICK_A_BOX_POLL_S` ≈ 10.5s) for either the
  screen to actually leave the Pick a Box event or a reward `COLLECT`
  popup to appear - a single immediate re-check can't tell "tap missed"
  apart from "tap landed, box-reveal animation still playing" (confirmed
  live: the OCR text still reads "PICK A BOX" while the crates are shown
  open with revealed contents, before the auto-transition back to the
  main board). Bounded to `PICK_A_BOX_TAP_RETRIES` (3) total tap attempts
  before giving up and waiting 60s between later attempts, in case the
  `GO_BUTTON`/crate overlap ever stops holding (reskin, layout shift, or a
  genuine future touch-injection regression). Wired into both `cmd_loop()`
  and `sleep_keeping_awake()` in place of the old print-and-wait branch,
  and added to `_settle_before_long_backoff()`'s recognized-screen list
  (it wasn't covered by `is_card_popup_screen()` there either, for the
  same reason). If a box clears during the long roll backoff and rolls are
  visible again, the wait ends immediately so the loop resumes rolling.
- **Safety**: `cmd_pick_a_box()` is only ever invoked after
  `is_pick_a_box_screen()`'s OCR match on "PICK" + "BOX" in the narrow
  banner region - it is never reachable from the generic card-popup or
  purchase-upsell branches, and taps only the single fixed `GO_BUTTON`
  point (never a dynamically-found button near price/buy text), so this
  carries none of the real-money risk the purchase-upsell handling guards
  against.
- **Offline tests**: `test_monopoly_go_assist.py` (new file, same
  directory) covers `_pick_a_box_ocr_matches()`'s text matching, the
  `is_card_popup_screen()`-independence regression, and
  `cmd_pick_a_box()`'s tap/poll/retry control flow (success, chained
  reward popup, mid-animation false-failure avoidance, bounded give-up) -
  all via monkeypatched module functions, no real device/Pillow/tesseract
  required. Run with `python test_monopoly_go_assist.py`. **Not yet run
  against the real device** - the next live session should confirm
  `cmd_pick_a_box()` end-to-end against a real, freshly-appeared Pick a
  Box screen (not just the retroactive before/after screenshots this fix
  was based on) and update this entry with the result.

## 2026-09-16: COLLECT exact-text fallback and direct command
- The existing reward handler only found wide green buttons in the narrow
  bottom band `y=2100..2340`. A user-reported current reward screen needed
  COLLECT tapping but did not match that established color/layout rule.
- Added `find_collect_button()`: it preserves `find_green_button()` as the
  fast first choice, then uses Tesseract TSV to locate only the literal
  word `COLLECT` below the fixed top HUD. In the continuous loop, the OCR
  fallback is allowed only when the roll pill is hidden, which is the same
  symptom reward overlays produce and prevents full-screen OCR/tapping
  during ordinary rolling.
- Added `monopoly-go-assist collect` for an explicit one-off action on the
  current screen. It screenshots, finds either the established green
  reward button or exact COLLECT text, and refuses to tap if neither is
  present. `_drain_collect_popups()` uses the same finder so chained
  differently-colored or vertically-shifted COLLECT screens are handled.
- The exact-text parser is covered by offline tests for coordinates,
  punctuation/case, partial-word rejection, low confidence, and top-HUD
  rejection.
- Live calibration found expired-event leaderboards with their green
  `COLLECT` button at approximately `(538, 1894)`, directly over the normal
  GO-button area rather than in the historic `y>=2100` reward band. The
  detector now checks this center band only when the top HUD is dimmed by a
  modal and only accepts a green button overlapping `GO_BUTTON`; those gates
  retain the earlier protection against flat green lawn false positives on
  ordinary boards. The first live tap revealed a 172,000 cash reward and a
  chained standard-band COLLECT popup.

## Known device/session facts
- Phone connected via USB (wireless debugging blocked by the phone being on
  a different Wi-Fi subnet than localnet, which has no wireless adapter).
- Package name: `com.scopely.monopolygo`.
- The Android emulator (AVD) crashes on this specific game due to a
  Berberis (ARM translation layer) bug — unrelated to any of the above;
  the real phone has no such issue.

### 2026-09-18: Specific mini-games precede broad screen detectors
A captured live Infinite Harvest PICK A BOX screen simultaneously returned true
for is_pick_a_box_screen(), is_build_menu_open(), and is_color_wheel_screen().
The live and Windows scripts had identical hashes before repair; no file revert
was found. Both cmd_loop() and sleep_keeping_awake() now check Pick a Box and
purple Roll Doubles before the broad color-wheel and BUILD checks. BUILD is
after the remaining specific mini-games and before generic popup dismissal.
Preserve this precedence: dedicated handlers can overlap broad color heuristics.
Regression tests deliberately make BUILD and color wheel true while each target
event is active, exercising both loops. Live box cleared on first calibrated GO
tap and normal rolls resumed. Purple priority is regression-tested; live jail
verification is recorded in TASKS.md when available.

## Blue Color Wheel SPIN (2026-09-19)

The wheel rim can match the quit dialog color samples. Require OCR word QUIT
and GAME or CANCEL before dismissing a quit dialog. A blue SPIN screenshot
passes the wheel detector and fails quit detection. The 21-test suite covers
this overlap; live verification cleared SPIN and resumed normal play.

## Multiplier max: bounded observed cycling (2026-09-19)

`get_multiplier()` used to accept only a single digit 1-3 and every
`_multiplier_action()` call assumed x3 was the fixed, permanent cap. That
assumption is gone: `get_multiplier()` now parses the full digit run as one
number (rejecting anything outside 1..`MULTIPLIER_SANITY_MAX` (50) as
unreadable OCR garbage rather than trusting it), and the actual cap is
discovered live by `_probe_multiplier_max()`:

- Taps the badge once, re-screenshots, and compares the new reading to the
  highest value seen so far in this pass.
- As long as it keeps climbing, the cap hasn't been reached - keep tapping.
- The first tap that makes the reading go DOWN (wrap back toward x1) proves
  the value seen right before that drop was the true cap. It then taps back
  up exactly that many times to resettle there, and confirms it landed
  correctly before returning success.
- Bounded by `MULTIPLIER_MAX_PROBE_TAPS` (30) total taps so a persistent OCR
  glitch that always reads "higher" can't tap forever - if that bound is
  hit without ever observing a wrap, it just keeps the highest confirmed
  reading rather than continuing to guess.
- An unreadable badge (before the first tap, mid-probe, or during the
  tap-back-to-max step) stops the probe immediately and returns "unknown"
  (`None`) rather than tapping blind or guessing a value.
- `_multiplier_probe_blocked()` re-checks every other known popup/dialog
  detector (quit dialog, COLLECT, Pick a Box, bonus-roll, color wheel,
  switch-opponent, match-3, raid, BUILD menu, any card/purchase-upsell
  popup) before every single tap in the probe - unlike the rest of the
  per-tick loop (which only checks these once per tick, before deciding
  what to do), a probe pass can span several taps/screenshots of its own,
  so it re-verifies nothing else appeared between them instead of trusting
  a screen state read one or more taps ago. It never taps GO_BUTTON - only
  ever `MULTIPLIER_BADGE`.
- `_multiplier_action()` (used by both `cmd_multiplier` and the main loop)
  caches the confirmed max in `_multiplier_cache` rather than reprobing
  every tick (which would mean occasionally cycling all the way back down
  to x1 and re-climbing just to re-confirm nothing changed). It only
  reprobes when: no cap is cached yet, the live reading exceeds the cached
  cap (a boosted event raised it), or `MULTIPLIER_REPROBE_TICKS` (~15min at
  `interval_s=1.3`) have passed since the last probe - this last case is
  what lets the loop pick up a mid-session cap increase (e.g. a
  boosted-rewards event starting) that wouldn't otherwise be visible from
  the current reading alone.
- New CLI command `multiplier-max` runs one probe pass standalone (does not
  read/write the loop's cache), for manual verification against a live
  device without needing `loop` running.

**Live verification (2026-09-19, real device, real taps, phone
`0B191FDD4000Q2`):** ran `multiplier-max` against the live phone while the
supervised `loop` was mid roll-empty-backoff (so nothing else was tapping
the badge concurrently). Observed real output:

```
multiplier detected: 1 (raw OCR: '"x1') - probing for current max.
after probe tap 1: multiplier = x2 (raw OCR: '"2')
after probe tap 2: multiplier = x3 (raw OCR: '"3')
after probe tap 3: multiplier = x1 (raw OCR: '"x1')
Wrap-around detected (x3 -> x1); true max is x3. Tapping 2 more time(s) to return to it.
Settled at observed max: x3.
```

A follow-up read-only check (`get_multiplier()`, no tap) confirmed the
badge was left sitting at `x3`. This confirms the mechanism works
end-to-end on the real device and that x3 remains the actual currently
available cap as of this date - no live evidence of any currently-active
event raising it further was observed or claimed.

Regression suite: 43 tests (21 pre-existing + 22 new, in
`MultiplierProbeTest`/`GetMultiplierParsingTest`/
`MultiplierActionCacheTest`/`MultiplierMaxCommandTest`), all offline/mocked
except the live spot-check above.

## Third-party software license records

Maintain a project-local `Third_party_licenses.md` following the format in
`C:/projects/smos/Third_party_licenses.md`. For each third-party component,
record its name, verified license (and version-specific exceptions), official
source URL, and how this project uses it. Group related components under
clear headings. Include libraries, SDKs, copied code, bundled tools and models;
record optional components as optional rather than implying they are installed.

Update the record when adding, upgrading, replacing or removing dependencies.
Verify terms against the actual component/version; do not guess from a similar
package name. Keep unresolved licensing questions explicit before distribution.
Preserve upstream copyright notices and include license/NOTICE texts when
required; a summary file does not replace those obligations. The project's own
license does not override third-party rights or automatically relicense them.
Keep proprietary source and credentials out of shared skill bundles and public
artifacts. This convention does not change this project's existing license.

Primary review: settle at the observed maximum before rolling, never add a
post-probe tap from a stale reading, and stop on failed probes. A 30-tap
bound does not establish a confirmed maximum. Changed readings trigger
a fresh probe; OCR values above 1000 are rejected as implausible.

## Multiplier OCR fallback (2026-09-20)
The live x1 badge was read as xt by the original crop, blocking all rolls.
If the primary crop has no digits, re-read a tighter glyph crop at 4x scale
using color and a white-text mask. Require both complete x-number readings
to agree; never substitute letters for digits. The original broad crop remains
primary for larger multipliers. Uncertain reads still stop without blind taps.

Reconnection check: an additional inner crop (700,1730,770,1778) excludes the animated x5 badge rim. Color and mask must still both return the same complete multiplier.

Tap-loop follow-up: badge animations at 0.4 seconds yielded stale OCR. Wait 2 seconds after each multiplier tap. Prefer two complete matching color/mask reads over single OCR (live x1 was misread x4). A GO tap log is not proof of rolling: verify dice count, board movement or earnings changed.

Current OCR rule (supersedes earlier fallback notes): only two full matching x-number reads may drive multiplier control. Remove loose-digit fallback entirely: it repeatedly read x1 as 4 after jail. Re-probes have a 60-second monotonic cooldown; during uncertain/cooldown states do not tap either badge or GO.

## 2026-09-20: low-dice recovery and faster frame checks
- Fixed a live false-empty result: 3/60 dice had 2.79% blue fill, below the old 3% threshold. A contiguous blue patch spanning three columns and three rows near the pill's left edge now counts as available; isolated blue noise does not.
- Decode each screenshot once and reuse it across detectors. File replacement invalidates the frame and per-frame region OCR cache. Capture writes atomically with fast PNG compression.
- Normal idle interval is 0.35s; animation-specific waits, multiplier consensus, 2s badge settling and 60s failed-probe cooldown remain.
- During empty-dice backoff, recheck every 15s instead of 300s. The outer 2h window still exists but exits as soon as dice return.
- Benchmark on the same captured board: ten repeated pixel detectors, median of five passes, 512.22ms before versus 6.43ms with the decoded frame cached (~80x). This excludes capture, OCR, input and game animation; it is not an end-to-end gameplay speedup.
- Live verification: observed x3 maximum, actual roll reduced dice 3/60 to 0/60 and cash changed 768164 to 794864. No claim of a higher available multiplier. Other event paths covered by regression tests, not all replayed live.
- 46 regression tests passed. Both live scripts match the workstation source. Rollback copies are under ~/.local/state/monopoly-speed-backup/ on the deployment host.
Follow-up: check confirmed empty dice BEFORE multiplier verification. Zero-dice badge changes must not cause repeated cap probes. Regression suite now 47 tests, including no badge/GO taps while empty.

## 2026-09-20: themed BUILD recovery
The Little M's Room footer was readable while price OCR was garbled and the
header pixel was teal. Detect a named city followed by valid 0..30/30 progress
in the bottom footer as another BUILD signature. Keep event handlers first.
Close recovery now confirms the menu before each bounded close attempt and
refreshes the screen afterward. Dice backoff returns to rolling as soon as
dice reappear, without first reopening BUILD. Build visits have a 30-second
cooldown, at most two card rounds and a ten-second card-action budget; every
card tap rechecks the menu so board completion cannot cause blind taps.
52 regression tests pass. The saved failing live screen now detects as BUILD.

## Purchase-loop guard (2026-09-22)
Automatic play no longer opens the shop from its persistent notification badge.
Detected orange-X purchase modals are handled before COLLECT, with two close-only
attempts maximum until a non-modal frame is observed. Persistent offers pause
for 15 seconds without taps. Unknown dimmed popups no longer receive blind center
or fixed bottom-X taps; manual dismissal may be required. Reward chains stop
when a detected purchase upsell appears. This does not prove detection of every
future store design. Current regression suite: 56 tests. Live deployment observed
normal board/empty-dice monitoring; purchase popup path tested offline only.

2026-09-22 billing-screen follow-up (supersedes earlier live-test limitation):
The observed Google Play sheet was cancelled with Android Back; the game confirmed cancellation. The Profit Herder offer's close button was above the old scan range. Expanded orange-X detection to y=230..550. Shape-detected reward buttons now require recognized COLLECT/CLAIM/GO text; prices and locked FREE offers are rejected. Every tap checks exact Monopoly foreground focus and fails closed if billing or an unknown window has focus. This is defense in depth, not a guarantee against every future store layout or a focus change between check and input.
60 regression tests pass. Deployed scripts and workstation mirrors match SHA256 f74e95589aa1bddd327aed32717200294bfaae1e6226f8c5189ed911519a489f. Live automation closed the actual offer on its first close-only attempt, returned to the board with 0/60 dice, and runs as one loop. Earlier source backups retained beside deployed scripts. Preserve these guards; never restore blind popup taps.

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

## Productive mini-game play (2026-09-23)
Supersedes the ten-minute treasure visit limit: continue while level or hammer count progresses. Leave at zero hammers or after 45 seconds without progress. Reinforced gold-star tiles now qualify only with a blue tile background; flood-fill keeps gold and blue components separate. Retry budget is two taps per tile/color/level, allowing reinforced tiles to change state. Existing purchase and foreground guards remain. 87 tests pass locally and on Localnet. Tutorial and event entry remain manual; this does not add support for every mini-game. Final source hash: 6ef39b0f5c61d3cbc6ac24ac014aee04e1b1570a47289226d49cad618e5b427c.

Live gold-star verification: all four remaining reinforced tiles on level 5 were detected; automation completed the treasure and reached the 9,700,000 cash COLLECT reward. Generic verified reward handler claimed it. Productive play resumed with no manual tile taps.


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


2026-09-23 railroad Chance recovery: live Halloween CHANCE / HEAD TO THE NEAREST RAILROAD IF YOU DARE card blocked at 95/60 dice. Specific white-card geometry plus exact OCR now precedes generic popup/purchase handling in both loop paths; two guarded center taps maximum, retries reset only after unobstructed screen. Unknown/purchase text is rejected; existing purchase/focus protections remain. 93 tests passed on workstation and Localnet. Live first tap advanced to match-3, which completed and collected its reward automatically. Single loop verified. Source, localnet-bin and both installed scripts SHA256 87d6598c0eaf3ee716a78a11c380ec88357c69c3b3d984495996f03cf07a83f1. Backup: ~/.local/state/monopoly-chance-backup. This handles the verified railroad card, not all future Chance designs.

Pi live follow-up: move badge/fallback BUILD visits before the next GO, after specific screen and empty-dice handling. Respect the existing visit cooldown and re-evaluate after every attempted visit; never roll from its pre-visit frame. The old post-GO visit raced roll animations and repeatedly failed to open BUILD. 101 regression tests pass, including ordering and failed-visit re-evaluation checks.

2026-10-02 audit follow-up: multiplier OCR uses the cached decoded frame, caches its full two-read result only for that capture, and tries the last successful crop first while still requiring a new agreeing pair on each new image. Unknown-popup observation polls in 2 seconds before bounded navigation is exhausted, but first Back remains delayed at least 15 seconds and only two attempts are permitted. Optional MONOPOLY_METRICS reports capture/OCR timing each minute. Optional MONOPOLY_DIAGNOSTICS retains at most 12 screenshots, rate-limited by failure type to once per minute. Pi enables both. 105 regression tests pass. User ended the planned hour early once the game returned to GO with zero dice; future minigame-layout support is not claimed.

2026-10-02 Pi Halloween title wrapping: long player names put Board on a second line. Keep original title read, then use the observed (190,200,650,315) text-only crop with PSM 6 if possessive Board validation fails. Still require multiple ring targets for entry and preserve bounded choices and foreground/purchase guards. 106 tests pass on Windows and Pi. Live first house choice advanced and awarded 9 treats; final completion verification in progress.
Completion verified: house event returned to board; one-time Win Win tutorial manually advanced. Follow-up Spooky Express 40 dice collected automatically; board 61/60. No general tutorial handler added.

2026-10-03 BUILD exclusion: a dice fraction plus at least two of WINS, ALBUM, FRIENDS in the footer identifies main board even when GO sparkles resemble BUILD card icons. Never let green-icon fallback override that main-board evidence. 107 tests pass. Pi user service remains manually started, active, with linger and restart-on-failure.

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

### Final follow-up after the 20-minute watch
Confirmed-board navigation now short-circuits Color Wheel outlined-title OCR during multiplier checks. Live board classification measured 0.652s; the saved real wheel remained accepted and the saved BUILD menu rejected. 132 tests passed on all three hosts. Additional validation continued after the watch; Pi normal play remains active. Final normalized source SHA256: 48a1da7dabcc8900dbba3d13af788a86c213468ef4f136d1a2d7216d30c63821

## 2026-10-09 Space-themed raid recovery completed
The observed space-themed raid stalled because a white background cross was treated as a target. Detect measured red ring reticles first; require angular ring coverage for white targets too, rejecting crosses and filled squares. Raid support was documented September 6, 2026; this is a variant fix, not a new mini-game introduction. Existing foreground, purchase, bounded-action and multiplier guards remain intact.
149 tests passed on Windows, Pi and Localnet. Live guarded recovery selected the actual red target, detected/tapped COLLECT and returned to the normal board. The single Pi user service resumed normal play; keep mode preserves the observed x5 badge. Rollback: ~/.local/state/monopoly-assist/backups/space-raid-20261009T213034Z. Source SHA256: ae49842cffb83e70757e8f66b409adc6d2358edee9e783b7d9ebb1b80d7f8665; Pi changes only the ADB path and hashes 2cf996d4f6432342b26ba652fa4c847f586a4c4257e3836b19856a5574f816ba. Localnet fallback remains inactive.
