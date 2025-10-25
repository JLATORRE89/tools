# outlook\_batch\_delete — README

Clean up Outlook/Exchange **Online** mailboxes using **Microsoft Graph**:

* Delete unread/all emails (optionally filtered by **sender**, **date**, **attachments**)
* **CSV report** mode
* **Parallel** `$batch` deletes with **sub-request retries** and **adaptive throttling**
* **Progress** output
* **Confirmation** prompt (with threshold)
* **Graceful Ctrl+C**
* **Cancelable** authentication (timeout aware)

> **Note**: Works with **Exchange Online / Outlook.com**. It does **not** support Exchange **on-prem** (use EWS/EMS for that).

---

## 1) Requirements

* **Python** 3.8+

* Packages:

  ```bash
  pip install msal requests
  ```

* An **Azure app registration** (public client) with **Delegated** permission:

  * `Mail.ReadWrite`
  * Supported accounts:

    * **Outlook.com / Personal Microsoft Account** → use tenant `consumers`
    * **Work/School (Microsoft 365)** → use your **tenant ID** or `organizations`
  * Public client auth is supported (device code or interactive browser).

---

## 2) Quick Start

Delete all **unread** mail older than **365 days**, hard-delete, throttle-friendly:

```powershell
python outlook_batch_delete.py --unread --older-than-days 365 --yes `
  --client-id YOUR_CLIENT_ID --tenant consumers `
  --hard-delete --max-workers 1 --batch-size 10 --page-top 100 --progress `
  --adaptive-throttle --min-workers 1 --min-batch-size 5 `
  --max-retry-waves 8 --retry-base-wait 5 --submit-sleep-ms 75
```

> Tip: For **work/school tenants**, replace `--tenant consumers` with your **tenant ID** or `organizations`.

Dry-run (no deletion) + CSV report:

```powershell
python outlook_batch_delete.py --unread --older-than-days 365 --dry-run `
  --client-id YOUR_CLIENT_ID --tenant consumers `
  --report-csv .\report.csv --report-limit 50000 --progress
```

Delete from one or more **senders**:

```powershell
# Single
python outlook_batch_delete.py --sender no-reply@emails.skechers.com --yes `
  --client-id YOUR_CLIENT_ID --tenant consumers --hard-delete --progress

# Multiple (flags or comma list)
python outlook_batch_delete.py --sender a@ex.com --sender b@ex.com --yes ...
python outlook_batch_delete.py --senders a@ex.com,b@ex.com --yes ...
```

Preserve any message that **has attachments** (inline counts as an attachment):

```powershell
python outlook_batch_delete.py --unread --preserve-attachments --yes `
  --client-id YOUR_CLIENT_ID --tenant consumers --hard-delete --progress
```

---

## 3) Authentication

* **Interactive** (default): pops browser to sign in.
* **Device code** (no browser on this machine):

  ```powershell
  python outlook_batch_delete.py --unread --device-code --yes --client-id YOUR_CLIENT_ID --tenant consumers
  ```
* **Timeout / cancel**:

  * `--auth-timeout-seconds 600` (default 10 min)
  * Ctrl+C during auth cancels immediately.

Test auth (prints scopes + sample folders):

```powershell
python outlook_batch_delete.py --test-auth --client-id YOUR_CLIENT_ID --tenant consumers
```

---

## 4) Options (CLI)

### Selection filters

* `--sender EMAIL` (repeatable)
* `--senders "a@ex.com,b@ex.com"`
* `--sender-file PATH` (one email per line, `#` or `;` comments)
* `--unread` (when used **without** senders, targets **all unread**)
* `--older-than-days N`
* `--newer-than-days N`
* `--preserve-attachments` → **excludes** any message where `hasAttachments = true`
* `--folder NAME` (default `Inbox`; well-known names allowed: `Inbox`, `DeletedItems`, `JunkEmail`, `Archive`, `Drafts`, `SentItems`)

### Auth

* `--client-id GUID` (or set env `OUTLOOK_CLIENT_ID`)
* `--tenant consumers|organizations|<tenant-id>` (or env `OUTLOOK_TENANT`, default `consumers`)
* `--device-code`
* `--auth-timeout-seconds 600`

### Performance / throttling

* `--page-top N` (1–100; fetch page size)
* `--batch-size N` (1–20; deletes per `$batch`)
* `--max-workers N` (parallel `$batch` workers)
* `--hard-delete` (permanent; skips Deleted Items)
* `--adaptive-throttle` (auto-reduce workers/batch under heavy throttling)
* `--min-workers N` (default 1)
* `--min-batch-size N` (default 5)
* `--submit-sleep-ms N` (pause between submitting batches)

### Retry waves (for sub-request 429/5xx)

* `--max-retry-waves N` (default 6)
* `--retry-base-wait SECONDS` (default 5) – exponential backoff + jitter between waves

### UX & safety

* `--dry-run` (no deletion)
* `--report-csv PATH` (+ `--report-limit N`) → writes `id,from,subject,receivedDateTime,hasAttachments`
* `--yes` (skip prompt)
* `--confirm-threshold N` (default 500; prompt only when matches ≥ N unless `--yes`)
* `--progress` (live progress while fetching/deleting)
* `--verbose` (HTTP traces)
* `--timeout-seconds N` (per HTTP request; default 30)

---

## 5) Typical Workflows

### A. Unread cleanup in chunks (older first)

```powershell
# Pass 1: very old
python outlook_batch_delete.py --unread --older-than-days 365 --yes `
  --client-id YOUR_CLIENT_ID --tenant consumers --hard-delete `
  --max-workers 1 --batch-size 10 --progress --adaptive-throttle `
  --max-retry-waves 8 --retry-base-wait 5 --submit-sleep-ms 75

# Pass 2: the rest
python outlook_batch_delete.py --unread --newer-than-days 365 --yes `
  --client-id YOUR_CLIENT_ID --tenant consumers --hard-delete `
  --max-workers 1 --batch-size 10 --progress --adaptive-throttle
```

### B. Target noisy senders but keep attachments

```powershell
python outlook_batch_delete.py --senders deals@shop.com,news@site.com `
  --preserve-attachments --yes --client-id YOUR_CLIENT_ID --tenant consumers `
  --hard-delete --max-workers 1 --batch-size 10 --progress --adaptive-throttle
```

### C. Report first, then delete with confirmation

```powershell
python outlook_batch_delete.py --unread --dry-run `
  --client-id YOUR_CLIENT_ID --tenant consumers `
  --report-csv .\unread_report.csv --progress

# Review CSV, then:
python outlook_batch_delete.py --unread --yes --client-id YOUR_CLIENT_ID --tenant consumers --hard-delete
```

---

## 6) Throttling (HTTP 429) — What to do

If you see:

```
[WARN] Delete failed: ... 429 ApplicationThrottled ("MailboxConcurrency limit")
```

That’s Microsoft Graph limiting requests to this mailbox. The script already:

* Retries **only** the sub-requests that failed (429/5xx), in **waves** with backoff
* Optionally **reduces** `workers`/`batch-size` when retry rate is high (`--adaptive-throttle`)

**Recommendations**

1. Start conservative: `--max-workers 1 --batch-size 10 --submit-sleep-ms 50-100`
2. Use **date slices** (older/newer than) and re-run
3. Re-run the same command; already-deleted items won’t reappear

---

## 7) PowerShell: environment variables (optional)

Set for **current session**:

```powershell
$env:OUTLOOK_CLIENT_ID = "YOUR_CLIENT_ID"
$env:OUTLOOK_TENANT   = "consumers"       # or your tenant id / organizations
```

Persist for **current user**:

```powershell
[Environment]::SetEnvironmentVariable("OUTLOOK_CLIENT_ID", "YOUR_CLIENT_ID", "User")
[Environment]::SetEnvironmentVariable("OUTLOOK_TENANT",   "consumers",      "User")
```

---

## 8) Safety & Notes

* **Hard delete** is **permanent**. Use `--dry-run` and/or `--report-csv` to verify.
* `--preserve-attachments` excludes any message with **any** attachment (including **inline images**).
* `$batch` hard cap is **20** sub-requests; `--batch-size` is clamped to that.
* `--page-top` hard cap is **100**.
* Ctrl+C will **gracefully stop**: remaining queued batches are canceled; completed deletions remain.

---

## 9) Troubleshooting

* **400 Bad Request** on date filters
  Ensure the script is up to date (uses OData DateTimeOffset **without quotes**, e.g., `2024-09-02T00:00:00Z`). This README’s script already includes the fix.

* **401/403** during delete
  Your app must have **Delegated** `Mail.ReadWrite`. Sign in with the target mailbox and consent.

* **“request not valid for the application's userAudience / /common”**
  Use the correct `--tenant` for your app’s audience:

  * Outlook.com (personal) → `consumers`
  * Work/school → your tenant ID or `organizations`

* **Hangs on auth**
  Use `--auth-timeout-seconds`, or `--device-code` if a browser isn’t available. Ctrl+C cancels immediately.

---

## 10) License & Contributions
