# Codex Handoff: Monopoly GO Automation Project

Written 2026-09-06, handing off from a Claude Code session to whoever
(Codex or otherwise) picks this up next. This file is meant to be
self-contained — read this, then `RULES.md` in the same directory for the
full mechanics reference, and you should be able to continue without
needing to ask the user to re-explain anything already covered here.

## What this project is

The user plays "Monopoly GO" (`com.scopely.monopolygo`) on their real
Android phone, connected via USB to a Linux box on the LAN called
`localnet` (Ubuntu 24.04, SSH alias `localnet`, IP 192.168.1.80). The goal
is to have "our local AI" (an Open WebUI instance running on `localnet`)
automate the repetitive parts of play — rolling dice, bumping the reward
multiplier, buying building upgrades, and flipping match-3 tiles — driven
by a screenshot-and-tap loop over `adb`, not by any accessibility API
(this game exposes a single opaque `unitySurfaceView` with no UI tree —
confirmed via `uiautomator dump`, see RULES.md).

Everything the automation knows about the game's mechanics, coordinates,
and confirmed rules lives in **`/ai/monopolygo/RULES.md`** on localnet —
treat that as the durable source of truth and keep it updated as you learn
more. This handoff file is a snapshot of *where things stood* and *what to
do next*, not a replacement for RULES.md.

## Where things live

| What | Path |
|---|---|
| Mechanics/rules doc (source of truth) | `localnet:/ai/monopolygo/RULES.md` |
| This handoff doc | `localnet:/ai/monopolygo/CODEX_HANDOFF.md` |
| The automation script (deployed, live) | `localnet:~/bin/monopoly-go-assist` |
| Reference copy (Windows side) | `C:\projects\tools\python\localnet-bin\monopoly-go-assist` |
| adb binary | `/ai/android-sdk/platform-tools/adb` on localnet |
| Screenshot scratch file | `/tmp/mg_screen.png` on localnet |
| Related wrapper scripts (all in `~/bin` on localnet, auto-exposed to Open WebUI via `local-bin-mcp`) | `android-adb`, `android-gradle`, `android-emulator`, `android-tap-record`, `android-screen-record` |

The script is auto-exposed as a tool to the Open WebUI instance on
localnet via a pre-existing MCP bridge (`~/projects/local-bin-mcp/bin_tools_mcp_http.py`,
which turns any executable in `~/bin` into a callable tool). You do not
need to register it anywhere — dropping/updating the file in `~/bin` is
sufficient, as long as it stays executable (`chmod +x`).

To run it manually for testing: `ssh localnet` then
`monopoly-go-assist {roll|multiplier|build|match3|loop|status}`.

## Current script state (as of this handoff)

The script was just updated and redeployed with two bug fixes plus a
simplification, all verified live against the real phone
(`monopoly-go-assist status` → `roll pill fill ratio: 0.97 (has rolls)`,
`multiplier: 3 (raw: '"x3')` — both correct).

1. **Roll-count reading**: OCR (tesseract) was tried and abandoned for the
   roll-count pill after ~10 failed preprocessing attempts — this game's
   font/background combo defeats it reliably. Replaced with a **color
   fill-ratio heuristic**: scan the horizontal line `y=2152` from
   `x=380` to `x=703` on the 1080x2340 screenshot, count pixels where
   `b > 200 and g > 140 and r < 220 and b > r` (blue = filled), divide by
   the scan width. Calibrated against a real "17/30" reading (~60.7%
   measured vs ~56.7% naive-expected — close enough to trust for
   empty-vs-not classification, not for an exact count).
2. **Roll rule simplified**: per the user's explicit direction — *"as long
   as it is not 0/0, we can keep rolling single (not 3x)"* and *"if it is
   0/0, we need to wait the remaining time"* — the old <2/>10 threshold +
   long-press-for-auto-roll logic was **removed entirely** from
   automation. `cmd_roll()` now just single-taps GO whenever
   `fill_ratio >= 0.03`, and returns exit code `2` (instead of tapping)
   when the pill reads empty, signaling the caller to back off. Long-press
   is still a real, confirmed mechanic (documented in RULES.md) but is no
   longer used by any automated command — it was too fragile/unnecessary
   once single-tap-always-when-available proved sufficient.
3. **`cmd_loop()` now consumes that backoff signal**: previously it always
   slept a fixed `interval_s` (4s) between ticks regardless of what
   `cmd_roll()` returned. Now, if `cmd_roll()` returns `2`, the loop sleeps
   `ROLL_EMPTY_BACKOFF_S` (60s, a fixed guess — see limitations below)
   instead of 4s, so it doesn't busy-poll while rolls regenerate.
4. **Multiplier regex fixed**: the old regex `r"[xX]\s*(\d)"` required
   literally seeing an "x" character in the OCR output, but tesseract
   frequently drops it on this badge's font. Replaced with: strip all
   non-digit characters from the OCR text, then return the first digit
   found that is `1`, `2`, or `3`. This is more permissive but still safe
   (the badge can only ever show 1, 2, or 3).
5. **Dead code removed**: a `get_roll_level()` function existed that
   referenced `ROLL_RATIO_LOW`/`ROLL_RATIO_HIGH` constants which had
   already been renamed to `ROLL_RATIO_EMPTY` in an earlier edit — calling
   it would have raised `NameError`. It was unused by any `cmd_*` function,
   so it was deleted rather than fixed.

The full current script (for reference — but the deployed copy on
localnet at `~/bin/monopoly-go-assist` is authoritative; if this snippet
and that file ever disagree, trust the live file):

```python
#!/usr/bin/env python3
"""
monopoly-go-assist: reads on-screen state via OCR/color-heuristics and
applies the confirmed rules for rolling / multiplier tapping / building.
See /ai/monopolygo/RULES.md for the full mechanics writeup and why
coordinates need periodic recalibration.
"""
import subprocess, sys, re, time

ADB = "/ai/android-sdk/platform-tools/adb"
GO_BUTTON = (539, 1901)
MULTIPLIER_BADGE = (725, 1740)
BUILD_ICON = (256, 2137)
BUILD_CLOSE_X = (538, 2267)
BUILD_CARD_Y = 1966
BUILD_CARD_XS = (111, 326, 541, 756, 971)
SCREENSHOT = "/tmp/mg_screen.png"

ROLL_PILL_Y = 2152
ROLL_PILL_X_START = 380
ROLL_PILL_X_END = 703
ROLL_RATIO_EMPTY = 0.03
ROLL_EMPTY_BACKOFF_S = 60

def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def screenshot():
    sh(f"{ADB} exec-out screencap -p > {SCREENSHOT}")

def ocr_region(box):
    from PIL import Image
    img = Image.open(SCREENSHOT)
    crop = img.crop(box)
    crop_path = "/tmp/mg_crop.png"
    crop.save(crop_path)
    result = sh(f"tesseract {crop_path} - --psm 7 2>/dev/null")
    return result.stdout.strip()

def _is_pill_blue(rgb):
    r, g, b = rgb
    return b > 200 and g > 140 and r < 220 and b > r

def get_roll_fill_ratio():
    from PIL import Image
    img = Image.open(SCREENSHOT).convert("RGB")
    total = ROLL_PILL_X_END - ROLL_PILL_X_START
    blue = sum(
        1 for x in range(ROLL_PILL_X_START, ROLL_PILL_X_END)
        if _is_pill_blue(img.getpixel((x, ROLL_PILL_Y)))
    )
    return blue / total if total else 0.0

def get_multiplier():
    text = ocr_region((685, 1700, 765, 1785))
    cleaned = re.sub(r"[^0-9]", "", text)
    for ch in cleaned:
        if ch in "123":
            return int(ch), text
    return None, text

def tap(x, y):
    sh(f"{ADB} shell input tap {x} {y}")

def long_press(x, y, duration_s=2.5):
    sh(f"{ADB} shell input motionevent DOWN {x} {y}")
    steps = max(1, int(duration_s / 0.24))
    for _ in range(steps):
        time.sleep(0.24)
        sh(f"{ADB} shell input motionevent MOVE {x} {y}")
    sh(f"{ADB} shell input motionevent UP {x} {y}")

def cmd_roll():
    screenshot()
    ratio = get_roll_fill_ratio()
    print(f"roll pill fill ratio: {ratio:.2f}")
    if ratio < ROLL_RATIO_EMPTY:
        print("Pill reads empty (0/0). Not tapping - back off and recheck later.")
        return 2
    print("Rolls available: single tap.")
    tap(*GO_BUTTON)
    return 0

def cmd_multiplier():
    screenshot()
    mult, raw = get_multiplier()
    print(f"multiplier detected: {mult} (raw OCR: {raw!r})")
    if mult is None:
        print("Could not read multiplier via OCR. No action taken.")
        return 1
    if mult >= 3:
        print("Already at cap (x3). Not tapping (would reset to x1).")
        return 0
    print("Tapping multiplier to increase.")
    tap(*MULTIPLIER_BADGE)
    return 0

def cmd_status():
    screenshot()
    ratio = get_roll_fill_ratio()
    mult, raw2 = get_multiplier()
    print(f"roll pill fill ratio: {ratio:.2f} ({'EMPTY' if ratio < ROLL_RATIO_EMPTY else 'has rolls'})")
    print(f"multiplier: {mult} (raw: {raw2!r})")
    return 0

def cmd_build():
    print("Opening BUILD menu.")
    tap(*BUILD_ICON)
    time.sleep(1.0)
    for x in BUILD_CARD_XS:
        tap(x, BUILD_CARD_Y)
        time.sleep(0.6)
    print("Closing BUILD menu.")
    tap(*BUILD_CLOSE_X)
    return 0

def cmd_match3():
    xs = (175, 420, 652, 895)
    ys = (1132, 1452, 1772)
    print("Flipping all 12 tiles in the match-3 grid.")
    for y in ys:
        for x in xs:
            tap(x, y)
            time.sleep(0.7)
    return 0

def cmd_loop(interval_s=4):
    print(f"Starting continuous loop (roll + multiplier + periodic build), "
          f"checking every {interval_s}s. Ctrl-C to stop.")
    tick = 0
    try:
        while True:
            roll_result = cmd_roll()
            cmd_multiplier()
            tick += 1
            if tick % 15 == 0:
                cmd_build()
            if roll_result == 2:
                print(f"Backing off {ROLL_EMPTY_BACKOFF_S}s (rolls empty).")
                time.sleep(ROLL_EMPTY_BACKOFF_S)
            else:
                time.sleep(interval_s)
    except KeyboardInterrupt:
        print("Loop stopped.")
    return 0

def usage():
    print("Usage: monopoly-go-assist {roll|multiplier|build|match3|loop|status}")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    actions = {
        "roll": cmd_roll, "multiplier": cmd_multiplier, "build": cmd_build,
        "match3": cmd_match3, "loop": cmd_loop, "status": cmd_status,
    }
    if cmd in actions:
        sys.exit(actions[cmd]())
    usage()
    sys.exit(1)
```

## What's verified working, live, on the real device

- `roll` — single-tap logic and empty detection both confirmed via
  `status` (fill ratio 0.97 read correctly as "has rolls").
- `multiplier` — regex fix confirmed live: raw OCR `'"x3'` parsed
  correctly as `3`.
- `build` — opens BUILD, taps all 5 card slots, closes via X. Confirmed
  working in earlier testing this session (before today's edits, but
  those edits didn't touch `cmd_build()`).
- `match3` — confirmed working with a **real cash payout** (36,523 →
  42,093) in earlier testing this session.
- `loop` — the tick logic and backoff branch are new; only smoke-tested
  via a single `status` call, **not yet run end-to-end unattended for an
  extended period** (e.g., 10+ minutes). This is the most valuable thing
  to test next if you want higher confidence before leaving it running
  unsupervised.

## What is NOT done / good next steps

1. **Run `loop` unattended for a real session** (several minutes+) and
   watch for: does the empty-backoff actually kick in correctly when
   rolls run out; does `build` firing every ~15 ticks cause any visible
   problems (e.g. opening BUILD while a roll animation is still playing);
   does anything about the game's camera/UI drift over a longer session
   in a way that breaks the hardcoded coordinates (see the "coordinates
   drift" warning at the top of RULES.md — this has bitten us before).
2. **The 60s empty-backoff is a guess**, not derived from the actual
   regen countdown shown on-screen ("5 Rolls ready in HH:MM" — OCR on that
   text failed on both attempts made this session). If you want to do
   better: either retry OCR with different preprocessing specifically for
   that countdown text's font (different from the pill's font, might
   behave differently), or apply the same color-heuristic methodology used
   for the pill fill-ratio to some other visual signal, or just leave it
   as a fixed interval — the user has not indicated the 60s guess is
   currently a problem.
3. **`build` doesn't check affordability first** — it just taps all 5
   card slots and relies on the game silently no-op'ing on ones you can't
   afford. Confirmed safe, but wastes a little time/taps. Not urgent.
4. **Raid target selection (avoiding smoke/cooldown buildings) is
   unscripted** — explicitly left to a human or a future vision-model call,
   per RULES.md. If you want to tackle this: it likely needs either a
   proper image-classification step (smoke vs. clean) or another
   color-heuristic (smoke effects may have a distinctive dark/gray color
   signature worth testing against a real screenshot).
5. **Match3 has no memory/strategy** — it blind-flips all 12 tiles in
   fixed order rather than remembering revealed icons and targeting known
   pairs. Works well enough today (real payout confirmed) but a smarter
   version is a plausible improvement if you have screenshots-between-taps
   budget to spare (current version deliberately skips that to be fast).
6. **Coordinates are calibrated for one specific camera position/session**
   and are known to drift (see RULES.md's opening warning — this cost real
   debugging time earlier, e.g. BUILD icon was off by ~550px from an
   initial guess). If the automation starts silently doing nothing, the
   first thing to check is whether a screenshot's actual pixel content at
   the hardcoded coordinates still matches expectations — recalibrate via
   crop-and-view or color-blob detection, not by re-guessing from a
   description.

## Environment / access notes

- Phone is connected to `localnet` via **USB**, not wireless debugging —
  wireless was attempted but the phone is on a different Wi-Fi subnet than
  localnet (which has no wireless adapter at all), so USB is the only
  current path. If the phone gets unplugged/replugged, you may need to
  re-authorize USB debugging on the phone (tap "Allow" on the prompt).
- `adb devices` should show exactly one device; if `unauthorized`, the
  phone needs its "Allow USB debugging" prompt re-tapped (unplug/replug to
  re-trigger it if it doesn't reappear).
- Package name is `com.scopely.monopolygo`.
- **Do not try to run this game in the Android emulator/AVD on localnet**
  — it crashes on this specific app due to a confirmed Berberis (ARM
  translation layer) bug, unrelated to anything in this automation. The
  real phone has no such issue. This was root-caused via a full `logcat`
  tombstone backtrace, not guessed — see RULES.md's closing section for
  detail if you want to double check that conclusion.
- There is a standing housekeeping item unrelated to this project but on
  the same box: a temporary NOPASSWD sudo rule
  (`/etc/sudoers.d/90-temp-jason-nopasswd`) was added earlier in this
  effort's larger session (for xrdp/Android SDK setup work) and has not
  yet been removed. Not required for monopoly-go-assist to function, but
  worth flagging if you're doing any broader cleanup on this box.

## Recommended first move if you're an agent picking this up cold

Run `ssh localnet "monopoly-go-assist status"` to confirm the phone is
still connected and readable, then read `/ai/monopolygo/RULES.md` in full
for mechanics context before changing anything.
