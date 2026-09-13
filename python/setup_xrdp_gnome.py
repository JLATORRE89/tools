#!/usr/bin/env python3
"""
setup_xrdp_gnome.py

Set up RDP access to a headless/monitor-less Ubuntu GNOME box from Windows,
using xrdp + xorgxrdp (NOT GNOME's own gnome-remote-desktop, which has known
handover bugs on Ubuntu 24.04 that make it unreliable for this scenario).

WHY NOT gnome-remote-desktop (GNOME's native RDP):
  We tried it first since it's built in, but it's broken for exactly this
  headless-box scenario on Ubuntu 24.04 (GNOME 46):
    - Its per-user "Remote Desktop" mode (screen-sharing an existing login)
      needs to store the RDP credential in the gnome-keyring Secret Service.
      Creating that keyring collection requires an interactive "set a keyring
      password" prompt, which needs a working prompter UI - one never
      appears in a monitor-less session, so the credential write just hangs
      forever, headlessly unfixable short of a real physical display.
    - Its system-level "Remote Login" mode (headless, GDM-broker based) DOES
      work for the first connection phase, but the handoff to the actual
      per-session process ("Handover.desktop") does its own separate NTLM
      check against that same broken per-user credential store, so it fails
      with "Could not find user in SAM database" / SEC_E_NO_CREDENTIALS and
      the client sees a black screen then disconnect.
    - This is a confirmed upstream/Ubuntu bug, not a config mistake: see
      https://gitlab.gnome.org/GNOME/gnome-remote-desktop/-/issues/272 and
      Ubuntu Launchpad bug #2141992. The real fix landed only in
      gnome-remote-desktop ~49.2, while Ubuntu 24.04 LTS ships 46.x with no
      backport available (the one SRU that existed targeted 25.10, which is
      already end-of-life).
  xrdp sidesteps all of this: it authenticates via PAM against the real
  Linux account password (no gnome-keyring involved) and has no multi-phase
  handover, so none of the above applies.

What this does on the remote host (over SSH, using your existing ~/.ssh/config
alias or a hostname):
  - installs xrdp, xorgxrdp, dbus-x11
  - fixes the TLS key permission issue (adds xrdp user to the ssl-cert group)
  - rewrites /etc/xrdp/startwm.sh to explicitly launch the Ubuntu GNOME (Xorg)
    session and correctly import DISPLAY/XAUTHORITY into the systemd --user
    activation environment (without this, snap-packaged GUI apps silently
    fail to open windows)
  - disables gnome-remote-desktop if it's running, so it doesn't fight xrdp
    for port 3389
  - optionally resets the target Linux user's password, since xrdp
    authenticates against the real account password via PAM
  - opens the port in ufw if ufw is active

What this does on this Windows machine:
  - stores the RDP credentials in Windows Credential Manager (cmdkey), so
    you aren't prompted for a password
  - writes a ready-to-use .rdp file to your Desktop

Requires: an SSH client on PATH, key-based SSH access to the target already
working, and sudo on the target (passworded sudo is fine - you'll be
prompted; NOPASSWD sudo works too).

Examples:
  py setup_xrdp_gnome.py localnet --user jason --set-password
  py setup_xrdp_gnome.py 192.168.1.80 --user jason --set-password --desktop-name "LocalNet Desktop"
  py setup_xrdp_gnome.py localnet --user jason --status
"""

from __future__ import annotations

import argparse
import getpass
import logging
import shlex
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
LOG_DIR = SCRIPT_DIR / "logs"

STARTWM_SH = r"""#!/bin/sh
# xrdp X session start script - modified by setup_xrdp_gnome.py
# Launches the Ubuntu GNOME (Xorg) session and imports DISPLAY/XAUTHORITY
# into the systemd --user activation environment so systemd/snap-launched
# apps (Firefox, Firmware Updater, etc.) can authenticate to the X server.

if test -r /etc/profile; then
	. /etc/profile
fi

if test -r ~/.profile; then
	. ~/.profile
fi

export GNOME_SHELL_SESSION_MODE=ubuntu
export XDG_CURRENT_DESKTOP=ubuntu:GNOME
export XDG_SESSION_TYPE=x11
export XAUTHORITY="$HOME/.Xauthority"
systemctl --user import-environment DISPLAY XAUTHORITY XDG_SESSION_TYPE 2>/dev/null

if test -x /usr/bin/gnome-session; then
	exec /usr/bin/gnome-session --session=ubuntu
fi

test -x /etc/X11/Xsession && exec /etc/X11/Xsession
exec /bin/sh /etc/X11/Xsession
"""

log = logging.getLogger("setup_xrdp_gnome")


def setup_logging(log_file: Path, verbose: bool) -> None:
    log.setLevel(logging.DEBUG)

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG if verbose else logging.INFO)
    console.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(console)

    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )
    log.addHandler(file_handler)
    log.debug("Logging to %s", log_file)


class RemoteError(RuntimeError):
    pass


def run_ssh(host: str, remote_cmd: str, input_data: str | None = None,
            timeout: int = 60, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command on the remote host over ssh, logging it."""
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host, remote_cmd]
    log.debug("ssh %s <<< %r", host, remote_cmd[:200])
    result = subprocess.run(
        cmd,
        input=input_data,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.stdout:
        log.debug("stdout: %s", result.stdout.strip())
    if result.stderr:
        log.debug("stderr: %s", result.stderr.strip())
    if check and result.returncode != 0:
        raise RemoteError(
            f"Command failed on {host} (exit {result.returncode}): {remote_cmd}\n{result.stderr}"
        )
    return result


def sudo_wrap(script: str, sudo_password: str | None) -> tuple[str, str | None]:
    """Wrap a remote shell script so it runs as root via sudo.

    Uses `sudo -S` so this works whether the target has NOPASSWD sudo
    (the extra stdin data is simply ignored) or requires a real password.
    """
    quoted = shlex.quote(script)
    remote_cmd = f"sudo -S -p '' bash -c {quoted}"
    stdin = (sudo_password or "") + "\n"
    return remote_cmd, stdin


def check_ssh_reachable(host: str) -> None:
    log.info("Checking SSH connectivity to %s ...", host)
    run_ssh(host, "echo ok")
    log.info("SSH OK.")


def install_packages(host: str, sudo_password: str | None) -> None:
    log.info("Installing xrdp, xorgxrdp, dbus-x11 ...")
    script = (
        "DEBIAN_FRONTEND=noninteractive apt-get update -qq && "
        "DEBIAN_FRONTEND=noninteractive apt-get install -y xrdp xorgxrdp dbus-x11"
    )
    cmd, stdin = sudo_wrap(script, sudo_password)
    run_ssh(host, cmd, input_data=stdin, timeout=180)
    log.info("Packages installed.")


def fix_tls_permissions(host: str, sudo_password: str | None) -> None:
    log.info("Fixing xrdp TLS key permissions (adding xrdp to ssl-cert group) ...")
    cmd, stdin = sudo_wrap("adduser xrdp ssl-cert", sudo_password)
    run_ssh(host, cmd, input_data=stdin, check=False)


def write_startwm(host: str, sudo_password: str | None) -> None:
    log.info("Writing corrected /etc/xrdp/startwm.sh ...")
    heredoc = (
        "cp /etc/xrdp/startwm.sh /etc/xrdp/startwm.sh.bak 2>/dev/null; "
        "cat > /etc/xrdp/startwm.sh << 'STARTWM_EOF'\n"
        f"{STARTWM_SH}"
        "STARTWM_EOF\n"
        "chmod +x /etc/xrdp/startwm.sh"
    )
    cmd, stdin = sudo_wrap(heredoc, sudo_password)
    run_ssh(host, cmd, input_data=stdin)
    log.info("startwm.sh updated.")


def disable_gnome_remote_desktop(host: str, sudo_password: str | None) -> None:
    log.info("Disabling gnome-remote-desktop if present (avoids port 3389 conflict) ...")
    cmd, stdin = sudo_wrap(
        "systemctl disable --now gnome-remote-desktop.service", sudo_password
    )
    run_ssh(host, cmd, input_data=stdin, check=False)


def enable_xrdp(host: str, sudo_password: str | None) -> None:
    log.info("Enabling and starting xrdp + xrdp-sesman ...")
    cmd, stdin = sudo_wrap(
        "systemctl enable --now xrdp xrdp-sesman && systemctl restart xrdp-sesman xrdp",
        sudo_password,
    )
    run_ssh(host, cmd, input_data=stdin)


def open_firewall(host: str, sudo_password: str | None) -> None:
    log.info("Checking firewall (ufw) ...")
    cmd, stdin = sudo_wrap(
        "ufw status | grep -q 'Status: active' && ufw allow 3389/tcp || true",
        sudo_password,
    )
    run_ssh(host, cmd, input_data=stdin, check=False)


def set_remote_password(host: str, user: str, password: str, sudo_password: str | None) -> None:
    log.info("Setting Linux account password for %s (needed for xrdp/PAM auth) ...", user)
    script = f"echo {shlex.quote(user + ':' + password)} | chpasswd"
    cmd, stdin = sudo_wrap(script, sudo_password)
    run_ssh(host, cmd, input_data=stdin)
    log.info("Password set.")


def resolve_target_ip(host: str) -> str:
    """Resolve the actual hostname/IP ssh will connect to, for the Windows side."""
    try:
        result = subprocess.run(
            ["ssh", "-G", host], capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.splitlines():
            if line.lower().startswith("hostname "):
                return line.split(None, 1)[1].strip()
    except Exception as exc:  # noqa: BLE001
        log.debug("ssh -G failed: %s", exc)
    return host


def check_port_open(ip: str, port: int = 3389, timeout: float = 5.0) -> bool:
    log.info("Testing TCP connectivity to %s:%d ...", ip, port)
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            log.info("Port %d is open on %s.", port, ip)
            return True
    except OSError as exc:
        log.warning("Could not reach %s:%d (%s)", ip, port, exc)
        return False


def store_windows_credential(ip: str, user: str, password: str) -> None:
    if sys.platform != "win32":
        log.info("Not on Windows; skipping Credential Manager step.")
        return
    log.info("Storing RDP credential in Windows Credential Manager ...")
    target = f"TERMSRV/{ip}"
    subprocess.run(["cmdkey", f"/delete:{target}"], capture_output=True, text=True)
    result = subprocess.run(
        ["cmdkey", f"/generic:{target}", f"/user:{user}", f"/pass:{password}"],
        capture_output=True,
        text=True,
    )
    log.debug(result.stdout.strip())
    if result.returncode != 0:
        raise RuntimeError(f"cmdkey failed: {result.stderr}")
    log.info("Credential stored for %s.", target)


def write_rdp_file(ip: str, user: str, desktop_name: str, width: int, height: int) -> Path:
    if sys.platform != "win32":
        out_path = SCRIPT_DIR / f"{desktop_name}.rdp"
    else:
        out_path = Path.home() / "Desktop" / f"{desktop_name}.rdp"
    log.info("Writing .rdp file to %s ...", out_path)
    content = (
        f"full address:s:{ip}\n"
        f"username:s:{user}\n"
        "prompt for credentials:i:0\n"
        "authentication level:i:0\n"
        "enablecredsspsupport:i:1\n"
        "administrative session:i:0\n"
        "screen mode id:i:2\n"
        f"desktopwidth:i:{width}\n"
        f"desktopheight:i:{height}\n"
        "session bpp:i:32\n"
        "compression:i:1\n"
        "audiomode:i:0\n"
        "redirectclipboard:i:1\n"
        "redirectprinters:i:0\n"
        "autoreconnection enabled:i:1\n"
    )
    out_path.write_text(content, encoding="utf-8")
    log.info("Desktop icon ready: %s", out_path)
    return out_path


def cmd_status(host: str) -> None:
    log.info("=== Status for %s ===", host)
    checks = [
        ("xrdp service", "systemctl is-active xrdp"),
        ("xrdp-sesman service", "systemctl is-active xrdp-sesman"),
        ("gnome-remote-desktop service", "systemctl is-active gnome-remote-desktop.service || true"),
        ("port 3389 listening", "ss -tlnp 2>/dev/null | grep -q ':3389 ' && echo listening || echo NOT-listening"),
        ("startwm.sh managed by us", "grep -q 'setup_xrdp_gnome.py' /etc/xrdp/startwm.sh 2>/dev/null && echo yes || grep -q 'GNOME_SHELL_SESSION_MODE' /etc/xrdp/startwm.sh 2>/dev/null && echo 'likely (custom session vars present)' || echo no"),
    ]
    for label, remote_cmd in checks:
        result = run_ssh(host, remote_cmd, check=False)
        value = (result.stdout or result.stderr).strip() or "(no output)"
        log.info("  %-32s %s", label + ":", value)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="setup_xrdp_gnome.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "host",
        help="SSH alias (e.g. from ~/.ssh/config) or hostname/IP of the target Ubuntu box",
    )
    parser.add_argument(
        "--user", required=True, help="Linux username on the target to configure RDP for"
    )
    parser.add_argument(
        "--ip",
        help="RDP target IP/hostname for the Windows side, if different from --host "
        "(default: resolved from ssh config, or --host itself)",
    )
    parser.add_argument(
        "--set-password",
        action="store_true",
        help="Reset the target Linux account's password (required the first time, "
        "since xrdp authenticates via PAM against the real account password)",
    )
    parser.add_argument(
        "--password",
        help="Password to set/use for RDP login. If --set-password is given without "
        "this, one is generated randomly and printed/logged.",
    )
    parser.add_argument(
        "--ask-sudo-password",
        action="store_true",
        help="Prompt for the remote sudo password interactively. Omit this if the "
        "target already has passwordless (NOPASSWD) sudo configured.",
    )
    parser.add_argument(
        "--desktop-name",
        default="LocalNet Desktop",
        help="Base filename (no extension) for the .rdp file written to the Desktop "
        "(default: 'LocalNet Desktop')",
    )
    parser.add_argument("--width", type=int, default=1920, help="RDP session width (default 1920)")
    parser.add_argument("--height", type=int, default=1080, help="RDP session height (default 1080)")
    parser.add_argument(
        "--skip-windows-steps",
        action="store_true",
        help="Only configure the remote host; skip Credential Manager + .rdp file creation",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Only check the current state of xrdp on the target; make no changes",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose (debug) logging")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_file = LOG_DIR / f"setup_xrdp_gnome_{timestamp}.log"
    setup_logging(log_file, args.verbose)

    try:
        if args.status:
            check_ssh_reachable(args.host)
            cmd_status(args.host)
            return 0

        sudo_password = None
        if args.ask_sudo_password:
            sudo_password = getpass.getpass(f"sudo password for {args.user}@{args.host}: ")

        check_ssh_reachable(args.host)
        install_packages(args.host, sudo_password)
        fix_tls_permissions(args.host, sudo_password)
        write_startwm(args.host, sudo_password)
        disable_gnome_remote_desktop(args.host, sudo_password)
        enable_xrdp(args.host, sudo_password)
        open_firewall(args.host, sudo_password)

        password = args.password
        if args.set_password:
            if not password:
                import secrets
                import string

                alphabet = string.ascii_letters + string.digits
                password = "".join(secrets.choice(alphabet) for _ in range(20))
                log.info("Generated RDP password: %s", password)
            set_remote_password(args.host, args.user, password, sudo_password)
        elif not password:
            log.warning(
                "No --password given and --set-password not used: assuming the "
                "account's existing Linux password is already known to you."
            )

        target_ip = args.ip or resolve_target_ip(args.host)
        log.info("Target IP/hostname for RDP: %s", target_ip)
        check_port_open(target_ip)

        if not args.skip_windows_steps:
            if not password:
                log.warning(
                    "No password available; skipping Credential Manager step. "
                    "Pass --password or --set-password."
                )
            else:
                store_windows_credential(target_ip, args.user, password)
            write_rdp_file(target_ip, args.user, args.desktop_name, args.width, args.height)

        log.info("Done. See log for details: %s", log_file)
        return 0

    except RemoteError as exc:
        log.error("Remote command failed: %s", exc)
        return 1
    except subprocess.TimeoutExpired as exc:
        log.error("Timed out: %s", exc)
        return 1
    except Exception as exc:  # noqa: BLE001
        log.exception("Unexpected error: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
