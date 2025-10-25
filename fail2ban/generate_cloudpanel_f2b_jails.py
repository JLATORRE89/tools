#!/usr/bin/env python3
"""
CloudPanel Fail2Ban jail generator with per-jail maxretry.
- Linux: generates real jail/filter files (unless --dry-run).
- Windows: always writes preview files locally (never touches /etc/*).
- Default: 7 attempts across all jails, can override per jail.
"""

import argparse
import datetime
import glob
import os
import re
import shutil
import sys
import tempfile
from typing import List, Set, Tuple

# Linux target paths
DEFAULT_OUT = "/etc/fail2ban/jail.d/cloudpanel-nginx.local"
DEFAULT_FILTER_4XX = "/etc/fail2ban/filter.d/nginx-4xx-local.conf"
DEFAULT_FILTER_5XX = "/etc/fail2ban/filter.d/nginx-5xx-local.conf"

# Windows preview filenames
WIN_PREVIEW_JAIL   = "cloudpanel-nginx.local.preview"
WIN_PREVIEW_4XX    = "nginx-4xx-local.conf.preview"
WIN_PREVIEW_5XX    = "nginx-5xx-local.conf.preview"

DEFAULT_IGNORE_IPS = ["127.0.0.1/8", "::1", "69.153.26.6", "72.14.201.232", "107.172.27.113"]

# Default thresholds
DEFAULT_MAXRETRY = 7
DEFAULT_FINDTIME = "600"   # 10 minutes
DEFAULT_BANTIME  = "3600"  # 1 hour
RECIDIVE_BANTIME = "86400" # 24 hours
RECIDIVE_FINDTIME= "86400"


def generate_cloudpanel_f2b_jails(
    out_path: str = DEFAULT_OUT,
    ignore_ips: List[str] = None,
    bantime: str = DEFAULT_BANTIME,
    findtime: str = DEFAULT_FINDTIME,
    banaction: str = "iptables-multiport",
    backend: str = "auto",
    # per-jail maxretry
    maxretry_auth: int = DEFAULT_MAXRETRY,
    maxretry_badbots: int = DEFAULT_MAXRETRY,
    maxretry_botsearch: int = DEFAULT_MAXRETRY,
    maxretry_4xx: int = DEFAULT_MAXRETRY,
    maxretry_5xx: int = DEFAULT_MAXRETRY,
    maxretry_recidive: int = DEFAULT_MAXRETRY,
    include_4xx: bool = True,
    include_5xx: bool = True,
    dry_run: bool = False,
    filter4xx_path: str = DEFAULT_FILTER_4XX,
    filter5xx_path: str = DEFAULT_FILTER_5XX,
    preview_dir: str = ".",
    force_write: bool = False,
):
    """Generate Fail2Ban jails for CloudPanel-managed Nginx logs."""

    is_windows = os.name == "nt"
    if is_windows:
        dry_run = True
        preview_dir_abs = os.path.abspath(preview_dir or ".")
        os.makedirs(preview_dir_abs, exist_ok=True)
        out_path      = os.path.join(preview_dir_abs, WIN_PREVIEW_JAIL)
        filter4xx_path= os.path.join(preview_dir_abs, WIN_PREVIEW_4XX)
        filter5xx_path= os.path.join(preview_dir_abs, WIN_PREVIEW_5XX)
        if not force_write:
            force_write = True
        print("[INFO] Windows detected → preview mode enabled; writing local previews.")
        print(f"       Jail preview  : {out_path}")
        if include_4xx:
            print(f"       4xx filter    : {filter4xx_path}")
        if include_5xx:
            print(f"       5xx filter    : {filter5xx_path}")

    def is_real_shell_unix(shell: str) -> bool:
        return not re.search(r"(nologin|false)\\s*$", shell or "")

    def active_homes() -> List[str]:
        homes: List[str] = []
        if os.name == "posix":
            try:
                import pwd
            except ModuleNotFoundError:
                homes = [d for d in glob.glob("/home/*") if os.path.isdir(d)]
            else:
                for p in pwd.getpwall():
                    if p.pw_dir.startswith("/home/") and is_real_shell_unix(p.pw_shell):
                        homes.append(p.pw_dir)
        else:  # Windows
            drive = os.path.splitdrive(os.path.expanduser("~"))[0] or "C:"
            users_base = os.path.join(drive, "Users")
            if os.path.isdir(users_base):
                for name in os.listdir(users_base):
                    home = os.path.join(users_base, name)
                    if os.path.isdir(home):
                        homes.append(home)
        return homes

    def any_matches(pattern: str) -> bool:
        return len(glob.glob(pattern)) > 0

    def collect_nginx_paths_for_home(home: str) -> Tuple[Set[str], Set[str]]:
        errors: Set[str] = set()
        access: Set[str] = set()
        candidates = [
            os.path.join(home, "logs", "nginx"),
            os.path.join(home, "logs"),
            os.path.join(home, "htdocs"),
        ]
        flat_patterns = [
            ("error", ["*.error.log", "*.error.log.*", "*.error.log*.gz"]),
            ("access", ["*.access.log", "*.access.log.*", "*.access.log*.gz"]),
        ]
        nginx_patterns = [
            ("error", ["nginx/*.error.log", "nginx/*.error.log.*", "nginx/*.error.log*.gz"]),
            ("access", ["nginx/*.access.log", "nginx/*.access.log.*", "nginx/*.access.log*.gz"]),
        ]
        for c in candidates:
            if not os.path.isdir(c):
                continue
            if os.path.basename(c) == "htdocs":
                for d in glob.glob(os.path.join(c, "*")):
                    logs_dir = os.path.join(d, "logs")
                    if not os.path.isdir(logs_dir):
                        continue
                    for kind, pats in flat_patterns + nginx_patterns:
                        for pat in pats:
                            pat_path = os.path.join(logs_dir, pat)
                            if any_matches(pat_path):
                                (errors if kind == "error" else access).add(pat_path)
            else:
                for kind, pats in flat_patterns + nginx_patterns:
                    for pat in pats:
                        pat_path = os.path.join(c, pat)
                        if any_matches(pat_path):
                            (errors if kind == "error" else access).add(pat_path)
        return errors, access

    def write_filter(content: str, path_out: str, label: str):
        if dry_run:
            with open(path_out, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[PREVIEW] Wrote {label} filter preview: {path_out}")
            return
        os.makedirs(os.path.dirname(path_out), exist_ok=True)
        with open(path_out, "w", encoding="utf-8") as f:
            f.write(content)
        os.chmod(path_out, 0o644)
        print(f"Wrote {label} filter: {path_out} (absolute: {os.path.abspath(path_out)})")

    FILTER_4XX_CONTENT = """# Fail2Ban filter for repeated 4xx in Nginx access logs
[Definition]
failregex = ^<HOST> [^ ]+ [^ ]+ \\[[^\\]]+\\] "(?:[A-Z]+) [^"]*" 4\\d{2} [0-9-]+
ignoreregex =
"""
    FILTER_5XX_CONTENT = """# Fail2Ban filter for repeated 5xx in Nginx access logs
[Definition]
failregex = ^<HOST> [^ ]+ [^ ]+ \\[[^\\]]+\\] "(?:[A-Z]+) [^"]*" 5\\d{2} [0-9-]+
ignoreregex =
"""

    def build_jail_content(error_paths: List[str], access_paths: List[str], include_examples: bool) -> str:
        ignore = ignore_ips or DEFAULT_IGNORE_IPS
        header = [
            f"# Auto-generated on {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
            "",
            "[DEFAULT]",
            f"ignoreip = {' '.join(ignore)}",
            f"bantime  = {bantime}",
            f"findtime = {findtime}",
            f"backend  = {backend}",
            f"banaction = {banaction}",
            "",
        ]

        blocks: List[str] = []

        if error_paths or include_examples:
            blocks += [
                "[nginx-cloudpanel-auth]",
                "enabled = true",
                "filter  = nginx-http-auth",
                "port    = http,https",
                f"maxretry = {maxretry_auth}",
            ]
        if error_paths:
            blocks.append("logpath =" + " \\\n  " + " \\\n  ".join(sorted(error_paths)))
        else:
            blocks += ["# logpath = /home/*/logs/*.error.log", "# ..."]
        blocks.append("")

        if access_paths or include_examples:
            blocks += [
                "[nginx-cloudpanel-badbots]",
                "enabled = true",
                "filter  = nginx-badbots",
                "port    = http,https",
                f"maxretry = {maxretry_badbots}",
            ]
        if access_paths:
            blocks.append("logpath =" + " \\\n  " + " \\\n  ".join(sorted(access_paths)))
        else:
            blocks += ["# logpath = /home/*/logs/*.access.log", "# ..."]
        blocks.append("")

        if access_paths or include_examples:
            blocks += [
                "[nginx-cloudpanel-botsearch]",
                "enabled = true",
                "filter  = nginx-botsearch",
                "port    = http,https",
                f"maxretry = {maxretry_botsearch}",
            ]
        if access_paths:
            blocks.append("logpath =" + " \\\n  " + " \\\n  ".join(sorted(access_paths)))
        else:
            blocks += ["# logpath = /home/*/logs/*.access.log", "# ..."]
        blocks.append("")

        if include_4xx and (access_paths or include_examples):
            blocks += [
                "[nginx-cloudpanel-4xx]",
                "enabled = true",
                "filter  = nginx-4xx-local",
                "port    = http,https",
                f"maxretry = {maxretry_4xx}",
                f"findtime = {findtime}",
                f"bantime  = {bantime}",
            ]
            blocks += ["logpath =" + " \\\n  " + " \\\n  ".join(sorted(access_paths))] if access_paths else ["# logpath = /home/*/logs/*.access.log"]
            blocks.append("")

        if include_5xx and (access_paths or include_examples):
            blocks += [
                "[nginx-cloudpanel-5xx]",
                "enabled = true",
                "filter  = nginx-5xx-local",
                "port    = http,https",
                f"maxretry = {maxretry_5xx}",
                f"findtime = {findtime}",
                f"bantime  = {bantime}",
            ]
            blocks += ["logpath =" + " \\\n  " + " \\\n  ".join(sorted(access_paths))] if access_paths else ["# logpath = /home/*/logs/*.access.log"]
            blocks.append("")

        blocks += [
            "[recidive]",
            "enabled  = true",
            "logpath  = /var/log/fail2ban.log",
            f"banaction = {banaction}",
            f"bantime  = {RECIDIVE_BANTIME}",
            f"findtime = {RECIDIVE_FINDTIME}",
            f"maxretry = {maxretry_recidive}",
            "",
        ]

        return "\n".join(header + blocks).rstrip() + "\n"

    homes = active_homes()
    error_paths, access_paths = set(), set()
    for home in homes:
        e, a = collect_nginx_paths_for_home(home)
        error_paths |= e
        access_paths |= a

    no_logs_found = not error_paths and not access_paths
    include_examples = force_write and no_logs_found
    content = build_jail_content(sorted(error_paths), sorted(access_paths), include_examples)

    if include_4xx and (access_paths or force_write):
        write_filter(FILTER_4XX_CONTENT, filter4xx_path, "4xx")
    if include_5xx and (access_paths or force_write):
        write_filter(FILTER_5XX_CONTENT, filter5xx_path, "5xx")

    if dry_run:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[PREVIEW] Wrote jail preview: {out_path}")
        print(content)
    else:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        shutil.move(tmp_path, out_path)
        os.chmod(out_path, 0o644)
        print(f"Wrote jail file: {out_path} (absolute: {os.path.abspath(out_path)})")
        print(content)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generate Fail2Ban jails with per-jail maxretry.")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--ignoreip", nargs="*", default=DEFAULT_IGNORE_IPS)
    ap.add_argument("--bantime", default=DEFAULT_BANTIME)
    ap.add_argument("--findtime", default=DEFAULT_FINDTIME)
    ap.add_argument("--banaction", default="iptables-multiport")
    ap.add_argument("--backend", default="auto")
    ap.add_argument("--maxretry-auth", type=int, default=DEFAULT_MAXRETRY)
    ap.add_argument("--maxretry-badbots", type=int, default=DEFAULT_MAXRETRY)
    ap.add_argument("--maxretry-botsearch", type=int, default=DEFAULT_MAXRETRY)
    ap.add_argument("--maxretry-4xx", type=int, default=DEFAULT_MAXRETRY)
    ap.add_argument("--maxretry-5xx", type=int, default=DEFAULT_MAXRETRY)
    ap.add_argument("--maxretry-recidive", type=int, default=DEFAULT_MAXRETRY)
    ap.add_argument("--no-4xx", action="store_true")
    ap.add_argument("--no-5xx", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--preview-dir", default=".")
    ap.add_argument("--force-write", action="store_true")
    args = ap.parse_args()

    generate_cloudpanel_f2b_jails(
        out_path=args.out,
        ignore_ips=args.ignoreip,
        bantime=args.bantime,
        findtime=args.findtime,
        banaction=args.banaction,
        backend=args.backend,
        maxretry_auth=args.maxretry_auth,
        maxretry_badbots=args.maxretry_badbots,
        maxretry_botsearch=args.maxretry_botsearch,
        maxretry_4xx=args.maxretry_4xx,
        maxretry_5xx=args.maxretry_5xx,
        maxretry_recidive=args.maxretry_recidive,
        include_4xx=not args.no_4xx,
        include_5xx=not args.no_5xx,
        dry_run=args.dry_run,
        preview_dir=args.preview_dir,
        force_write=args.force_write,
    )
