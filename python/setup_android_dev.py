#!/usr/bin/env python3
"""
setup_android_dev.py

Set up a headless Android development environment on a remote Linux box:
JDK, Android Studio (GUI, for interactive use over RDP/VNC), the Android SDK
command-line tools, platform-tools/build-tools/emulator packages, a KVM-
accelerated AVD, and the local-bin-mcp bridge wrapper scripts that expose
Gradle build/test, adb device control, and emulator lifecycle management as
Open WebUI tools (see localnet-bin/ in this same directory for their source).

Everything is installed under one directory (default /ai) rather than system
paths, so it's easy to find, move, or wipe independently of the OS.

Requires: an SSH client on PATH, key-based SSH access to the target already
working, and sudo on the target (passworded sudo is fine - you'll be
prompted; NOPASSWD sudo works too).

KVM note: the emulator needs /dev/kvm for reasonable performance. This script
loads the kvm_amd/kvm_intel module and adds the user to the kvm group, but if
virtualization (SVM/AMD-V or VT-x) is disabled in the BIOS, module loading
will fail with "Operation not supported" - that requires a physical trip into
BIOS setup (Advanced/CPU Configuration, usually labeled "SVM Mode" on AMD
boards) and cannot be fixed remotely. The script detects and reports this
rather than silently continuing with a slow, unaccelerated emulator.

Examples:
  py setup_android_dev.py localnet --user jason
  py setup_android_dev.py localnet --user jason --skip-studio   # SDK/CLI tools only
  py setup_android_dev.py localnet --user jason --status
"""

from __future__ import annotations

import argparse
import getpass
import logging
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
LOG_DIR = SCRIPT_DIR / "logs"
LOCALNET_BIN_DIR = SCRIPT_DIR / "localnet-bin"

DEFAULT_INSTALL_ROOT = "/ai"
DEFAULT_API_LEVEL = "35"
DEFAULT_AVD_NAME = "pixel_api35"

log = logging.getLogger("setup_android_dev")


def setup_logging(log_file: Path, verbose: bool) -> None:
    log.setLevel(logging.DEBUG)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG if verbose else logging.INFO)
    console.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(console)

    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    log.addHandler(file_handler)
    log.debug("Logging to %s", log_file)


class RemoteError(RuntimeError):
    pass


def run_ssh(host: str, remote_cmd: str, input_data: str | None = None,
            timeout: int = 120, check: bool = True) -> subprocess.CompletedProcess:
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host, remote_cmd]
    log.debug("ssh %s <<< %r", host, remote_cmd[:200])
    result = subprocess.run(cmd, input=input_data, capture_output=True, text=True, timeout=timeout)
    if result.stdout:
        log.debug("stdout: %s", result.stdout.strip()[:4000])
    if result.stderr:
        log.debug("stderr: %s", result.stderr.strip()[:4000])
    if check and result.returncode != 0:
        raise RemoteError(f"Command failed on {host} (exit {result.returncode}): {remote_cmd}\n{result.stderr}")
    return result


def sudo_wrap(script: str, sudo_password: str | None) -> tuple[str, str | None]:
    """Wrap a remote script to run as root via `sudo -S` (works whether the
    target has NOPASSWD sudo or needs a real password)."""
    remote_cmd = f"sudo -S -p '' bash -c {shlex.quote(script)}"
    return remote_cmd, (sudo_password or "") + "\n"


def find_download_url(pattern_hint: str, page_grep: str) -> None:
    """Placeholder - actual URL discovery happens inline in install steps
    below via curl+grep of the live developer.android.com page, since Google
    does not publish a stable versioned alias for these downloads."""
    raise NotImplementedError


def check_ssh_reachable(host: str) -> None:
    log.info("Checking SSH connectivity to %s ...", host)
    run_ssh(host, "echo ok")
    log.info("SSH OK.")


def install_jdk(host: str, sudo_password: str | None) -> None:
    log.info("Installing OpenJDK 17 ...")
    cmd, stdin = sudo_wrap(
        "DEBIAN_FRONTEND=noninteractive apt-get update -qq && "
        "DEBIAN_FRONTEND=noninteractive apt-get install -y openjdk-17-jdk-headless",
        sudo_password,
    )
    run_ssh(host, cmd, input_data=stdin, timeout=180)


def download_and_extract_studio(host: str, install_root: str) -> None:
    log.info("Discovering current Android Studio Linux download URL ...")
    studio_dir = f"{install_root}/android-studio"
    script = (
        f'mkdir -p "{studio_dir}" && cd /tmp && '
        'curl -s "https://developer.android.com/studio" -o studio_page.html && '
        'URL=$(grep -oE "https://[^\\"]*android-studio[^\\"]*linux\\.tar\\.gz" studio_page.html | sort -u | head -1) && '
        'echo "Resolved URL: $URL" && '
        'test -n "$URL" && '
        'curl -L -o android-studio.tar.gz "$URL" && '
        f'tar xzf android-studio.tar.gz -C "{studio_dir}" --strip-components=1 && '
        'rm -f android-studio.tar.gz studio_page.html'
    )
    run_ssh(host, script, timeout=900)
    log.info("Android Studio installed to %s", studio_dir)


def download_and_extract_cmdline_tools(host: str, sdk_root: str) -> None:
    log.info("Discovering current SDK command-line tools download URL ...")
    script = (
        f'mkdir -p "{sdk_root}/cmdline-tools" && cd /tmp && '
        'curl -s "https://developer.android.com/studio" -o studio_page.html && '
        'URL=$(grep -oE "https://[^\\"]*commandlinetools-linux[^\\"]*\\.zip" studio_page.html | sort -u | head -1) && '
        'echo "Resolved URL: $URL" && '
        'test -n "$URL" && '
        'curl -L -o cmdline-tools.zip "$URL" && '
        'rm -rf /tmp/cmdline-tools-extract && mkdir -p /tmp/cmdline-tools-extract && '
        'unzip -q cmdline-tools.zip -d /tmp/cmdline-tools-extract && '
        f'rm -rf "{sdk_root}/cmdline-tools/latest" && '
        f'mv /tmp/cmdline-tools-extract/cmdline-tools "{sdk_root}/cmdline-tools/latest" && '
        'rm -rf /tmp/cmdline-tools-extract cmdline-tools.zip studio_page.html'
    )
    run_ssh(host, script, timeout=300)
    log.info("SDK command-line tools installed to %s/cmdline-tools/latest", sdk_root)


def accept_licenses_and_install_packages(host: str, sdk_root: str, api_level: str) -> None:
    log.info("Accepting SDK licenses ...")
    sdkmanager = f"{sdk_root}/cmdline-tools/latest/bin/sdkmanager"
    env = "export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64; "
    run_ssh(host, f'{env}yes | "{sdkmanager}" --sdk_root="{sdk_root}" --licenses', timeout=120, check=False)

    log.info("Installing platform-tools, platform %s, build-tools, emulator, system image ...", api_level)
    packages = " ".join(
        shlex.quote(p)
        for p in (
            "platform-tools",
            f"platforms;android-{api_level}",
            f"build-tools;{api_level}.0.0",
            "emulator",
            f"system-images;android-{api_level};google_apis;x86_64",
        )
    )
    run_ssh(host, f'{env}"{sdkmanager}" --sdk_root="{sdk_root}" {packages}', timeout=900)


def setup_env_vars(host: str, sdk_root: str) -> None:
    log.info("Setting Android env vars in ~/.bashrc ...")
    script = (
        'grep -q "ANDROID_SDK_ROOT" ~/.bashrc || cat >> ~/.bashrc << EOF\n\n'
        f'# Android SDK (installed under {sdk_root})\n'
        f'export ANDROID_SDK_ROOT={sdk_root}\n'
        f'export ANDROID_HOME={sdk_root}\n'
        f'export ANDROID_AVD_HOME={sdk_root}/avd\n'
        f'export PATH="$PATH:{sdk_root}/cmdline-tools/latest/bin:{sdk_root}/platform-tools:{sdk_root}/emulator"\n'
        'EOF\n'
        f'mkdir -p {sdk_root}/avd'
    )
    run_ssh(host, script)


def enable_kvm(host: str, user: str, sudo_password: str | None) -> bool:
    """Load the KVM module and add the user to the kvm group.

    Returns True if /dev/kvm ends up present, False if it looks like a
    BIOS-level virtualization disable that needs physical access to fix.
    """
    log.info("Checking CPU virtualization support and loading KVM module ...")
    flag_check = run_ssh(host, "grep -o -m1 -E 'svm|vmx' /proc/cpuinfo || true", check=False)
    if "svm" in flag_check.stdout:
        module = "kvm_amd"
    elif "vmx" in flag_check.stdout:
        module = "kvm_intel"
    else:
        log.warning("No svm/vmx CPU flag found - this CPU may not support virtualization at all.")
        return False

    cmd, stdin = sudo_wrap(f"modprobe {module}", sudo_password)
    result = run_ssh(host, cmd, input_data=stdin, check=False)
    if result.returncode != 0 or "not supported" in (result.stdout + result.stderr).lower():
        log.warning(
            "Could not load %s - virtualization is likely disabled in the BIOS "
            "(look for 'SVM Mode' on AMD boards, 'Intel VT-x' on Intel, under "
            "Advanced/CPU Configuration). This requires physical access and cannot "
            "be fixed remotely. Continuing setup - the emulator will just run slower "
            "(software rendering) until that's enabled.",
            module,
        )
        dev_check = run_ssh(host, "test -e /dev/kvm && echo yes || echo no", check=False)
        return "yes" in dev_check.stdout

    cmd, stdin = sudo_wrap(f"echo {module} > /etc/modules-load.d/kvm.conf", sudo_password)
    run_ssh(host, cmd, input_data=stdin, check=False)

    cmd, stdin = sudo_wrap(f"usermod -aG kvm {user}", sudo_password)
    run_ssh(host, cmd, input_data=stdin, check=False)
    log.info(
        "Added %s to the kvm group. This only takes effect on a FRESH login - "
        "if using xrdp with lingering enabled, existing sessions and the "
        "systemd --user manager may need to be killed for this to apply "
        "(see README.md in this folder for the full story on why).",
        user,
    )
    return True


def create_avd(host: str, sdk_root: str, api_level: str, avd_name: str) -> None:
    log.info("Creating AVD '%s' ...", avd_name)
    env = f"export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64; export ANDROID_SDK_ROOT={sdk_root}; export ANDROID_AVD_HOME={sdk_root}/avd; "
    avdmanager = f"{sdk_root}/cmdline-tools/latest/bin/avdmanager"
    check = run_ssh(host, f'{env}"{avdmanager}" list avd', check=False)
    if avd_name in check.stdout:
        log.info("AVD '%s' already exists, skipping creation.", avd_name)
        return
    script = (
        f'{env}echo no | "{avdmanager}" create avd --name {shlex.quote(avd_name)} '
        f'--package "system-images;android-{api_level};google_apis;x86_64" --device pixel_6'
    )
    run_ssh(host, script, check=False)  # avdmanager exits nonzero on a harmless devices.xml warning


def deploy_wrapper_scripts(host: str, install_root: str) -> None:
    log.info("Deploying android-gradle / android-adb / android-emulator to ~/bin ...")
    run_ssh(host, "mkdir -p ~/bin")
    for name in ("android-gradle", "android-adb", "android-emulator"):
        src = LOCALNET_BIN_DIR / name
        if not src.exists():
            log.warning("%s not found in %s, skipping (has it been moved?)", name, LOCALNET_BIN_DIR)
            continue
        subprocess.run(["scp", "-o", "BatchMode=yes", str(src), f"{host}:~/bin/{name}"], check=True)
        run_ssh(host, f"chmod +x ~/bin/{name}")
    log.info("Wrapper scripts deployed. If Open WebUI's local-bin-mcp server points at ~/bin, "
             "these are now callable as tools with no restart needed.")


def cmd_status(host: str, sdk_root: str) -> None:
    log.info("=== Android dev environment status on %s ===", host)
    checks = [
        ("Java", "java -version 2>&1 | head -1"),
        ("Android Studio", f"test -x {sdk_root}/../android-studio/bin/studio.sh && echo installed || echo missing"),
        ("SDK cmdline-tools", f"test -x {sdk_root}/cmdline-tools/latest/bin/sdkmanager && echo installed || echo missing"),
        ("adb", f"{sdk_root}/platform-tools/adb version 2>&1 | head -1"),
        ("/dev/kvm", "ls -la /dev/kvm 2>&1"),
        ("kvm group membership", "groups"),
        ("AVDs", f"{sdk_root}/cmdline-tools/latest/bin/avdmanager list avd 2>&1 | grep Name || echo none"),
        ("wrapper scripts", "ls ~/bin/android-* 2>&1"),
    ]
    for label, remote_cmd in checks:
        result = run_ssh(host, remote_cmd, check=False)
        value = (result.stdout or result.stderr).strip() or "(no output)"
        log.info("  %-24s %s", label + ":", value.splitlines()[0] if value else "")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="setup_android_dev.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("host", help="SSH alias or hostname/IP of the target Linux box")
    parser.add_argument("--user", required=True, help="Linux username on the target (for kvm group, wrapper deploy)")
    parser.add_argument("--install-root", default=DEFAULT_INSTALL_ROOT,
                         help=f"Base directory for Android Studio/SDK (default: {DEFAULT_INSTALL_ROOT})")
    parser.add_argument("--api-level", default=DEFAULT_API_LEVEL,
                         help=f"Android API level to install (default: {DEFAULT_API_LEVEL})")
    parser.add_argument("--avd-name", default=DEFAULT_AVD_NAME,
                         help=f"Name for the created AVD (default: {DEFAULT_AVD_NAME})")
    parser.add_argument("--skip-studio", action="store_true",
                         help="Skip the ~1.5GB Android Studio GUI download; SDK/CLI tools only")
    parser.add_argument("--skip-avd", action="store_true", help="Skip AVD creation")
    parser.add_argument("--ask-sudo-password", action="store_true",
                         help="Prompt for the remote sudo password interactively. Omit if the "
                         "target already has passwordless (NOPASSWD) sudo configured.")
    parser.add_argument("--status", action="store_true",
                         help="Only check the current state of the Android dev setup; make no changes")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose (debug) logging")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    setup_logging(LOG_DIR / f"setup_android_dev_{timestamp}.log", args.verbose)

    sdk_root = f"{args.install_root}/android-sdk"

    try:
        if args.status:
            check_ssh_reachable(args.host)
            cmd_status(args.host, sdk_root)
            return 0

        sudo_password = None
        if args.ask_sudo_password:
            sudo_password = getpass.getpass(f"sudo password for {args.user}@{args.host}: ")

        check_ssh_reachable(args.host)
        install_jdk(args.host, sudo_password)

        if not args.skip_studio:
            download_and_extract_studio(args.host, args.install_root)
        else:
            log.info("Skipping Android Studio GUI download (--skip-studio).")

        download_and_extract_cmdline_tools(args.host, sdk_root)
        accept_licenses_and_install_packages(args.host, sdk_root, args.api_level)
        setup_env_vars(args.host, sdk_root)

        kvm_ok = enable_kvm(args.host, args.user, sudo_password)
        if not kvm_ok:
            log.warning("KVM is not available - see the warning above. Emulator will still be "
                        "created but will run unaccelerated until that's resolved.")

        if not args.skip_avd:
            create_avd(args.host, sdk_root, args.api_level, args.avd_name)

        deploy_wrapper_scripts(args.host, args.install_root)

        log.info("Done. Run with --status to verify, or: ssh %s 'android-emulator start-gui'", args.host)
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
