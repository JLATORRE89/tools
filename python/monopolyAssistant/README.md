# Monopoly GO Assistant

## Keep a manually selected multiplier

Use `monopoly mode keep` to let the player choose the badge value. The agent reads
the verified value but never cycles the badge or probes for a higher maximum.
Manual changes are respected on later turns. The preference persists and takes
effect on the next check, including interrupting an automatic probe.

`monopoly mode max` restores bounded automatic maximum discovery; `monopoly mode
status` shows the policy. The active Pi is configured to **keep** at the user's
request. A game-imposed reduction when dice are insufficient is still possible;
the agent does not attempt to undo the game's own limit. No numeric value is
guessed or forced. Explicit `multiplier-max` remains a deliberate one-off command.

Mini-game introduction dates, scope and Git references are recorded in
[MINIGAME_HISTORY.md](MINIGAME_HISTORY.md). Use `git log --show-notes` to display
historical commit comments. The October 9 Halloween title-separator fix is live
verified; details are in RULES.md.

The active installation is on **rpi3**, using the user service
`monopoly-assist.service`. Windows source is in this repository; LocalNet
retains synchronized fallback copies and stays inactive while the phone is
connected to the Pi. The Pi runtime uses `/usr/bin/adb`; the LocalNet runtime
uses `/ai/android-sdk/platform-tools/adb`. Current scope and validation are
recorded in `RULES.md` and `TASKS.md`.

## Phone connection monitoring

Keep the service running when unplugging the phone. It polls ADB every five
seconds while idle. No device, offline transport, pending USB debugging approval,
multiple devices and game-not-in-foreground have distinct waiting states in the
log. Approve USB debugging on the phone, unlock it and open Monopoly GO to resume.
The assistant does not enable debugging or launch/unlock the game for you.

One authorized device is selected automatically. With multiple attached devices,
set `MONOPOLY_DEVICE_SERIAL` in the service environment to select the intended
one. Capture, focus checks and inputs stay bound to that serial. A new device
clears previous screenshots, OCR, multiplier and mini-game state before play.
Unsupported screen geometry stays idle; the current layout is 1080 by 2340.
`monopoly status` and `monopoly logs` show why the service is waiting.

Side-icon free items: the source checks visible FREE labels on both sides during
play and dice waiting, then claims only separately verified free gift buttons.
Paid, locked, conditional, mixed-price or unreadable offers are skipped. Checks
have a five-minute cooldown and one bounded icon visit at a time. Current scope
and pending live Pi validation are in RULES.md. No automatic purchases or use
of paid inventory is added.

## Raspberry Pi desktop installation

On Raspberry Pi OS / Debian, install `python3`, `python3-pil`, `adb`,
`tesseract-ocr`, `tesseract-ocr-eng`, `python3-tesserocr`, `android-sdk-platform-tools-common`,
and `desktop-file-utils`. Copy `install_pi.py`, `monopoly-go-assist`,
`test_monopoly_go_assist.py`, and `RULES.md` to a staging folder on the Pi,
then run `python3 install_pi.py` as the desktop user, without sudo.

The installer runs the regression suite against the installed copy, adapts
only its ADB path to `/usr/bin/adb`, and creates a **Monopoly Assist** desktop
launcher plus a `monopoly` Bash alias. Open a new terminal or run
`source ~/.bash_aliases` in an existing one.

- `monopoly` starts one background instance; repeated launches reuse it.
- `monopoly stop` stops it.
- `monopoly status` shows service/device status and recent logs.
- `monopoly logs` follows the log; Ctrl+C exits the log viewer.

The user service is not enabled at boot. Runtime logs are stored at
`~/.local/state/monopoly-assist/assistant.log`; installed code, usage notes,
and regression results are in `~/.local/share/monopoly-assist/`.
Connect the calibrated phone over USB, approve USB debugging on that phone,
and bring the unlocked game to the foreground. Installation verification
without the phone does not establish live gameplay performance.

The Pi service enables `MONOPOLY_INPROCESS_OCR=1`: a reusable Tesseract
engine avoids loading the language model for every crop. Each image clears
recognition/adaptive state and has a 30-second recognition timeout. If the
optional binding is unavailable, command-line OCR remains the fallback.
Other deployments retain command-line OCR unless explicitly enabled.

The Pi also enables minute-level capture/OCR timing logs and diagnostic
screenshots for persistent unknown popups, unreadable multipliers, and raid
reward timeouts. Diagnostics are under
`~/.local/state/monopoly-assist/diagnostics/`, limited to twelve screenshots
and one capture per failure type per minute. Disable them with
`MONOPOLY_DIAGNOSTICS=0`; timing logs use `MONOPOLY_METRICS=0`.
Multiplier OCR results are reused only within the same captured frame;
each new frame still requires two complete agreeing readings.

Automates the repetitive parts of playing "Monopoly GO" (`com.scopely.monopolygo`)
on a real Android phone connected over USB: rolling dice, bumping the reward
multiplier, buying building upgrades, playing the match-3 mini-game, handling
raids, dismissing card popups and bonus events, and running unattended for
hours at a time.

This folder contains the maintained source and regression tests. Deployment
instructions below for LocalNet describe the fallback installation; the Pi
installation and launcher are described above.

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
- The reward multiplier (taps to increase toward its currently-available
  cap, discovered live via bounded observed cycling rather than assumed
  fixed at x3 - see "Multiplier max" in `RULES.md`; run
  `monopoly-go-assist multiplier-max` to check/settle it manually)
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

Performance update: screen checks reuse a decoded frame, tiny nonempty dice fills
are recognized, and empty-dice monitoring rechecks every 15 seconds. Normal
idle polling is 0.35 seconds; game animations and safe multiplier verification
still take time. See RULES.md for measured scope and live validation.

Build recovery update: themed menus are also recognized by their city/progress
footer. Build visits are bounded and have a 30-second cooldown; closing is
verified before rolling resumes. Empty-dice monitoring does not reopen BUILD
before checking whether dice returned.

See [September 22 log audit](LOG_AUDIT_20260922.md) for capture/disconnection recovery, popup protections, timestamped status and remaining live checks.
