#!/usr/bin/env python3
# Author: Jason LaTorre
"""
WD My Cloud Discovery Utility - v1.0.0
=====================================

Discover Western Digital (WD) My Cloud NAS appliances via SSDP/UPnP.

Usage examples:
    python -m nas_tools.wd_discovery --debug
    python -m nas_tools.wd_discovery --status
    python -m nas_tools.wd_discovery --setup
"""

from __future__ import annotations

import argparse
import base64
import logging
import socket
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.error import URLError
from urllib.request import urlopen

__all__ = [
    "CONFIG_FILE",
    "NO_DEVICE_MESSAGE",
    "find_nas",
    "load_config",
    "ensure_default_config",
    "interactive_setup",
]

__version__ = "1.0.0"
__author__ = "Jason LaTorre"

PACKAGE_ROOT = Path(__file__).resolve().parent
CONFIG_FILE = PACKAGE_ROOT / "config.xml"
LOG_FILE = PACKAGE_ROOT / "wd_discovery.log"
DEFAULT_TIMEOUT = 5
NO_DEVICE_MESSAGE = "No WD My Cloud devices found"

# Multicast information for SSDP queries.
SSDP_GROUP = ("239.255.255.250", 1900)
SSDP_REQUEST = "\r\n".join(
    [
        "M-SEARCH * HTTP/1.1",
        f"HOST: {SSDP_GROUP[0]}:{SSDP_GROUP[1]}",
        'MAN: "ssdp:discover"',
        "MX: 3",
        "ST: upnp:rootdevice",
        "",
        "",
    ]
)

# Template used for automatically provisioning config.xml.
DEFAULT_CONFIG_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<config>
  <network>
    <timeout>{timeout}</timeout>
  </network>
  <share>
    <hostname>{hostname}</hostname>
    <ip>{ip}</ip>
    <smb_share>{share}</smb_share>
    <username>{username}</username>
    <password encoding="base64">{password}</password>
    <mount_point>{mount_point}</mount_point>
    <drive_letter>{drive_letter}</drive_letter>
  </share>
</config>
"""


@dataclass
class DeviceInfo:
    """Lightweight structure for device metadata gathered via SSDP."""

    ip: str
    location: str
    server: str
    model: str
    friendly_name: str

    def as_dict(self) -> Dict[str, str]:
        return {
            "ip": self.ip,
            "location": self.location,
            "server": self.server,
            "model": self.model,
            "friendly_name": self.friendly_name,
        }


def _ensure_log_folder() -> None:
    PACKAGE_ROOT.mkdir(parents=True, exist_ok=True)


def _build_logger(debug: bool = False) -> logging.Logger:
    _ensure_log_folder()
    logger = logging.getLogger("nas_tools.wd_discovery")
    if not logger.handlers:
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    return logger


def _b64_encode(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def _b64_decode(value: str) -> str:
    try:
        return base64.b64decode(value).decode("utf-8")
    except Exception:
        return value


def ensure_default_config() -> None:
    """Create a starter config.xml when one is not present."""
    if CONFIG_FILE.exists():
        return
    logger = _build_logger()
    content = DEFAULT_CONFIG_TEMPLATE.format(
        timeout=DEFAULT_TIMEOUT,
        hostname="MYCLOUD",
        ip="",
        share="Public",
        username="guest",
        password=_b64_encode(""),
        mount_point="/mnt/mycloud",
        drive_letter="Z:",
    )
    CONFIG_FILE.write_text(content, encoding="utf-8")
    logger.info("Created default config.xml at %s", CONFIG_FILE)


def _write_config(data: Dict[str, str]) -> None:
    """Persist configuration data back to config.xml."""
    content = DEFAULT_CONFIG_TEMPLATE.format(
        timeout=data.get("timeout", DEFAULT_TIMEOUT),
        hostname=data.get("hostname", "MYCLOUD"),
        ip=data.get("ip", ""),
        share=data.get("smb_share", "Public"),
        username=data.get("username", "guest"),
        password=_b64_encode(data.get("password", "")),
        mount_point=data.get("mount_point", "/mnt/mycloud"),
        drive_letter=data.get("drive_letter", "Z:"),
    )
    CONFIG_FILE.write_text(content, encoding="utf-8")


def load_config() -> Dict[str, str]:
    """Load configuration values from config.xml, creating defaults if needed."""
    ensure_default_config()
    data = {
        "timeout": DEFAULT_TIMEOUT,
        "hostname": "MYCLOUD",
        "ip": "",
        "smb_share": "Public",
        "username": "guest",
        "password": "",
        "mount_point": "/mnt/mycloud",
        "drive_letter": "Z:",
    }

    try:
        root = ET.parse(CONFIG_FILE).getroot()
    except ET.ParseError as exc:
        logger = _build_logger()
        logger.error("Unable to parse config.xml: %s", exc)
        return data

    timeout_text = root.findtext("./network/timeout")
    if timeout_text and timeout_text.isdigit():
        data["timeout"] = int(timeout_text)

    share = root.find("./share")
    if share is None:
        return data

    for tag in ["hostname", "ip", "smb_share", "username", "mount_point", "drive_letter"]:
        text = share.findtext(tag)
        if text:
            data[tag] = text.strip()

    password_node = share.find("password")
    if password_node is not None:
        value = password_node.text or ""
        if password_node.attrib.get("encoding") == "base64":
            data["password"] = _b64_decode(value.strip())
        else:
            data["password"] = value.strip()

    return data


def interactive_setup() -> None:
    """Interactively collect configuration values and update config.xml."""
    cfg = load_config()
    print("Configure WD My Cloud access (press Enter to keep existing values).")
    hostname = input(f"Hostname [{cfg['hostname']}]: ").strip() or cfg["hostname"]
    ip = input(f"Static IP [{cfg.get('ip', '')}]: ").strip() or cfg.get("ip", "")
    share = input(f"Share name [{cfg['smb_share']}]: ").strip() or cfg["smb_share"]
    username = input(f"Username [{cfg['username']}]: ").strip() or cfg["username"]
    password_prompt = "Password (stored as base64) [leave blank to keep current]: "
    password = input(password_prompt)
    if not password:
        password = cfg["password"]
    mount_point = input(f"Mount point [{cfg['mount_point']}]: ").strip() or cfg["mount_point"]
    drive_letter = input(f"Windows drive letter [{cfg['drive_letter']}]: ").strip() or cfg["drive_letter"]
    timeout_input = input(f"Discovery timeout seconds [{cfg['timeout']}]: ").strip()

    try:
        timeout = int(timeout_input) if timeout_input else cfg["timeout"]
    except ValueError:
        timeout = cfg["timeout"]

    updated = {
        "hostname": hostname,
        "ip": ip,
        "smb_share": share,
        "username": username,
        "password": password,
        "mount_point": mount_point,
        "drive_letter": drive_letter.upper() if drive_letter else "Z:",
        "timeout": max(1, timeout),
    }
    _write_config(updated)
    logger = _build_logger()
    logger.info("Updated config.xml via interactive setup")
    print(f"Configuration saved to {CONFIG_FILE}")


def _ssdp_discover(timeout: int, logger: logging.Logger, debug: bool) -> List[Tuple[str, str]]:
    """Send an SSDP probe and collect responses."""
    responses: List[Tuple[str, str]] = []
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.settimeout(timeout)
    try:
        sock.sendto(SSDP_REQUEST.encode("utf-8"), SSDP_GROUP)
        start = time.time()
        while time.time() - start <= timeout:
            try:
                raw, addr = sock.recvfrom(65535)
            except socket.timeout:
                break
            payload = raw.decode("utf-8", errors="ignore")
            responses.append((addr[0], payload))
            if debug:
                logger.debug("SSDP response from %s:\n%s", addr[0], payload)
                print(f"[DEBUG] SSDP response from {addr[0]}:\n{payload}\n")
    except OSError as exc:
        logger.error("SSDP broadcast failed: %s", exc)
    finally:
        sock.close()
    return responses


def _parse_headers(payload: str) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    for line in payload.split("\r\n"):
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    return headers


def _fetch_descriptor(location: str, logger: logging.Logger) -> Dict[str, str]:
    metadata: Dict[str, str] = {}
    if not location:
        return metadata
    try:
        with urlopen(location, timeout=4) as response:
            xml_payload = response.read()
    except (URLError, OSError) as exc:
        logger.debug("Descriptor fetch failed for %s: %s", location, exc)
        return metadata

    try:
        root = ET.fromstring(xml_payload)
    except ET.ParseError as exc:
        logger.debug("Descriptor parse failed for %s: %s", location, exc)
        return metadata

    metadata["manufacturer"] = root.findtext(".//manufacturer", default="").strip()
    metadata["model"] = root.findtext(".//modelName", default="").strip()
    metadata["friendly_name"] = root.findtext(".//friendlyName", default="").strip()
    return metadata


def _looks_like_wd(headers: Dict[str, str], descriptor: Dict[str, str]) -> bool:
    server = headers.get("server", "")
    location = headers.get("location", "")
    if "wd" in server.lower() or "mycloud" in server.lower():
        return True
    manufacturer = descriptor.get("manufacturer", "").lower()
    model = descriptor.get("model", "").lower()
    friendly = descriptor.get("friendly_name", "").lower()
    match_terms = ("western", "digital", "my cloud", "wd")
    return any(term in manufacturer for term in match_terms) or any(
        term in model or term in friendly for term in match_terms
    ) or "wd2go" in location.lower()


def _identify_devices(
    responses: List[Tuple[str, str]], logger: logging.Logger
) -> List[DeviceInfo]:
    # Convert SSDP responses to DeviceInfo objects when they look like WD nodes.
    devices: List[DeviceInfo] = []
    for ip, payload in responses:
        headers = _parse_headers(payload)
        descriptor = _fetch_descriptor(headers.get("location", ""), logger)
        if not _looks_like_wd(headers, descriptor):
            continue
        device = DeviceInfo(
            ip=ip,
            location=headers.get("location", ""),
            server=headers.get("server", ""),
            model=descriptor.get("model") or headers.get("server", "WD My Cloud"),
            friendly_name=descriptor.get("friendly_name") or descriptor.get("model") or "WD My Cloud",
        )
        devices.append(device)
        logger.info("Device discovered at %s (%s)", device.ip, device.friendly_name)
    return devices


def find_nas(verbose: bool = True, debug: bool = False) -> List[Dict[str, str]]:
    """
    Discover WD My Cloud devices on the local network.

    Args:
        verbose: When True, print discovered devices for humans.
        debug: When True, emit verbose SSDP traces.

    Returns:
        List of device dictionaries containing ip, location, server, model, and friendly_name.
    """
    logger = _build_logger(debug)
    cfg = load_config()
    timeout = max(int(cfg.get("timeout", DEFAULT_TIMEOUT)), 1)

    responses = _ssdp_discover(timeout, logger, debug)
    devices = _identify_devices(responses, logger)

    if verbose and devices:
        for idx, device in enumerate(devices, start=1):
            print(f"{idx}. {device.friendly_name} @ {device.ip}")
            if device.location:
                print(f"   Descriptor: {device.location}")

    return [device.as_dict() for device in devices]


def _report_no_devices(logger: logging.Logger, status_only: bool) -> None:
    logger.warning(NO_DEVICE_MESSAGE)
    print(NO_DEVICE_MESSAGE)
    if status_only:
        print("0")


def main(argv: List[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="WD My Cloud SSDP discovery helper")
    parser.add_argument("--status", action="store_true", help="Print machine-friendly status output")
    parser.add_argument("--debug", action="store_true", help="Enable verbose logging and SSDP dumps")
    parser.add_argument("--setup", action="store_true", help="Interactive configuration helper")
    args = parser.parse_args(argv)

    if args.setup:
        interactive_setup()
        return 0

    devices = find_nas(verbose=not args.status, debug=args.debug)
    if not devices:
        _report_no_devices(_build_logger(args.debug), args.status)
        return 1

    if args.status:
        print(f"1 {devices[0]['ip']}")
        return 0

    print(f"Found {len(devices)} WD device(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
