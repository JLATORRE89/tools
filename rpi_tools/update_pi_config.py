#!/usr/bin/env python3
"""
Update Raspberry Pi config.txt on a specified Windows drive to support ELECROW 7 Inch Touchscreen Monitor for Raspberry Pi.

Example:
  py update_pi_config.py --drive D

Edits:
  D:\config.txt

What it does (idempotent / safe to re-run):
- Makes a timestamped backup next to config.txt
- Ensures model-specific sections exist: [pi3], [pi4], [pi5]
- Moves/normalizes VC4 overlay + max_framebuffers into those sections:
    [pi3] dtoverlay=vc4-fkms-v3d ; max_framebuffers=2
    [pi4] dtoverlay=vc4-fkms-v3d ; max_framebuffers=2
    [pi5] (no vc4 overlay forced) ; max_framebuffers=2
- Removes global (top-level) dtoverlay=vc4-kms-v3d / vc4-fkms-v3d and global max_framebuffers=2
  so Pi 3/4/5 can coexist cleanly.
- Ensures your HDMI LCD settings live under [all] and are present/updated:
    hdmi_force_edid_audio=1
    max_usb_current=1
    hdmi_force_hotplug=1
    config_hdmi_boost=7
    hdmi_group=2
    hdmi_mode=87
    hdmi_drive=2
    display_rotate=0
    hdmi_cvt 1024 600 60 6 0 0 0
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
from typing import List, Tuple, Optional

# --- HDMI/LCD settings from your image ---
ALL_REQUIRED_LINES = [
    "hdmi_force_edid_audio=1",
    "max_usb_current=1",
    "hdmi_force_hotplug=1",
    "config_hdmi_boost=7",
    "hdmi_group=2",
    "hdmi_mode=87",
    "hdmi_drive=2",
    "display_rotate=0",
    "hdmi_cvt 1024 600 60 6 0 0 0",
]

# --- Model-specific desired config ---
MODEL_TARGETS = {
    "pi3": {
        "dtoverlay": "dtoverlay=vc4-fkms-v3d",
        "max_framebuffers": "max_framebuffers=2",
    },
    "pi4": {
        "dtoverlay": "dtoverlay=vc4-fkms-v3d",
        "max_framebuffers": "max_framebuffers=2",
    },
    "pi5": {
        # Do not force vc4-kms/fkms overlays on Pi 5
        "dtoverlay": None,
        "max_framebuffers": "max_framebuffers=2",
    },
}


def normalize_line(s: str) -> str:
    """Normalize for comparison."""
    s = s.strip()
    if not s:
        return ""
    # normalize whitespace for space-separated commands like hdmi_cvt
    if " " in s and "=" not in s:
        s = " ".join(s.split())
    return s


def is_comment_or_blank(line: str) -> bool:
    t = line.strip()
    return (t == "") or t.startswith("#")


def backup_file(path: Path) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_suffix(path.suffix + f".bak.{stamp}")
    backup.write_bytes(path.read_bytes())
    return backup


def parse_sections(lines: List[str]) -> List[Tuple[Optional[str], List[str]]]:
    """
    Split file into sections.
    Returns list of (section_name, section_lines) where section_name is:
      None for the global/top section (before any [section])
      "all", "pi3", etc. for bracketed sections
    Section header line itself is included as the first line of that section (except global).
    """
    blocks: List[Tuple[Optional[str], List[str]]] = []
    current_name: Optional[str] = None
    current_lines: List[str] = []

    def flush():
        nonlocal current_name, current_lines
        if current_lines:
            blocks.append((current_name, current_lines))
        current_lines = []

    for line in lines:
        t = line.strip()
        if t.startswith("[") and t.endswith("]") and len(t) >= 3:
            # new section starts
            flush()
            current_name = t[1:-1].strip().lower()
            current_lines = [line]
        else:
            current_lines.append(line)

    flush()
    return blocks


def rebuild_from_blocks(blocks: List[Tuple[Optional[str], List[str]]]) -> List[str]:
    out: List[str] = []
    for _, blines in blocks:
        out.extend(blines)
    return out


def find_block(blocks: List[Tuple[Optional[str], List[str]]], name: str) -> int:
    name = name.lower()
    for i, (n, _) in enumerate(blocks):
        if n == name:
            return i
    return -1


def insert_model_blocks_before_all(blocks: List[Tuple[Optional[str], List[str]]], new_blocks: List[Tuple[str, List[str]]]) -> None:
    """
    Insert blocks like [pi3], [pi4], [pi5] before [all] if it exists,
    else append at end.
    """
    idx_all = find_block(blocks, "all")
    if idx_all == -1:
        # append
        for name, bl in new_blocks:
            blocks.append((name, bl))
    else:
        # insert in order before [all]
        insert_at = idx_all
        for name, bl in new_blocks:
            blocks.insert(insert_at, (name, bl))
            insert_at += 1


def remove_global_vc4_and_framebuffers(blocks: List[Tuple[Optional[str], List[str]]], changes: List[str]) -> None:
    """
    Remove any global dtoverlay=vc4-... lines and global max_framebuffers=2 line.
    Only from the global (None) block.
    """
    idx_global = find_block(blocks, None)  # type: ignore[arg-type]
    # find_block doesn't work with None; do it directly:
    idx_global = -1
    for i, (n, _) in enumerate(blocks):
        if n is None:
            idx_global = i
            break
    if idx_global == -1:
        return

    name, glines = blocks[idx_global]
    new_glines: List[str] = []
    removed_any = False

    for line in glines:
        t = normalize_line(line)
        if is_comment_or_blank(line):
            new_glines.append(line)
            continue

        if t in ("dtoverlay=vc4-kms-v3d", "dtoverlay=vc4-fkms-v3d"):
            removed_any = True
            changes.append(f"Removed global line: {t}")
            continue

        if t == "max_framebuffers=2":
            removed_any = True
            changes.append("Removed global line: max_framebuffers=2")
            continue

        new_glines.append(line)

    if removed_any:
        blocks[idx_global] = (name, new_glines)


def ensure_model_section(blocks: List[Tuple[Optional[str], List[str]]], model: str, changes: List[str]) -> None:
    """
    Ensure a given model section exists and contains the desired lines.
    Also remove any vc4-kms/fkms line in that model section if not desired.
    """
    model = model.lower()
    idx = find_block(blocks, model)

    if idx == -1:
        # create minimal block
        header = f"[{model}]"
        blines = [header, "\n"]
        blocks.append((model, blines))
        changes.append(f"Created section: [{model}]")
        idx = len(blocks) - 1

    sec_name, sec_lines = blocks[idx]

    # Build new section lines
    desired_overlay = MODEL_TARGETS[model]["dtoverlay"]
    desired_fb = MODEL_TARGETS[model]["max_framebuffers"]

    out_lines: List[str] = []
    saw_overlay = False
    saw_fb = False
    removed_overlay_lines: List[str] = []

    for j, line in enumerate(sec_lines):
        # always keep the header line as-is
        if j == 0 and line.strip().startswith("[") and line.strip().endswith("]"):
            out_lines.append(line.strip() + "\n")
            continue

        if is_comment_or_blank(line):
            out_lines.append(line if line.endswith("\n") else line + "\n")
            continue

        t = normalize_line(line)

        # Handle dtoverlay lines
        if t.startswith("dtoverlay="):
            if t in ("dtoverlay=vc4-kms-v3d", "dtoverlay=vc4-fkms-v3d"):
                if desired_overlay is None:
                    removed_overlay_lines.append(t)
                    continue
                # normalize to desired
                if t != desired_overlay:
                    removed_overlay_lines.append(t)
                    # don't keep old, we'll insert desired later
                    continue
                else:
                    saw_overlay = True
                    out_lines.append(desired_overlay + "\n")
                    continue
            # Keep other dtoverlay lines (e.g., dwc2 stuff in cm sections)
            out_lines.append(line if line.endswith("\n") else line + "\n")
            continue

        # Handle max_framebuffers
        if t.startswith("max_framebuffers="):
            if t != desired_fb:
                out_lines.append(desired_fb + "\n")
                changes.append(f"Updated [{model}] max_framebuffers to: {desired_fb}")
            else:
                out_lines.append(desired_fb + "\n")
            saw_fb = True
            continue

        out_lines.append(line if line.endswith("\n") else line + "\n")

    # If overlay was removed or missing, insert desired overlay (for pi3/pi4)
    if desired_overlay is not None and not saw_overlay:
        out_lines.append(desired_overlay + "\n")
        changes.append(f"Ensured [{model}] has: {desired_overlay}")

    # If overlay should not exist (pi5) and we removed any, record it
    for rm in removed_overlay_lines:
        changes.append(f"Removed [{model}] line: {rm}")

    # Ensure max_framebuffers exists
    if not saw_fb and desired_fb:
        out_lines.append(desired_fb + "\n")
        changes.append(f"Ensured [{model}] has: {desired_fb}")

    blocks[idx] = (sec_name, out_lines)


def ensure_all_section_and_hdmi(blocks: List[Tuple[Optional[str], List[str]]], changes: List[str]) -> None:
    """
    Ensure [all] section exists and contains/updates the required HDMI lines.
    """
    idx_all = find_block(blocks, "all")
    if idx_all == -1:
        # create [all] at end
        blocks.append(("all", ["[all]\n", "\n"]))
        changes.append("Created section: [all]")
        idx_all = len(blocks) - 1

    sec_name, sec_lines = blocks[idx_all]

    required_by_key = {}
    required_full = []
    for req in ALL_REQUIRED_LINES:
        if "=" in req:
            required_by_key[req.split("=", 1)[0].strip()] = req
        else:
            required_full.append(req)

    # We'll rebuild the [all] section
    out: List[str] = []
    existing_norm = set()

    # Track which keys were seen/handled
    seen_keys = set()
    saw_header = False

    for j, line in enumerate(sec_lines):
        if j == 0 and line.strip().lower() == "[all]":
            out.append("[all]\n")
            saw_header = True
            continue

        if is_comment_or_blank(line):
            out.append(line if line.endswith("\n") else line + "\n")
            continue

        t = normalize_line(line)
        existing_norm.add(t)

        if "=" in t:
            key = t.split("=", 1)[0].strip()
            if key in required_by_key:
                desired = required_by_key[key]
                seen_keys.add(key)
                if normalize_line(desired) != t:
                    out.append(desired + "\n")
                    changes.append(f"Updated [all] {key} to: {desired}")
                else:
                    out.append(desired + "\n")
                continue

        # keep other settings in [all]
        out.append(line if line.endswith("\n") else line + "\n")

    if not saw_header:
        # Section header got mangled somehow; normalize
        out.insert(0, "[all]\n")

    # Add missing key=value requirements
    for key, desired in required_by_key.items():
        if key not in seen_keys:
            out.append(desired + "\n")
            changes.append(f"Added to [all]: {desired}")

    # Add missing full-line requirements (hdmi_cvt ...)
    out_norm = {normalize_line(x) for x in out if not is_comment_or_blank(x)}
    for req in required_full:
        if normalize_line(req) not in out_norm:
            out.append(req + "\n")
            changes.append(f"Added to [all]: {req}")

    blocks[idx_all] = (sec_name, out)


def update_config_text(original_text: str) -> Tuple[str, List[str]]:
    # Normalize line endings to \n for processing
    original_text = original_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [l + "\n" for l in original_text.split("\n")]
    if lines and lines[-1] == "\n":
        # split created a trailing empty line
        pass

    blocks = parse_sections(lines)
    changes: List[str] = []

    # Ensure model sections exist; if missing, we want them inserted before [all] if possible.
    missing_models = [m for m in ("pi3", "pi4", "pi5") if find_block(blocks, m) == -1]
    if missing_models:
        new_blocks = []
        for m in missing_models:
            new_blocks.append((m, [f"[{m}]\n", "\n"]))
        # Insert before [all] if present; else append
        insert_model_blocks_before_all(blocks, new_blocks)
        for m in missing_models:
            changes.append(f"Created section: [{m}]")

    # Remove global vc4 overlay + max_framebuffers so they don't override model behavior
    remove_global_vc4_and_framebuffers(blocks, changes)

    # Ensure each model section has the desired lines
    ensure_model_section(blocks, "pi3", changes)
    ensure_model_section(blocks, "pi4", changes)
    ensure_model_section(blocks, "pi5", changes)

    # Ensure [all] contains required HDMI LCD settings
    ensure_all_section_and_hdmi(blocks, changes)

    # Rebuild file and return with Windows line endings
    new_lines = rebuild_from_blocks(blocks)
    # Ensure ends with newline
    new_text = "".join(new_lines)
    if not new_text.endswith("\n"):
        new_text += "\n"
    new_text = new_text.replace("\n", "\r\n")
    return new_text, changes


def main() -> int:
    ap = argparse.ArgumentParser(description="Modify Raspberry Pi config.txt on a specified drive (Windows 11).")
    ap.add_argument("--drive", required=True, help="Drive letter like D (or a path like D:\\).")
    args = ap.parse_args()

    drive = args.drive.strip().rstrip("\\/")
    if len(drive) == 1 and drive.isalpha():
        root = Path(drive.upper() + ":\\")
    else:
        root = Path(drive)

    config_path = root / "config.txt"
    if not config_path.exists():
        print(f"[!] Not found: {config_path}")
        print("    Make sure you selected the SD card/boot partition drive letter and config.txt is in its root.")
        return 2

    raw = config_path.read_bytes()
    try:
        original_text = raw.decode("utf-8")
    except UnicodeDecodeError:
        original_text = raw.decode("latin-1")

    backup = backup_file(config_path)
    print(f"[+] Backup created: {backup}")

    new_text, changes = update_config_text(original_text)

    if not changes:
        print("[=] No changes needed (already configured).")
        return 0

    config_path.write_text(new_text, encoding="utf-8", newline="\r\n")
    print(f"[+] Updated: {config_path}")
    print("\nChanges:")
    for c in changes:
        print(f" - {c}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
