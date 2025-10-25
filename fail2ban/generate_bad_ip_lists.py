#!/usr/bin/env python3
"""
Generate Fail2Ban-importable IP lists from web logs.

- Run directly, or import and call generate_ip_lists(...)
- Supports plain logs and rotated .gz logs
- --dry-run prints counts instead of writing files (default on Windows)
- --union adds union-all.txt; --only-union writes/prints just union-all.txt
- --all forces emitting every list (including union) even if empty (useful for automation)

Dry-run prints ONLY counts, never the IPs.
"""

import argparse
import gzip
import glob
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from typing import Iterable, List, Dict, Tuple

# --------- Defaults ----------
DEFAULT_OUTPUT_DIR = "./iplists_out"
DEFAULT_MIN_4XX = 15
DEFAULT_MIN_5XX = 7
DEFAULT_MIN_AUTH_FAIL = 7
DEFAULT_MIN_RATE = 120

# Nginx access (common/combined) regex
ACCESS_RE = re.compile(
    r'^\b(?P<ip>\d{1,3}(?:\.\d{1,3}){3})\b [^ ]+ [^ ]+ \[(?P<ts>[^\]]+)\] '
    r'"(?P<method>[A-Z]+) (?P<path>[^"]*) (?P<proto>[^"]+)" '
    r'(?P<status>\d{3}) (?P<size>\d+|-)'
)
IP_RE = re.compile(r'\b(?P<ip>\d{1,3}(?:\.\d{1,3}){3})\b')



def _open_log(path: str) -> Iterable[str]:
    """Open plain or gz log, yielding decoded lines (UTF-8 with replacement)."""
    if path.endswith(".gz"):
        with gzip.open(path, "rb") as fh:
            for bline in fh:
                yield bline.decode("utf-8", "replace")
    else:
        with open(path, "rb") as fh:
            for bline in fh:
                yield bline.decode("utf-8", "replace")


def _iter_existing_files(globs_list: List[str]) -> List[str]:
    """Expand a list of globs to a deduped, mtime-desc file list."""
    seen, files = set(), []
    for g in globs_list:
        for p in glob.glob(g):
            if os.path.isfile(p) and p not in seen:
                seen.add(p)
                files.append(p)
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return files


def parse_access_logs(paths: List[str]) -> Tuple[Counter, Counter, Dict[str, int]]:
    """Return fourxx, fivexx counters and total rate per IP."""
    fourxx, fivexx, rates = Counter(), Counter(), defaultdict(int)
    for p in paths:
        try:
            for line in _open_log(p):
                m = ACCESS_RE.match(line)
                if not m:
                    continue
                ip = m.group("ip")
                status = int(m.group("status"))
                rates[ip] += 1
                if 400 <= status <= 499:
                    fourxx[ip] += 1
                elif 500 <= status <= 599:
                    fivexx[ip] += 1
        except Exception as e:
            print(f"[WARN] Skipping {p}: {e}", file=sys.stderr)
    return fourxx, fivexx, dict(rates)


def parse_error_logs(paths: List[str]) -> Counter:
    """
    Heuristic for auth failures in error logs (format varies widely).
    Looks for common auth-related words and extracts the first IPv4.
    """
    auth = Counter()
    for p in paths:
        try:
            for line in _open_log(p):
                low = line.lower()
                if "auth" in low or "password" in low or "login" in low or "unauthorized" in low:
                    m = IP_RE.search(line)
                    if m:
                        auth[m.group("ip")] += 1
        except Exception as e:
            print(f"[WARN] Skipping {p}: {e}", file=sys.stderr)
    return auth


def _write_list_file(out_path: str, title: str, ips: List[str]) -> None:
    """Write a .txt list (real write; used when not dry-run)."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n# Generated: {now}\n# One IP per line. Lines starting with # are comments.\n\n")
        for ip in sorted(set(ips)):
            f.write(ip + "\n")
    print(f"Wrote {out_path} with {len(set(ips))} IPs")


def _preview_counts(out_path: str, title: str, ips: List[str]) -> None:
    """Dry-run: print counts only (never the IPs)."""
    count = len(set(ips))
    print(f"[DRY-RUN] {title} → {out_path}  (IPs: {count})")


def generate_ip_lists(
    output_dir: str = DEFAULT_OUTPUT_DIR,
    access_globs: List[str] = None,
    error_globs: List[str] = None,
    min_4xx: int = DEFAULT_MIN_4XX,
    min_5xx: int = DEFAULT_MIN_5XX,
    min_auth: int = DEFAULT_MIN_AUTH_FAIL,
    min_rate: int = DEFAULT_MIN_RATE,
    dry_run: bool = False,
    union: bool = False,
    only_union: bool = False,
    all_lists: bool = False,
) -> Dict[str, str]:
    """
    Main callable. Returns a dict of label -> output path (planned path in dry-run).
    - Thresholds always apply; --all just forces emitting files even if empty.
    """
    access_files = _iter_existing_files(access_globs or [])
    error_files  = _iter_existing_files(error_globs or [])

    if not access_files and not error_files:
        print("[INFO] No logs found with the provided globs.", file=sys.stderr)

    fourxx, fivexx, rates = parse_access_logs(access_files)
    auth = parse_error_logs(error_files)

    ips_4xx  = [ip for ip, c in fourxx.items() if c >= min_4xx]
    ips_5xx  = [ip for ip, c in fivexx.items() if c >= min_5xx]
    ips_auth = [ip for ip, c in auth.items() if c >= min_auth]
    ips_rate = [ip for ip, c in rates.items() if c >= min_rate]

    outputs: Dict[str, str] = {}
    def emit(name: str, title: str, ips: List[str]):
        path = os.path.join(output_dir, name)
        if dry_run:
            _preview_counts(path, title, ips)
        else:
            _write_list_file(path, title, ips)
        outputs[name] = path

    # Individual lists (unless only_union)
    if not only_union:
        if all_lists or ips_4xx:
            emit("4xx-abuse.txt", "IPs with many 4xx", ips_4xx)
        if all_lists or ips_5xx:
            emit("5xx-abuse.txt", "IPs with many 5xx", ips_5xx)
        if all_lists or ips_auth:
            emit("auth-bruteforce.txt", "IPs with auth failures", ips_auth)
        if all_lists or ips_rate:
            emit("high-rate.txt", "IPs with high request rates", ips_rate)

    # Union list
    if union or only_union or all_lists:
        union_set = set(ips_4xx) | set(ips_5xx) | set(ips_auth) | set(ips_rate)
        if union_set or all_lists:
            emit("union-all.txt", "Union of all detected abusive IPs", list(union_set))
        else:
            # Only print this info message when not forcing via --all
            if dry_run:
                print("[INFO] No IPs matched any criteria, skipping union list.")
            else:
                print("[INFO] No IPs matched any criteria, so union-all.txt was not created.")

    return outputs


def main():
    ap = argparse.ArgumentParser(description="Create IP list files from logs (Fail2Ban importable).")
    ap.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Directory to write .txt files")
    ap.add_argument("--access-glob", nargs="*", default=[],
                    help="Space-separated globs for access logs (supports .gz). Example: /home/*/logs/*.access.log")
    ap.add_argument("--error-glob", nargs="*", default=[],
                    help="Space-separated globs for error logs (supports .gz)")
    ap.add_argument("--min-4xx", type=int, default=DEFAULT_MIN_4XX, help="Min 4xx count to include an IP")
    ap.add_argument("--min-5xx", type=int, default=DEFAULT_MIN_5XX, help="Min 5xx count to include an IP")
    ap.add_argument("--min-auth", type=int, default=DEFAULT_MIN_AUTH_FAIL, help="Min auth failures (error logs)")
    ap.add_argument("--min-rate", type=int, default=DEFAULT_MIN_RATE, help="Min total requests to include an IP")
    ap.add_argument("--dry-run", action="store_true", help="Print counts only; do not write files")
    ap.add_argument("--union", action="store_true", help="Also produce a combined union-all.txt")
    ap.add_argument("--only-union", action="store_true", help="Produce only union-all.txt")
    ap.add_argument("--all", dest="all_lists", action="store_true",
                    help="Emit every list (including union) even if empty (good for automation)")
    args = ap.parse_args()

    # Auto-enable dry-run on Windows for safety
    if os.name == "nt" and not args.dry_run:
        args.dry_run = True
        print("[INFO] Windows detected → forcing --dry-run (no files will be written).")

    generate_ip_lists(
        output_dir=args.output_dir,
        access_globs=args.access_glob,
        error_globs=args.error_glob,
        min_4xx=args.min_4xx,
        min_5xx=args.min_5xx,
        min_auth=args.min_auth,
        min_rate=args.min_rate,
        dry_run=args.dry_run,
        union=args.union,
        only_union=args.only_union,
        all_lists=args.all_lists,
    )


if __name__ == "__main__":
    main()
