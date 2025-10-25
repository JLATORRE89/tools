#!/usr/bin/env python3
"""
Outlook cleanup via Microsoft Graph:
- Delete unread/all messages (optionally by sender)
- Date filters (older/newer than N days)
- Preserve emails with attachments
- CSV report of matches
- Confirmation prompt
- Parallel $batch deletes with sub-request retries + adaptive throttling
- Progress output
- Graceful Ctrl+C
- Cancelable authentication (timeout-aware)

Example (conservative for throttling):
  python outlook_batch_delete.py --unread --yes ^
    --client-id YOUR_CLIENT_ID --tenant consumers ^
    --hard-delete --max-workers 1 --batch-size 10 --page-top 100 --progress ^
    --adaptive-throttle --min-workers 1 --min-batch-size 5 ^
    --max-retry-waves 8 --retry-base-wait 5 --submit-sleep-ms 75
"""
import os, sys, time, argparse, requests, msal, signal, threading, csv, random
from typing import List, Tuple, Dict, Optional, Any, Callable
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from math import ceil

GRAPH = "https://graph.microsoft.com/v1.0"
SCOPES = ["Mail.ReadWrite"]

PAGE_TOP_DEFAULT = 100          # Graph max = 100
BATCH_MAX_DEFAULT = 20          # Graph per-$batch subrequest cap
DEFAULT_WORKERS = int(os.getenv("OUTLOOK_MAX_WORKERS", "6"))
TIMEOUT_DEFAULT = int(os.getenv("OUTLOOK_TIMEOUT", "30"))
AUTH_TIMEOUT_DEFAULT = int(os.getenv("OUTLOOK_AUTH_TIMEOUT", "600"))  # 10 min

# Global cancel flag set by Ctrl+C
CANCEL = threading.Event()

# ---------------- SIGINT handler ----------------
def _sigint_handler(signum, frame):
    if not CANCEL.is_set():
        print("\n^C received — attempting graceful shutdown…", file=sys.stderr)
        CANCEL.set()
signal.signal(signal.SIGINT, _sigint_handler)

# ------------- run_with_cancel: make blocking auth cancelable -------------
class _ResultBox:
    def __init__(self):
        self.value = None
        self.err = None

def run_with_cancel(fn: Callable[[], Any], timeout_s: int, check_interval: float = 0.2) -> Any:
    """
    Runs fn() in a background daemon thread so we can honor CANCEL/timeout.
    """
    box = _ResultBox()
    def _runner():
        try:
            box.value = fn()
        except BaseException as e:
            box.err = e
    t = threading.Thread(target=_runner, daemon=True)
    t.start()
    start = time.time()
    while t.is_alive():
        if CANCEL.is_set():
            raise KeyboardInterrupt("Canceled")
        if timeout_s is not None and (time.time() - start) > timeout_s:
            raise TimeoutError(f"Authentication timed out after {timeout_s} seconds.")
        time.sleep(check_interval)
    if box.err:
        raise box.err
    return box.value

# ------------- HTTP helpers (timeout + retries + verbose + cancel) -------------
def http_get(url, headers=None, params=None, timeout=TIMEOUT_DEFAULT, retries=5, verbose=False, cancel_event: Optional[threading.Event]=None):
    attempt = 0
    while True:
        if cancel_event and cancel_event.is_set(): raise KeyboardInterrupt
        attempt += 1
        if verbose:
            qs = f" params={params}" if params else ""
            print(f"[HTTP GET] {url}{qs}")
        try:
            r = requests.get(url, headers=headers, params=params, timeout=timeout)
        except requests.exceptions.Timeout:
            if attempt <= retries:
                wait = min(2 ** attempt, 15)
                print(f"[timeout] GET retry in {wait}s ({attempt}/{retries})"); time.sleep(wait); continue
            raise
        if r.status_code in (429, 500, 502, 503, 504):
            if attempt <= retries:
                ra = int(r.headers.get("Retry-After", "0") or 0)
                wait = max(ra, min(2 ** attempt, 15))
                print(f"[{r.status_code}] GET retry in {wait}s ({attempt}/{retries})"); time.sleep(wait); continue
        if r.status_code == 400:
            try:
                print(f"[HTTP 400] {r.text}", file=sys.stderr)
            except Exception:
                pass
        r.raise_for_status()
        return r

def http_post(url, headers=None, json=None, timeout=TIMEOUT_DEFAULT, retries=5, verbose=False, cancel_event: Optional[threading.Event]=None):
    attempt = 0
    while True:
        if cancel_event and cancel_event.is_set(): raise KeyboardInterrupt
        attempt += 1
        if verbose:
            ops = len(json.get('requests', [])) if isinstance(json, dict) else 0
            print(f"[HTTP POST] {url} ({ops} ops)")
        try:
            r = requests.post(url, headers=headers, json=json, timeout=timeout)
        except requests.exceptions.Timeout:
            if attempt <= retries:
                wait = min(2 ** attempt, 15)
                print(f"[timeout] POST retry in {wait}s ({attempt}/{retries})"); time.sleep(wait); continue
            raise
        if r.status_code in (429, 500, 502, 503, 504):
            if attempt <= retries:
                ra = int(r.headers.get("Retry-After", "0") or 0)
                wait = max(ra, min(2 ** attempt, 15))
                print(f"[{r.status_code}] POST retry in {wait}s ({attempt}/{retries})"); time.sleep(wait); continue
        r.raise_for_status()
        return r

# --------------------------- Auth (cancelable) ---------------------------
def get_token(client_id: str, tenant: str, use_device_code: bool, auth_timeout_s: int) -> dict:
    authority = f"https://login.microsoftonline.com/{tenant}"
    app = msal.PublicClientApplication(client_id, authority=authority)
    accounts = app.get_accounts()
    if accounts:
        try:
            result = run_with_cancel(lambda: app.acquire_token_silent(SCOPES, account=accounts[0]), timeout_s=auth_timeout_s)
            if result and "access_token" in result:
                return result
        except Exception:
            pass
    if use_device_code:
        flow = app.initiate_device_flow(scopes=SCOPES)
        if not flow or "user_code" not in flow:
            raise RuntimeError(f"Failed to start device code flow. Details: {flow}")
        print(flow["message"], flush=True)
        result = run_with_cancel(lambda: app.acquire_token_by_device_flow(flow), timeout_s=auth_timeout_s)
    else:
        result = run_with_cancel(lambda: app.acquire_token_interactive(scopes=SCOPES), timeout_s=auth_timeout_s)
    if "access_token" not in result:
        raise RuntimeError(f"Auth failed: {result}")
    return result

# ------------------------ Graph helpers ------------------------
def resolve_folder_id(access_token: str, folder_name: str, timeout: int, verbose: bool) -> str:
    """
    Returns a folder identifier acceptable by /me/mailFolders/{id or well-known}/messages.
    Well-known names like 'inbox' are allowed directly.
    """
    well_known = {"inbox", "junkemail", "deleteditems", "archive", "drafts", "sentitems"}
    if folder_name.lower() in well_known:
        return folder_name  # use well-known
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{GRAPH}/me/mailFolders"
    params = {"$top": "100", "$select": "id,displayName"}
    while True:
        r = http_get(url, headers=headers, params=params, timeout=timeout, verbose=verbose, cancel_event=CANCEL)
        data = r.json()
        for f in data.get("value", []):
            if f.get("displayName", "").lower() == folder_name.lower():
                return f["id"]
        next_link = data.get("@odata.nextLink")
        if not next_link: break
        url, params = next_link, None
    raise RuntimeError(f"Mail folder '{folder_name}' not found.")

def odata_datetime(dt: datetime) -> str:
    """Return an OData DateTimeOffset literal like 2024-09-02T00:00:00Z (unquoted)."""
    return dt.astimezone(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")

def build_filter(sender: Optional[str], unread_only: bool,
                 older_than_days: Optional[int], newer_than_days: Optional[int],
                 preserve_attachments: bool) -> str:
    parts = []
    if sender:
        parts.append(f"from/emailAddress/address eq '{sender}'")  # strings quoted
    if unread_only:
        parts.append("isRead eq false")
    if preserve_attachments:
        parts.append("hasAttachments eq false")
    now = datetime.now(timezone.utc)
    if older_than_days is not None:
        cutoff = now - timedelta(days=older_than_days)
        parts.append(f"receivedDateTime lt {odata_datetime(cutoff)}")  # NO quotes
    if newer_than_days is not None:
        cutoff = now - timedelta(days=newer_than_days)
        parts.append(f"receivedDateTime ge {odata_datetime(cutoff)}")  # NO quotes
    return " and ".join(parts) if parts else ""

def list_messages(access_token: str, folder_id: str, sender: Optional[str],
                  unread_only: bool, older_than_days: Optional[int], newer_than_days: Optional[int],
                  timeout: int, verbose: bool, progress: bool, label: str,
                  page_top: int, want_report: bool, preserve_attachments: bool
                  ) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Returns (ids, rows). If want_report=True, rows contain fields for CSV.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{GRAPH}/me/mailFolders/{folder_id}/messages"
    flt = build_filter(sender, unread_only, older_than_days, newer_than_days, preserve_attachments)

    if want_report:
        params = {"$select": "id,subject,from,receivedDateTime,hasAttachments", "$top": str(page_top)}
    else:
        params = {"$select": "id", "$top": str(page_top)}
    if flt: params["$filter"] = flt

    ids: List[str] = []
    rows: List[Dict[str, Any]] = []
    page = 0; start = time.time()

    try:
        while True:
            if CANCEL.is_set(): break
            page += 1
            r = http_get(url, headers=headers, params=params, timeout=timeout, verbose=verbose, cancel_event=CANCEL)
            data = r.json()

            vals = data.get("value", [])
            if want_report:
                for m in vals:
                    mid = m.get("id")
                    ids.append(mid)
                    frm = (m.get("from") or {}).get("emailAddress") or {}
                    rows.append({
                        "id": mid,
                        "from": frm.get("address"),
                        "subject": m.get("subject"),
                        "receivedDateTime": m.get("receivedDateTime"),
                        "hasAttachments": m.get("hasAttachments"),
                    })
            else:
                ids.extend([m["id"] for m in vals if "id" in m])

            if progress:
                elapsed = int(time.time() - start)
                print(f"[{label}] page {page}: +{len(vals)} (total {len(ids)}), elapsed {elapsed}s")

            next_link = data.get("@odata.nextLink")
            if not next_link: break
            url, params = next_link, None
    except KeyboardInterrupt:
        pass

    return ids, rows

def chunk(lst, n):
    for i in range(0, len(lst), n): yield lst[i:i+n]

# ------------------------ $batch helpers w/ subrequest retry ------------------------
def build_batch_body(ids: List[str], hard_delete: bool) -> dict:
    if hard_delete:
        return {"requests": [
            {"id": str(i), "method": "POST", "url": f"/me/messages/{mid}/permanentDelete"}
            for i, mid in enumerate(ids, start=1)
        ]}
    else:
        return {"requests": [
            {"id": str(i), "method": "DELETE", "url": f"/me/messages/{mid}"}
            for i, mid in enumerate(ids, start=1)
        ]}

def http_batch(access_token: str, ids: List[str], timeout: int, verbose: bool, hard_delete: bool) -> Tuple[int, List[str], Optional[int]]:
    """
    Returns (ok_count, retry_ids, retry_after_seconds_from_http_response)
    retry_ids are items that had sub-request 429/5xx inside the batch.
    """
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    body = build_batch_body(ids, hard_delete)
    r = http_post(f"{GRAPH}/$batch", headers=headers, json=body, timeout=timeout, verbose=verbose, cancel_event=CANCEL)
    data = r.json()
    ok = 0
    retry_ids: List[str] = []
    # server hint on outer response if present
    try:
        retry_after_http = int(r.headers.get("Retry-After", "0") or 0) or None
    except Exception:
        retry_after_http = None

    # Map subresponses to the original ids by order
    for idx, res in enumerate(data.get("responses", []), start=1):
        status = res.get("status")
        if status in (200, 204):
            ok += 1
        elif status in (429, 500, 502, 503, 504):
            if idx-1 < len(ids):
                retry_ids.append(ids[idx-1])
        else:
            print(f"[WARN] Delete failed: id={res.get('id')} status={status} body={res.get('body')}", file=sys.stderr)
    return ok, retry_ids, retry_after_http

def parallel_batch_delete(access_token: str, message_ids: List[str], batch_size: int,
                          max_workers: int, timeout: int, verbose: bool, progress: bool,
                          hard_delete: bool, max_retry_waves: int, base_sleep: int,
                          adaptive: bool, min_workers: int, min_batch_size: int,
                          submit_sleep_ms: int) -> int:
    """
    Sends batches in waves. Retries sub-request 429/5xx with exponential backoff and optional adaptive throttling.
    """
    if not message_ids:
        return 0

    total_deleted = 0
    pending: List[str] = list(message_ids)

    cur_workers = max(1, max_workers)
    cur_batch_size = max(1, min(batch_size, BATCH_MAX_DEFAULT))

    for wave in range(0, max_retry_waves + 1):
        if CANCEL.is_set() or not pending:
            break

        start = time.time()
        deleted_this_wave = 0
        retry_pool: List[str] = []
        batches = [pending[i:i+cur_batch_size] for i in range(0, len(pending), cur_batch_size)]

        with ThreadPoolExecutor(max_workers=cur_workers) as ex:
            futures = []
            for i, ids in enumerate(batches, start=1):
                if CANCEL.is_set(): break
                futures.append(ex.submit(http_batch, access_token, ids, timeout, verbose, hard_delete))
                if submit_sleep_ms > 0:
                    time.sleep(submit_sleep_ms / 1000.0)

            done = 0
            for fut in as_completed(futures):
                if CANCEL.is_set():
                    for f in futures: f.cancel()
                    ex.shutdown(wait=False, cancel_futures=True)
                    break
                ok, retry_ids, retry_after_http = fut.result()
                deleted_this_wave += ok
                retry_pool.extend(retry_ids)
                done += 1
                if progress and (done % 5 == 0 or done == len(futures)):
                    elapsed = int(time.time() - start)
                    print(f"[delete] wave {wave} batches {done}/{len(futures)} • ok+={deleted_this_wave} • retry+={len(retry_pool)} • elapsed {elapsed}s")

        total_deleted += deleted_this_wave
        pending = retry_pool

        if not pending or CANCEL.is_set():
            break

        # Backoff for next wave
        retry_ratio = len(retry_pool) / max(1, (len(batches) * cur_batch_size))
        sleep_s = base_sleep * (2 ** min(wave, 6)) + random.uniform(0, 1.5)

        # Adaptive throttling: reduce workers/batch size when retry rate is high
        if adaptive and retry_ratio >= 0.15:
            new_workers = max(min_workers, ceil(cur_workers / 2))
            new_batch = max(min_batch_size, ceil(cur_batch_size / 2))
            if new_workers < cur_workers or new_batch < cur_batch_size:
                print(f"[throttle] high retry rate {retry_ratio:.0%} → reduce workers {cur_workers}->{new_workers}, batch {cur_batch_size}->{new_batch}")
            cur_workers, cur_batch_size = new_workers, new_batch
            sleep_s += 5  # extra pause when we reduce concurrency

        print(f"[throttle] retrying {len(pending)} item(s) in {sleep_s:.1f}s…")
        # Respect CANCEL during sleep
        for _ in range(int(sleep_s * 10)):
            if CANCEL.is_set(): break
            time.sleep(0.1)

    if pending:
        print(f"[WARN] Gave up on {len(pending)} item(s) after retries (still throttled).")
    return total_deleted

# ------------------------ CSV / misc helpers ------------------------
def load_sender_list(path: str) -> List[str]:
    senders = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#") or s.startswith(";"): continue
            senders.append(s)
    return senders

def write_csv(path: str, rows: List[Dict[str, Any]], limit: Optional[int]) -> Tuple[int, Optional[str]]:
    if not rows:
        return 0, None
    written = 0
    truncated_note = None
    with open(path, "w", newline="", encoding="utf-8") as fp:
        w = csv.DictWriter(fp, fieldnames=["id","from","subject","receivedDateTime","hasAttachments"])
        w.writeheader()
        for r in rows:
            if limit is not None and written >= limit:
                truncated_note = f"(truncated to first {limit} rows)"
                break
            w.writerow(r)
            written += 1
    return written, truncated_note

def auth_tester(token_result: dict, timeout: int, verbose: bool):
    access_token = token_result["access_token"]
    scopes = token_result.get("scope"); print("Scopes granted:", scopes)
    h = {"Authorization": f"Bearer {access_token}"}
    r = http_get(f"{GRAPH}/me/mailFolders?$select=id,displayName,totalItemCount&$top=5",
                 headers=h, timeout=timeout, verbose=verbose, cancel_event=CANCEL)
    for f in r.json().get("value", []):
        print(f" - {f.get('displayName')} (items: {f.get('totalItemCount')})")

# ------------------------------ CLI ------------------------------
def main():
    p = argparse.ArgumentParser(description="Outlook cleanup (Microsoft Graph) with CSV report, confirmation, progress, cancelable auth, graceful Ctrl+C, and adaptive throttling.")
    # selection
    g = p.add_mutually_exclusive_group(required=False)
    g.add_argument("--sender", action="append", help="Sender email. Use multiple --sender flags for several.")
    g.add_argument("--senders", help="Comma-separated list of sender emails.")
    g.add_argument("--sender-file", help="Text file with one sender per line.")
    p.add_argument("--unread", action="store_true", help="Target only unread. With no senders, targets ALL unread.")
    p.add_argument("--older-than-days", type=int, help="Only messages older than N days.")
    p.add_argument("--newer-than-days", type=int, help="Only messages newer than N days.")
    p.add_argument("--preserve-attachments", action="store_true", help="Preserve emails that have attachments (exclude them).")

    p.add_argument("--folder", default=os.getenv("OUTLOOK_FOLDER","Inbox"),
                   help="Folder (default: Inbox). Examples: Inbox, DeletedItems, JunkEmail, Archive, or custom.")

    # auth
    p.add_argument("--client-id", help="Azure App Client ID (or set OUTLOOK_CLIENT_ID).")
    p.add_argument("--tenant", default=os.getenv("OUTLOOK_TENANT","consumers"),
                   help='AAD tenant: "consumers" (personal Outlook/Hotmail), "common", or your tenant ID.')
    p.add_argument("--device-code", action="store_true", help="Use device-code auth instead of interactive browser.")
    p.add_argument("--auth-timeout-seconds", type=int, default=AUTH_TIMEOUT_DEFAULT,
                   help=f"Max time to wait for authentication before aborting (default {AUTH_TIMEOUT_DEFAULT}s).")

    # performance / throttling knobs
    p.add_argument("--page-top", type=int, default=PAGE_TOP_DEFAULT, help="Messages per page (max 100).")
    p.add_argument("--batch-size", type=int, default=BATCH_MAX_DEFAULT, help="Deletes per $batch (max 20).")
    p.add_argument("--max-workers", type=int, default=DEFAULT_WORKERS, help="Parallel $batch workers.")
    p.add_argument("--hard-delete", action="store_true", help="Permanently delete (skip Deleted Items).")
    p.add_argument("--adaptive-throttle", action="store_true", help="Auto-reduce workers/batch size when throttled.")
    p.add_argument("--min-workers", type=int, default=1, help="Lower bound for workers when adapting.")
    p.add_argument("--min-batch-size", type=int, default=5, help="Lower bound for batch size when adapting (>=1, <=20).")
    p.add_argument("--submit-sleep-ms", type=int, default=0, help="Sleep this many ms between submitting batches.")

    # retry waves
    p.add_argument("--max-retry-waves", type=int, default=6, help="Max retry waves for 429/5xx sub-requests.")
    p.add_argument("--retry-base-wait", type=int, default=5, help="Base wait seconds for exponential backoff between waves.")

    # UX & safety
    p.add_argument("--dry-run", action="store_true", help="Only report counts; no deletion.")
    p.add_argument("--test-auth", action="store_true", help="Test login and print scopes + sample folders.")
    p.add_argument("--progress", action="store_true", help="Show progress while fetching and deleting.")
    p.add_argument("--verbose", action="store_true", help="Verbose HTTP logging.")
    p.add_argument("--timeout-seconds", type=int, default=TIMEOUT_DEFAULT, help="HTTP timeout per request.")
    p.add_argument("--yes", action="store_true", help="Skip confirmation prompt before deleting.")
    p.add_argument("--confirm-threshold", type=int, default=500, help="Prompt if total matches >= this number (unless --yes).")

    # CSV report
    p.add_argument("--report-csv", help="Write a CSV report of matches to this path.")
    p.add_argument("--report-limit", type=int, help="Max rows to write to CSV (default: all).")
    args = p.parse_args()

    # bounds
    if args.page_top < 1 or args.page_top > 100: args.page_top = 100
    if args.batch_size < 1: args.batch_size = 1
    if args.batch_size > 20: args.batch_size = 20
    if args.min_batch_size < 1: args.min_batch_size = 1
    if args.min_batch_size > 20: args.min_batch_size = 20
    if args.min_workers < 1: args.min_workers = 1

    client_id = args.client_id or os.getenv("OUTLOOK_CLIENT_ID")
    if not client_id:
        print("❌ Provide --client-id or set OUTLOOK_CLIENT_ID.", file=sys.stderr); sys.exit(1)

    # Build sender set (optional if --unread)
    senders = set()
    if args.sender: senders.update(args.sender)
    if args.senders: senders.update([s.strip() for s in args.senders.split(",") if s.strip()])
    if args.sender_file:
        try: senders.update(load_sender_list(args.sender_file))
        except FileNotFoundError:
            print(f"❌ Sender file not found: {args.sender_file}", file=sys.stderr); sys.exit(1)
    if not senders and not args.unread:
        print("❌ Provide senders OR use --unread to target all unread.", file=sys.stderr); sys.exit(1)

    try:
        # Auth
        token_result = get_token(client_id, args.tenant, args.device_code, args.auth_timeout_seconds)
        if args.test_auth:
            auth_tester(token_result, args.timeout_seconds, args.verbose); return
        access_token = token_result["access_token"]

        # Resolve folder
        folder_id = resolve_folder_id(access_token, args.folder, args.timeout_seconds, args.verbose)

        # Decide if we need richer fields (for CSV)
        want_report = bool(args.report_csv)

        # Gather (IDs + optional rows)
        all_ids: List[str] = []
        all_rows: List[Dict[str, Any]] = []

        if senders:
            for s in sorted(senders):
                ids, rows = list_messages(access_token, folder_id, s, args.unread,
                                          args.older_than_days, args.newer_than_days,
                                          args.timeout_seconds, args.verbose, args.progress,
                                          label=f"{args.folder}:{s}", page_top=args.page_top,
                                          want_report=want_report, preserve_attachments=args.preserve_attachments)
                print(f"Found {len(ids)} message(s) from {s} in {args.folder}"
                      + (" (unread only)" if args.unread else "")
                      + (" (attachments preserved)" if args.preserve_attachments else ""))
                all_ids.extend(ids); all_rows.extend(rows)
        else:
            ids, rows = list_messages(access_token, folder_id, None, True,
                                      args.older_than_days, args.newer_than_days,
                                      args.timeout_seconds, args.verbose, args.progress,
                                      label=f"{args.folder}:unread", page_top=args.page_top,
                                      want_report=want_report, preserve_attachments=args.preserve_attachments)
            print(f"Found {len(ids)} unread message(s) in {args.folder}"
                  + (" (attachments preserved)" if args.preserve_attachments else ""))
            all_ids.extend(ids); all_rows.extend(rows)

        # De-dup IDs (preserve order)
        unique_ids = list(dict.fromkeys(all_ids))
        if len(unique_ids) != len(all_ids):
            seen = set(); filtered_rows = []
            for r in all_rows:
                mid = r.get("id")
                if mid and mid not in seen:
                    filtered_rows.append(r); seen.add(mid)
            all_rows = filtered_rows

        total = len(unique_ids)
        print(f"Total messages matched: {total}")

        # Write CSV if requested
        if args.report_csv and all_rows:
            written, note = write_csv(args.report_csv, all_rows, args.report_limit)
            msg = f"📄 Wrote CSV report: {args.report_csv} ({written} row(s))"
            if note: msg += f" {note}"
            print(msg)

        if args.dry_run or total == 0 or CANCEL.is_set():
            return

        # Confirmation prompt (unless --yes or below threshold)
        if not args.yes and total >= args.confirm_threshold:
            try:
                mode = "hard delete (permanent)" if args.hard_delete else "delete (move to Deleted Items)"
                resp = input(f"\nAbout to {mode} {total} message(s) in '{args.folder}'. Proceed? [y/N]: ").strip().lower()
                if resp not in ("y","yes"):
                    print("Aborted. No messages were deleted.")
                    return
            except (EOFError, KeyboardInterrupt):
                print("\nAborted before deletion.", file=sys.stderr)
                return

        # Delete with retries & optional adaptive throttling
        deleted = parallel_batch_delete(
            access_token, unique_ids,
            batch_size=args.batch_size,
            max_workers=args.max_workers,
            timeout=args.timeout_seconds,
            verbose=args.verbose,
            progress=args.progress,
            hard_delete=args.hard_delete,
            max_retry_waves=args.max_retry_waves,
            base_sleep=args.retry_base_wait,
            adaptive=args.adaptive_throttle,
            min_workers=args.min_workers,
            min_batch_size=args.min_batch_size,
            submit_sleep_ms=args.submit_speech_ms if hasattr(args, "submit_speech_ms") else args.submit_sleep_ms,  # backward-safety
        )
        mode = "hard-deleted" if args.hard_delete else "deleted"
        scope = "unread " if args.unread else ""
        attn = " (attachments preserved)" if args.preserve_attachments else ""
        print(f"✅ {mode} {deleted} {scope}message(s) in {args.folder}.{attn}")
    except TimeoutError as te:
        print(f"\n❌ {te}", file=sys.stderr); return
    except KeyboardInterrupt:
        print("\nStopped by user (Ctrl+C). Work done so far was kept.", file=sys.stderr); return

if __name__ == "__main__":
    main()
