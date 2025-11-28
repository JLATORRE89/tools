#!/usr/bin/env python3
# Author: Jason LaTorre
"""
WD My Cloud Mount Utility - v1.0.0
=================================

Mount or unmount WD My Cloud SMB shares defined in config.xml.

Usage examples:
    python -m nas_tools.wd_mount --setup
    python -m nas_tools.wd_mount --status
    python -m nas_tools.wd_mount --umount
"""

from __future__ import annotations

import argparse
import logging
import platform
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

from . import wd_discovery

__all__ = ["mount_share", "unmount_share", "main"]
__version__ = "1.0.0"
__author__ = "Jason LaTorre"

PACKAGE_ROOT = Path(__file__).resolve().parent
LOG_FILE = PACKAGE_ROOT / "wd_mount.log"
NO_DEVICE_MESSAGE = wd_discovery.NO_DEVICE_MESSAGE


def _ensure_log_folder() -> None:
    PACKAGE_ROOT.mkdir(parents=True, exist_ok=True)


def _build_logger(debug: bool = False) -> logging.Logger:
    _ensure_log_folder()
    logger = logging.getLogger("nas_tools.wd_mount")
    if not logger.handlers:
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    return logger


def _resolve_device_ip(config: Dict[str, str], devices: List[Dict[str, str]]) -> str:
    """Pick the device IP based on config overrides or discovery results."""
    if config.get("ip"):
        return config["ip"]

    hostname = (config.get("hostname") or "").lower()
    if hostname:
        for device in devices:
            names = [
                (device.get("friendly_name") or "").lower(),
                (device.get("model") or "").lower(),
            ]
            if hostname in names or hostname in (device.get("server") or "").lower():
                return device["ip"]

    return devices[0]["ip"] if devices else ""


def mount_share(config: Dict[str, str], ip: str, logger: logging.Logger, debug: bool = False) -> bool:
    """Mount the configured SMB share on the current platform."""
    share = config.get("smb_share", "Public")
    username = config.get("username", "guest")
    password = config.get("password", "")
    mount_point = Path(config.get("mount_point", "/mnt/mycloud"))
    drive_letter = config.get("drive_letter", "Z:").rstrip(":") + ":"
    os_name = platform.system().lower()

    logger.info("Attempting to mount %s:%s on %s", ip, share, os_name)

    if os_name == "windows":
        target = f"\\\\{ip}\\{share}"
        command = ["net", "use", drive_letter, target]
        if username:
            command.append(f"/user:{username}")
        # Always append a password argument so Windows does not prompt interactively.
        command.append(password or "")
    elif os_name == "darwin":
        mount_point.mkdir(parents=True, exist_ok=True)
        target = f"//{username}:{password}@{ip}/{share}"
        command = ["mount_smbfs", target, str(mount_point)]
    else:
        # Linux/Unix platforms rely on the CIFS client for SMB access.
        mount_point.mkdir(parents=True, exist_ok=True)
        options = [
            f"username={username}",
            f"password={password}",
            "rw",
            "vers=3.0",
            "soft",
        ]
        command = [
            "mount",
            "-t",
            "cifs",
            f"//{ip}/{share}",
            str(mount_point),
            "-o",
            ",".join(options),
        ]

    if debug:
        logger.debug("Executing mount command: %s", command)

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        logger.error("Mount command failed: %s", exc)
        print(f"Mount failed for {ip}:{share}")
        return False

    if os_name == "windows":
        print(f"Mounted {share} to {drive_letter}")
    else:
        print(f"Mounted {share} to {mount_point}")
    logger.info("Mounted share %s from %s", share, ip)
    return True


def unmount_share(config: Dict[str, str], logger: logging.Logger, debug: bool = False) -> bool:
    """Unmount the previously mounted share."""
    mount_point = Path(config.get("mount_point", "/mnt/mycloud"))
    drive_letter = config.get("drive_letter", "Z:").rstrip(":") + ":"
    os_name = platform.system().lower()

    if os_name == "windows":
        command = ["net", "use", drive_letter, "/delete", "/y"]
    else:
        command = ["umount", str(mount_point)]

    if debug:
        logger.debug("Executing unmount command: %s", command)

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        logger.error("Unmount command failed: %s", exc)
        print(f"Unmount failed for {mount_point if os_name != 'windows' else drive_letter}")
        return False

    if os_name == "windows":
        print(f"Unmounted {drive_letter}")
    else:
        print(f"Unmounted {mount_point}")
    logger.info("Unmounted share target %s", mount_point if os_name != "windows" else drive_letter)
    return True


def _report_no_devices(logger: logging.Logger, status_only: bool) -> None:
    logger.warning(NO_DEVICE_MESSAGE)
    print(NO_DEVICE_MESSAGE)
    if status_only:
        print("0")


def main(argv: List[str] | None = None) -> int:
    """CLI entry point for mounting helper."""
    parser = argparse.ArgumentParser(description="WD My Cloud SMB mount helper")
    parser.add_argument("--status", action="store_true", help="Print machine-friendly status output")
    parser.add_argument("--debug", action="store_true", help="Enable verbose logging")
    parser.add_argument("--setup", action="store_true", help="Interactive configuration helper")
    parser.add_argument("--umount", action="store_true", help="Unmount the configured share")
    args = parser.parse_args(argv)

    logger = _build_logger(args.debug)

    if args.setup:
        wd_discovery.interactive_setup()
        return 0

    config = wd_discovery.load_config()
    devices = wd_discovery.find_nas(verbose=not args.status, debug=args.debug)
    ip = _resolve_device_ip(config, devices)

    if not ip:
        _report_no_devices(logger, args.status)
        return 1

    if args.umount:
        success = unmount_share(config, logger, debug=args.debug)
        if args.status:
            print("1" if success else "0")
        return 0 if success else 2

    success = mount_share({**config, "ip": ip}, ip, logger, debug=args.debug)
    if args.status:
        print(f"1 {ip}" if success else "0")
    return 0 if success else 2


if __name__ == "__main__":
    sys.exit(main())
