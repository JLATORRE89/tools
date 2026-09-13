# Monopoly GO Assistant

Automates the repetitive parts of playing "Monopoly GO" (`com.scopely.monopolygo`)
on a real Android phone connected over USB: rolling dice, bumping the reward
multiplier, buying building upgrades, playing the match-3 mini-game, handling
raids, dismissing card popups and bonus events, and running unattended for
hours at a time.

This is a **copy** of the live application. The canonical, actively-deployed
copy runs on `localnet` (an Ubuntu 24.04 box on the LAN) at `~/bin/`. This
folder is a snapshot for reference/version history on the Windows side — to
actually run it, deploy these files to `localnet` (see "Deploying" below).

There is no accessibility API or UI tree available for this game (confirmed
via `uiautomator dump` — it's a single opaque `unitySurfaceView`), so
everything here works by taking screenshots, reading pixel colors/OCR at
fixed calibrated coordinates, and injecting taps via `adb`.

## Files

| File | What it is |
|---|---|
| `monopoly-go-assist` | The core Python automation script (`roll\|multiplier\|build\|match3\|raid\|loop\|status`) |
| `monopoly-go-supervisor` | Bash wrapper: runs `monopoly-go-assist loop` with auto-restart-on-crash and logging, for unattended overnight runs |
| `RULES.md` | Full mechanics reference: every confirmed game mechanic, calibrated coordinate, color signature, and known limitation. **Read this before changing coordinates or detectors.** |
| `CODEX_HANDOFF.md` | A point-in-time detailed handoff snapshot (written for another AI agent to pick up the project) — useful background, but `RULES.md` is the living source of truth |

## Dependencies

### On the host machine that runs the script (`localnet`)
- **Python 3** (standard library only for most of it: `subprocess`, `sys`, `re`, `time`)
- **Pillow** (`pip install Pillow` / `from PIL import Image`) — used for all
  pixel-color and screenshot-region reading
- **`tesseract-ocr`** (system package, e.g. `apt install tesseract-ocr`) —
  invoked via `subprocess` as a plain `tesseract` command-line call, used
  only for the multiplier badge OCR (roll-count reading uses a color
  heuristic instead — tesseract proved unreliable there, see `RULES.md`)
- **Android SDK platform-tools (`adb`)** — the script hardcodes the path
  `/ai/android-sdk/platform-tools/adb`; adjust the `ADB` constant at the top
  of `monopoly-go-assist` if your `adb` lives elsewhere
- Standard coreutils for the supervisor script: `bash`, `date`, `mkdir`,
  `pgrep`, `kill`, `sleep`

### Hardware / device setup
- A **real Android phone** with the actual Monopoly GO app installed and
  signed in — the Android emulator does **not** work for this app (a
  confirmed Berberis/ARM-translation-layer crash, unrelated to this
  automation; see `RULES.md`)
- **USB debugging enabled** on the phone, connected via USB to the host
  running the script (wireless `adb` was attempted but blocked by the phone
  and host being on different networks in this setup)
- Phone screen resolution **1080x2340** — every tap/detection coordinate in
  this script is calibrated for that exact resolution. A different device
  will need full recalibration (see the "coordinates drift" section of
  `RULES.md` for the calibration methodology: crop-and-view or color-blob
  detection against a real screenshot, never guess from a description)
- **No PIN/pattern/biometric lock** on the phone (or the auto-unlock swipe
  built into the script won't work) — a plain swipe-to-dismiss lock screen
  is fine and is what this was built against
- Recommended: `adb shell settings put system screen_off_timeout 1800000`
  (extends screen timeout to 30 min) to reduce how often the phone's screen
  needs to be woken up mid-run

### Auto-exposure to a local LLM chat UI (optional)
If dropped into a directory served by a tool like `local-bin-mcp` (any
executable-script-to-MCP-tool bridge), both scripts become callable as
tools from a chat interface (e.g. Open WebUI) without extra configuration —
this is how the canonical deployment on `localnet` is normally invoked
("ask the local AI to run monopoly-go-assist loop").

## Deploying (to `localnet` or any other host)

```bash
scp monopoly-go-assist monopoly-go-supervisor user@host:~/bin/
ssh user@host "chmod +x ~/bin/monopoly-go-assist ~/bin/monopoly-go-supervisor"
```

## Running

```bash
# One-off actions:
ssh user@host "~/bin/monopoly-go-assist status"     # report state, no action
ssh user@host "~/bin/monopoly-go-assist roll"        # single roll if available
ssh user@host "~/bin/monopoly-go-assist build"       # open BUILD, buy what's affordable
ssh user@host "~/bin/monopoly-go-assist raid"        # find and tap a raid target

# Unattended overnight run (auto-restarts on crash, logs to ~/ai-logs/):
ssh user@host "~/bin/monopoly-go-supervisor start"
ssh user@host "~/bin/monopoly-go-supervisor status"
ssh user@host "~/bin/monopoly-go-supervisor stop"
```

**Important:** always invoke by full path (`~/bin/monopoly-go-supervisor`,
not the bare command) when running non-interactively over
`ssh host "command"` — `~/bin` is typically not on `PATH` for non-interactive
shells, so the bare command fails with "command not found" in that context
even though it works fine from an interactive login shell.

## What it handles automatically

- Rolling (single-tap whenever the roll pill isn't empty)
- The reward multiplier (taps to increase, never resets past the x3 cap)
- Building upgrades (opens BUILD the instant its red badge shows something
  pending, not on a fixed timer)
- The match-3 "steal" mini-game (auto-detects and plays it blind)
- The "Roll Doubles" purple-button bonus event
- Chance/Community Chest/other card popups (detected via the dimmed-board
  overlay they all share, not any one card's specific color)
- Raid/heist target screens (finds and taps a target reticle; does **not**
  avoid smoke/cooldown targets — that still needs visual judgment this
  doesn't attempt)
- Chained reward popups (a raid win followed immediately by a separate
  event reward, etc.)
- Keeping the phone's screen awake/unlocked during the long (2h) backoff
  it uses when out of rolls, so a multi-hour unattended run doesn't get
  interrupted by the screen locking

See `RULES.md` for the full detail behind every one of these, including
exact calibrated coordinates, color thresholds, and known remaining gaps
(raid smoke-avoidance, the "board complete" green GO! button is still
uncalibrated, etc).
