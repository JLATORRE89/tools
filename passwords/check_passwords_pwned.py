import csv
import hashlib
import html
from io import StringIO
from pathlib import Path
from collections import defaultdict
from typing import Optional

import requests
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, PlainTextResponse

# -------- CONFIG --------
# Default CSV path for CLI mode – you can override with subcommand args
CSV_PATH = Path(r"C:\Users\OfficePC\Documents\Chrome Passwords.csv")

REPORT_CSV_PATH = Path("pwned_report.csv")        # Output CSV
REPORT_HTML_PATH = Path("pwned_report.html")      # Output HTML

HIBP_API_URL = "https://api.pwnedpasswords.com/range/"
TIMEOUT = 10
# ------------------------


HELP_TEXT = """
Password & System Security Scanner API
======================================

Endpoints
---------

1) POST /scan
   Upload a Chrome-style CSV export of passwords.
   - Field: file (multipart/form-data)
   - Input: CSV with columns like: name, url, username, password
   - Output: JSON
       {
         "summary": { ... },
         "reused_passwords": [ ... ],
         "accounts": [ ... ]
       }

   Notes:
   - Uses Have I Been Pwned's Pwned Passwords API (k-anonymity).
   - Never returns plaintext passwords in the JSON.
   - Groups reused passwords and gives each group an anonymous password_id.

2) POST /system-audit
   Safe system configuration audit. No password hashes, no /etc/shadow.

   Accepts up to three files (all optional, but at least one must be provided):

   - passwd_file: /etc/passwd-style file (no hashes)
   - sshd_file: sshd_config file
   - env_file: .env or KEY=VALUE config file

   Example curl:
     curl -X POST http://127.0.0.1:8001/system-audit \\
       -F "passwd_file=@/etc/passwd" \\
       -F "sshd_file=@/etc/ssh/sshd_config" \\
       -F "env_file=@/opt/myapp/.env"

   Returns:
     {
       "audit": {
         "passwd": { ... },
         "sshd_config": { ... },
         "env_file": { ... }
       }
     }

   What is checked:
   - passwd_file:
       * total users
       * users with UID 0
       * users with interactive shells
       * issues like multiple UID 0 users
   - sshd_file:
       * flags risky sshd_config settings:
         - PermitRootLogin yes
         - PasswordAuthentication yes
         - PermitEmptyPasswords yes
         - ChallengeResponseAuthentication yes
   - env_file:
       * scans for weak-looking secrets in keys containing:
         "password", "passwd", "secret", "token", "apikey", "api_key", "key"
       * flags very short values or default-ish values (e.g. "password", "changeme")

3) GET /help
   Returns this help text as plain text.


How to export files safely
--------------------------

passwd_file:
  On Linux:
    sudo cp /etc/passwd ./passwd.audit
  Then upload 'passwd.audit' as 'passwd_file'.

sshd_file:
  On Linux:
    sudo cp /etc/ssh/sshd_config ./sshd_config.audit
  Then upload 'sshd_config.audit' as 'sshd_file'.

env_file:
  Copy your app's environment file or secret config:
    cp /opt/myapp/.env ./myapp.env
  Then upload 'myapp.env' as 'env_file'.

Security Notes
--------------
- Do NOT upload /etc/shadow, Windows SAM, or any password hash dumps.
- This tool is for systems you control and for reviewing *your own* credentials.
- The system-audit endpoint never sends your file contents to external APIs.
"""


# ================== PASSWORD CHECK LOGIC ================== #

def sha1_hex(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest().upper()


def check_password_pwned(password: str) -> int:
    """
    Uses Have I Been Pwned Pwned Passwords API (k-anonymity model).
    Returns number of times seen in breaches (0 if not found).
    """
    full_hash = sha1_hex(password)
    prefix = full_hash[:5]
    suffix = full_hash[5:]

    url = HIBP_API_URL + prefix
    response = requests.get(url, timeout=TIMEOUT)
    if response.status_code != 200:
        raise RuntimeError(
            f"HIBP API error: {response.status_code} {response.text[:200]}"
        )

    for line in response.text.splitlines():
        try:
            hash_suffix, count = line.strip().split(":")
        except ValueError:
            continue
        if hash_suffix.upper() == suffix:
            return int(count)

    return 0


def _load_passwords_from_reader(reader: csv.DictReader):
    """
    Internal helper: load rows from a DictReader.
    Returns a list of dicts:
      { 'name': ..., 'url': ..., 'username': ..., 'password': ... }
    """
    rows = []
    headers = {h.lower(): h for h in (reader.fieldnames or [])}

    def get(row, *possible):
        for key in possible:
            if key in headers:
                return row.get(headers[key], "")
        return ""

    for row in reader:
        item = {
            "name": get(row, "name", "site", "website"),
            "url": get(row, "url", "origin", "website", "site"),
            "username": get(row, "username", "user", "login"),
            "password": get(row, "password"),
        }
        if item["password"]:
            rows.append(item)
    return rows


def load_passwords_from_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return _load_passwords_from_reader(reader)


def load_passwords_from_text(csv_text: str):
    """For API uploads: load entries from a CSV text string."""
    f = StringIO(csv_text)
    reader = csv.DictReader(f)
    return _load_passwords_from_reader(reader)


def severity_label(count: int) -> str:
    """Return a severity label based on breach count."""
    if count <= 0:
        return "SAFE"
    if count <= 10:
        return "LOW"
    if count <= 100:
        return "MEDIUM"
    if count <= 1000:
        return "HIGH"
    return "CRITICAL"


def analyze_entries(entries):
    """
    Core analysis logic.
    entries: list of {name, url, username, password}
    Returns:
      results           - list of {password, count, accounts}
      per_account_records  - flat list of rows for CSV/HTML
      summary           - dict with high-level stats
      reused_groups     - list of groups for reused passwords
    """
    # Map password -> list of accounts
    password_map = defaultdict(list)
    for e in entries:
        password_map[e["password"]].append(
            {
                "name": e["name"],
                "url": e["url"],
                "username": e["username"],
            }
        )

    print(f"[INFO] Checking {len(password_map)} unique passwords against HIBP ...")

    results = []  # each: {password, count, accounts}

    for idx, (pwd, accounts) in enumerate(password_map.items(), start=1):
        try:
            count = check_password_pwned(pwd)
        except Exception as e:
            print(f"[WARN] Could not check password #{idx}: {e}")
            continue

        results.append(
            {
                "password": pwd,
                "count": count,
                "accounts": accounts,
            }
        )
        if idx % 10 == 0 or idx == len(password_map):
            print(f"[INFO] Checked {idx}/{len(password_map)} passwords...")

    compromised = [r for r in results if r["count"] > 0]
    safe = [r for r in results if r["count"] <= 0]

    # Build per-account records for CSV/HTML (no plaintext passwords!)
    per_account_records = []
    for item in results:
        count = item["count"]
        sev = severity_label(count)
        status = "COMPROMISED" if count > 0 else "SAFE"
        reuse_count = len(item["accounts"])
        for acc in item["accounts"]:
            per_account_records.append(
                {
                    "status": status,
                    "severity": sev,
                    "breach_count": count,
                    "reuse_count": reuse_count,
                    "site_name": acc["name"] or "",
                    "url": acc["url"] or "",
                    "username": acc["username"] or "",
                }
            )

    # Reused passwords (same password on multiple accounts)
    reused_groups = []
    for item in results:
        accounts = item["accounts"]
        if len(accounts) > 1:
            reused_groups.append(
                {
                    # Short hash prefix as an anonymous ID for the password
                    "password_id": sha1_hex(item["password"])[:10],
                    "reuse_count": len(accounts),
                    "breach_count": item["count"],
                    "severity": severity_label(item["count"]),
                    "accounts": accounts,
                }
            )

    summary = {
        "total_unique_passwords": len(results),
        "compromised_passwords": len(compromised),
        "safe_passwords": len(safe),
        "total_accounts": len(per_account_records),
        "reused_password_groups": len(reused_groups),
    }

    return results, per_account_records, summary, reused_groups


def write_csv_report(per_account_records):
    fieldnames = [
        "status",
        "severity",
        "breach_count",
        "reuse_count",
        "site_name",
        "url",
        "username",
    ]
    with REPORT_CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in per_account_records:
            writer.writerow(rec)

    print(f"[INFO] CSV report written to: {REPORT_CSV_PATH}")


def write_html_report(per_account_records, summary, reused_groups):
    # Main table rows (per account) with severity-based row class
    html_rows = []
    for rec in per_account_records:
        sev_class = rec["severity"]
        html_rows.append(
            f"<tr class=\"{html.escape(sev_class)}\">"
            f"<td>{html.escape(rec['status'])}</td>"
            f"<td>{html.escape(rec['severity'])}</td>"
            f"<td>{rec['breach_count']}</td>"
            f"<td>{rec['reuse_count']}</td>"
            f"<td>{html.escape(rec['site_name'])}</td>"
            f"<td>{html.escape(rec['url'])}</td>"
            f"<td>{html.escape(rec['username'])}</td>"
            "</tr>"
        )

    # Reused password groups (no plaintext passwords)
    reused_sections = []
    if reused_groups:
        reused_sections.append("<h2>Reused Passwords (change these first)</h2>")
        reused_sections.append(
            "<p>Each group below represents the same password used on multiple accounts. "
            "The actual password value is NOT shown for security reasons.</p>"
        )

        reused_sections.append(
            "<table id=\"reused-table\">"
            "<thead><tr>"
            "<th data-type=\"string\">Password ID<span class=\"sort-indicator\"></span></th>"
            "<th data-type=\"number\">Reuse Count<span class=\"sort-indicator\"></span></th>"
            "<th data-type=\"number\">Breach Count<span class=\"sort-indicator\"></span></th>"
            "<th data-type=\"string\">Severity<span class=\"sort-indicator\"></span></th>"
            "<th data-type=\"string\">Accounts (Site / URL / Username)<span class=\"sort-indicator\"></span></th>"
            "</tr></thead><tbody>"
        )

        for grp in reused_groups:
            accounts_html = "<ul>"
            for acc in grp["accounts"]:
                accounts_html += (
                    "<li>"
                    f"{html.escape(acc.get('name') or '(no name)')} | "
                    f"{html.escape(acc.get('url') or '(no url)')} | "
                    f"{html.escape(acc.get('username') or '(no username)')}"
                    "</li>"
                )
            accounts_html += "</ul>"

            reused_sections.append(
                f"<tr class=\"{html.escape(grp['severity'])}\">"
                f"<td>{html.escape(grp['password_id'])}</td>"
                f"<td>{grp['reuse_count']}</td>"
                f"<td>{grp['breach_count']}</td>"
                f"<td>{html.escape(grp['severity'])}</td>"
                f"<td>{accounts_html}</td>"
                "</tr>"
            )

        reused_sections.append("</tbody></table>")

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Password Breach Report</title>
<style>
  body {{
    font-family: Arial, sans-serif;
    margin: 20px;
  }}
  h1, h2 {{
    margin-bottom: 0.3em;
  }}
  table {{
    border-collapse: collapse;
    width: 100%;
    margin-top: 1em;
  }}
  th, td {{
    border: 1px solid #ccc;
    padding: 6px 8px;
    font-size: 14px;
    vertical-align: top;
  }}
  th {{
    background: #f2f2f2;
    cursor: pointer;
    user-select: none;
  }}
  tr:nth-child(even) {{
    background: #fafafa;
  }}
  .SAFE {{ background-color: #e6ffe6; }}
  .LOW {{ background-color: #ffffe6; }}
  .MEDIUM {{ background-color: #fff0cc; }}
  .HIGH {{ background-color: #ffe6e6; }}
  .CRITICAL {{ background-color: #ffd6d6; }}

  .sort-indicator {{
    font-size: 11px;
    margin-left: 4px;
    opacity: 0.7;
  }}

  #filter-box {{
    margin: 10px 0;
  }}
  #filter-input {{
    padding: 4px 6px;
    font-size: 14px;
    width: 260px;
  }}
</style>
</head>
<body>
<h1>Password Breach Report</h1>

<h2>Summary</h2>
<ul>
  <li>Total unique passwords checked: {summary['total_unique_passwords']}</li>
  <li>Compromised passwords: {summary['compromised_passwords']}</li>
  <li>Unseen (safe) passwords: {summary['safe_passwords']}</li>
  <li>Total accounts (rows in this report): {summary['total_accounts']}</li>
  <li>Reused password groups: {summary['reused_password_groups']}</li>
</ul>

{"".join(reused_sections)}

<h2>Details by Account</h2>
<p>
  <strong>Status</strong>: SAFE = not found in breaches, COMPROMISED = found in Pwned Passwords.<br>
  <strong>Severity</strong>: based on how many times that password appears in breaches.<br>
  <strong>Password Reuse Count</strong>: how many accounts share that password.<br>
  Click a column header to sort. Use the filter box below to narrow rows.
</p>

<div id="filter-box">
  <label for="filter-input"><strong>Quick Filter:</strong> </label>
  <input id="filter-input" type="text" placeholder="Filter by site, URL, username, severity, etc." />
</div>

<table id="accounts-table">
  <thead>
    <tr>
      <th data-type="string">Status<span class="sort-indicator"></span></th>
      <th data-type="string">Severity<span class="sort-indicator"></span></th>
      <th data-type="number">Breach Count<span class="sort-indicator"></span></th>
      <th data-type="number">Password Reuse Count<span class="sort-indicator"></span></th>
      <th data-type="string">Site Name<span class="sort-indicator"></span></th>
      <th data-type="string">URL<span class="sort-indicator"></span></th>
      <th data-type="string">Username<span class="sort-indicator"></span></th>
    </tr>
  </thead>
  <tbody>
    {''.join(html_rows)}
  </tbody>
</table>

<script>
// Generic table sort function (numeric or string) for any table
function makeTableSortable(tableId) {{
  const table = document.getElementById(tableId);
  if (!table) return;
  const headers = table.querySelectorAll("thead th");
  headers.forEach((th, index) => {{
    th.addEventListener("click", () => sortTable(table, index, th));
  }});
}}

function sortTable(table, colIndex, header) {{
  const tbody = table.querySelector("tbody");
  const rows = Array.from(tbody.querySelectorAll("tr"));
  const type = header.getAttribute("data-type") || "string";
  const currentDir = header.getAttribute("data-sort-dir") || "asc";
  const newDir = currentDir === "asc" ? "desc" : "asc";

  // Clear indicators on all headers in this table
  const allHeaders = table.querySelectorAll("thead th");
  allHeaders.forEach(h => {{
    h.setAttribute("data-sort-dir", "");
    const span = h.querySelector(".sort-indicator");
    if (span) span.textContent = "";
  }});

  // Set indicator on active header
  header.setAttribute("data-sort-dir", newDir);
  const indicator = header.querySelector(".sort-indicator");
  if (indicator) {{
    indicator.textContent = newDir === "asc" ? "▲" : "▼";
  }}

  rows.sort((a, b) => {{
    const aText = (a.children[colIndex].innerText || "").trim();
    const bText = (b.children[colIndex].innerText || "").trim();

    if (type === "number") {{
      const aVal = parseFloat(aText.replace(/[^0-9.-]/g, "")) || 0;
      const bVal = parseFloat(bText.replace(/[^0-9.-]/g, "")) || 0;
      return newDir === "asc" ? aVal - bVal : bVal - aVal;
    }} else {{
      const aVal = aText.toLowerCase();
      const bVal = bText.toLowerCase();
      if (aVal < bVal) return newDir === "asc" ? -1 : 1;
      if (aVal > bVal) return newDir === "asc" ? 1 : -1;
      return 0;
    }}
  }});

  // Re-attach rows
  rows.forEach(row => tbody.appendChild(row));
}}

// Filter rows in one table by text
function filterTable(tableId, query) {{
  const table = document.getElementById(tableId);
  if (!table) return;
  const tbody = table.querySelector("tbody");
  const rows = Array.from(tbody.querySelectorAll("tr"));
  const q = query.toLowerCase();

  rows.forEach(row => {{
    const text = row.innerText.toLowerCase();
    row.style.display = text.includes(q) ? "" : "none";
  }});
}}

document.addEventListener("DOMContentLoaded", function() {{
  makeTableSortable("accounts-table");
  makeTableSortable("reused-table");

  const filterInput = document.getElementById("filter-input");
  if (filterInput) {{
    filterInput.addEventListener("input", function() {{
      const val = filterInput.value || "";
      filterTable("accounts-table", val);
      filterTable("reused-table", val);
    }});
  }}
}});
</script>

</body>
</html>
"""
    with REPORT_HTML_PATH.open("w", encoding="utf-8") as f:
        f.write(doc)

    print(f"[INFO] HTML report written to: {REPORT_HTML_PATH}")


# ---------------- CLI MODE (PASSWORD SCAN) ---------------- #

def main_cli(csv_path: Path):
    if not csv_path.exists():
        print(f"[ERROR] CSV file not found: {csv_path}")
        print("Export your passwords from Chrome to a CSV and update CSV_PATH or pass --csv.")
        return

    print(f"[INFO] Loading passwords from {csv_path} ...")
    entries = load_passwords_from_csv(csv_path)
    print(f"[INFO] Loaded {len(entries)} entries with non-empty passwords.")

    results, per_account_records, summary, reused_groups = analyze_entries(entries)

    print("\n========== PASSWORD BREACH REPORT ==========\n")
    print(f"Total unique passwords: {summary['total_unique_passwords']}")
    print(f"Compromised passwords : {summary['compromised_passwords']}")
    print(f"Unseen passwords      : {summary['safe_passwords']}")
    print(f"Reused password groups: {summary['reused_password_groups']}\n")

    if summary["compromised_passwords"] > 0:
        print("=== PASSWORDS YOU SHOULD CHANGE (FOUND IN BREACHES) ===\n")
        for item in results:
            if item["count"] <= 0:
                continue
            label = severity_label(item["count"])
            print(f"Password seen {item['count']} times in breaches (severity: {label}).")
            for acc in item["accounts"]:
                name = acc['name'] or "(no name)"
                url = acc['url'] or "(no url)"
                user = acc['username'] or "(no username)"
                print(f"  - Site: {name} | URL: {url} | Username: {user}")
            print()
    else:
        print("Good news: None of your passwords were found in the Pwned Passwords database!")

    if summary["reused_password_groups"] > 0:
        print("=== REUSED PASSWORDS (CHANGE THESE FIRST) ===\n")
        for grp in reused_groups:
            print(
                f"Password ID {grp['password_id']} is used on {grp['reuse_count']} accounts "
                f"(severity: {grp['severity']}, breaches: {grp['breach_count']})."
            )
        print()

    write_csv_report(per_account_records)
    write_html_report(per_account_records, summary, reused_groups)

    print("\n=== SECURITY NOTES ===")
    print("- Any password that appears in breaches should be changed everywhere you use it.")
    print("- Prioritize passwords labeled HIGH or CRITICAL, especially if reused.")
    print("- Use unique, strong passwords and a reputable password manager.")
    print("- Enable multi-factor authentication (MFA) whenever possible.")
    print("- Delete the exported Chrome CSV once you’re done reviewing the reports.")


# ================== SYSTEM AUDIT LOGIC (SAFE) ================== #

def analyze_passwd_text(text: str) -> dict:
    """
    Analyze an /etc/passwd-style file (no password hashes).
    Returns summary and per-user details (no secrets).
    """
    users = []
    uid0_users = []
    login_shell_users = []

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(":")
        if len(parts) < 7:
            continue
        username, _, uid_str, gid_str, gecos, home, shell = parts[:7]
        try:
            uid = int(uid_str)
        except ValueError:
            uid = -1

        user = {
            "username": username,
            "uid": uid,
            "gid": gid_str,
            "gecos": gecos,
            "home": home,
            "shell": shell,
        }
        users.append(user)

        if uid == 0:
            uid0_users.append(user)
        # crude heuristic for "real" shells
        if shell not in ("/usr/sbin/nologin", "/bin/false", "nologin"):
            login_shell_users.append(user)

    issues = []

    if len(uid0_users) > 1:
        issues.append({
            "severity": "HIGH",
            "message": "Multiple UID 0 (root-equivalent) accounts detected.",
            "details": [u["username"] for u in uid0_users],
        })

    if not any(u["username"] == "root" and u["uid"] == 0 for u in users):
        issues.append({
            "severity": "MEDIUM",
            "message": "No 'root' user with UID 0 found (unusual configuration).",
        })

    return {
        "summary": {
            "total_users": len(users),
            "uid0_users": len(uid0_users),
            "login_shell_users": len(login_shell_users),
        },
        "uid0_users": uid0_users,
        "login_shell_users": login_shell_users,
        "issues": issues,
    }


def analyze_sshd_config_text(text: str) -> dict:
    """
    Analyze an OpenSSH sshd_config file (no secrets).
    Flags risky settings like PermitRootLogin yes, PasswordAuthentication yes, etc.
    """
    issues = []
    settings = {}

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        key = parts[0].lower()
        val = " ".join(parts[1:])
        settings[key] = val

    def flag_if(key, bad_values, severity, msg):
        val = settings.get(key)
        if val is not None and val.lower() in bad_values:
            issues.append({
                "severity": severity,
                "setting": key,
                "value": val,
                "message": msg,
            })

    flag_if(
        "permitrootlogin",
        {"yes"},
        "HIGH",
        "Root SSH login is enabled. Consider 'PermitRootLogin no' or 'prohibit-password'.",
    )
    flag_if(
        "passwordauthentication",
        {"yes"},
        "MEDIUM",
        "PasswordAuthentication is enabled. Prefer key-based auth only.",
    )
    flag_if(
        "permitemptypasswords",
        {"yes"},
        "CRITICAL",
        "PermitEmptyPasswords is enabled. This is extremely dangerous.",
    )
    flag_if(
        "challengeresponseauthentication",
        {"yes"},
        "LOW",
        "ChallengeResponseAuthentication is enabled; verify this is intentional.",
    )

    return {
        "settings": settings,
        "issues": issues,
    }


def analyze_env_text(text: str) -> dict:
    """
    Analyze a .env-style file for obviously weak secrets.
    Does NOT send anything to external services.
    """
    weak_vars = []
    all_vars = []

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if not key:
            continue

        rec = {
            "key": key,
            "length": len(value),
        }
        all_vars.append(rec)

        lowered_key = key.lower()
        if any(token in lowered_key for token in ("password", "passwd", "secret", "token", "apikey", "api_key", "key")):
            # simple heuristics
            is_defaultish = value.lower() in ("password", "changeme", "123456", "admin", "test")
            too_short = len(value) > 0 and len(value) < 12

            if is_defaultish or too_short:
                weak_vars.append({
                    "key": key,
                    "length": len(value),
                    "reason": "default-looking" if is_defaultish else "too short",
                })

    return {
        "total_variables": len(all_vars),
        "weak_variables": weak_vars,
    }


def run_system_audit(passwd_text: Optional[str], sshd_text: Optional[str], env_text: Optional[str]) -> dict:
    """
    Combine all system audit checks into a single result.
    All inputs are text; caller is responsible for reading files.
    """
    result = {
        "passwd": None,
        "sshd_config": None,
        "env_file": None,
    }
    if passwd_text is not None:
        result["passwd"] = analyze_passwd_text(passwd_text)
    if sshd_text is not None:
        result["sshd_config"] = analyze_sshd_config_text(sshd_text)
    if env_text is not None:
        result["env_file"] = analyze_env_text(env_text)
    return result


# ---------------- CLI SYSTEM AUDIT MODE ---------------- #

def main_system_audit(passwd_path: Optional[Path], sshd_path: Optional[Path], env_path: Optional[Path]):
    """
    CLI entry point for system audit.
    You pass paths explicitly; this function does not auto-read /etc/shadow or anything sensitive.
    """
    passwd_text = sshd_text = env_text = None

    if passwd_path is not None and passwd_path.exists():
        print(f"[INFO] Reading passwd-style file from {passwd_path}")
        passwd_text = passwd_path.read_text(encoding="utf-8", errors="replace")
    if sshd_path is not None and sshd_path.exists():
        print(f"[INFO] Reading sshd_config from {sshd_path}")
        sshd_text = sshd_path.read_text(encoding="utf-8", errors="replace")
    if env_path is not None and env_path.exists():
        print(f"[INFO] Reading .env file from {env_path}")
        env_text = env_path.read_text(encoding="utf-8", errors="replace")

    audit = run_system_audit(passwd_text, sshd_text, env_text)

    print("\n========== SYSTEM AUDIT REPORT ==========\n")

    if audit["passwd"]:
        p = audit["passwd"]["summary"]
        print("[/etc/passwd-style] Users:", p["total_users"])
        print("  UID 0 users:", p["uid0_users"])
        print("  Login-shell users:", p["login_shell_users"])
        for issue in audit["passwd"]["issues"]:
            print(f"  ISSUE ({issue['severity']}): {issue['message']}")
            if "details" in issue:
                print("    Details:", ", ".join(issue["details"]))
        print()

    if audit["sshd_config"]:
        print("[sshd_config] Issues:")
        if audit["sshd_config"]["issues"]:
            for issue in audit["sshd_config"]["issues"]:
                print(
                    f"  ISSUE ({issue['severity']}): {issue['message']} "
                    f"(setting {issue['setting']}={issue['value']})"
                )
        else:
            print("  No obvious risky sshd_config settings detected.")
        print()

    if audit["env_file"]:
        ev = audit["env_file"]
        print("[.env] Total variables:", ev["total_variables"])
        if ev["weak_variables"]:
            print("  Weak variables detected:")
            for v in ev["weak_variables"]:
                print(f"    {v['key']} (length={v['length']}, reason={v['reason']})")
        else:
            print("  No obviously weak secrets detected.")
        print()

    print("=== NOTES ===")
    print("- System audit does not read /etc/shadow or password hashes.")
    print("- Review uid 0 users, sshd_config, and any weak .env secrets manually.")


# ================== API MODE (FastAPI) ================== #

app = FastAPI(title="Password Breach Scanner API")


@app.post("/scan")
async def scan_passwords(file: UploadFile = File(...)):
    """
    Upload a Chrome-style CSV export of passwords.
    Returns JSON summary and details (no plaintext passwords in the response).
    """
    try:
        content_bytes = await file.read()
        csv_text = content_bytes.decode("utf-8", errors="replace")
        entries = load_passwords_from_text(csv_text)
        if not entries:
            return JSONResponse(
                status_code=400,
                content={"error": "No valid password entries found in CSV."},
            )

        _, per_account_records, summary, reused_groups = analyze_entries(entries)

        # Prepare a JSON-safe version of reused_groups (no passwords already)
        reused_groups_clean = []
        for grp in reused_groups:
            reused_groups_clean.append(
                {
                    "password_id": grp["password_id"],
                    "reuse_count": grp["reuse_count"],
                    "breach_count": grp["breach_count"],
                    "severity": grp["severity"],
                    "accounts": [
                        {
                            "site_name": acc.get("name") or "",
                            "url": acc.get("url") or "",
                            "username": acc.get("username") or "",
                        }
                        for acc in grp["accounts"]
                    ],
                }
            )

        return {
            "summary": summary,
            "reused_passwords": reused_groups_clean,
            "accounts": per_account_records,
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Internal error: {e}"},
        )


@app.post("/system-audit")
async def system_audit(
    passwd_file: Optional[UploadFile] = File(default=None),
    sshd_file: Optional[UploadFile] = File(default=None),
    env_file: Optional[UploadFile] = File(default=None),
):
    """
    Safe system audit endpoint.

    Accepts:
      - passwd_file: /etc/passwd-style file (no hashes, no /etc/shadow)
      - sshd_file: sshd_config file
      - env_file: .env or config file with KEY=VALUE lines

    Returns:
      JSON report with findings. Never sends contents to external APIs.
    """
    try:
        passwd_text = sshd_text = env_text = None

        if passwd_file is not None:
            passwd_bytes = await passwd_file.read()
            passwd_text = passwd_bytes.decode("utf-8", errors="replace")

        if sshd_file is not None:
            sshd_bytes = await sshd_file.read()
            sshd_text = sshd_bytes.decode("utf-8", errors="replace")

        if env_file is not None:
            env_bytes = await env_file.read()
            env_text = env_bytes.decode("utf-8", errors="replace")

        if not any([passwd_text, sshd_text, env_text]):
            return JSONResponse(
                status_code=400,
                content={"error": "No files provided. Upload at least one of passwd_file, sshd_file, env_file."},
            )

        audit = run_system_audit(passwd_text, sshd_text, env_text)
        return {"audit": audit}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Internal error: {e}"},
        )


@app.get("/help")
async def api_help():
    """Return human-readable help text about the API and how to export files."""
    return PlainTextResponse(HELP_TEXT)


# ================== ENTRYPOINT ================== #

if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="Password & System Security Scanner.")
    subparsers = parser.add_subparsers(dest="mode")

    # Password scan (default/legacy)
    scan_parser = subparsers.add_parser("scan", help="Scan Chrome-exported passwords against HIBP.")
    scan_parser.add_argument(
        "--csv",
        type=str,
        default=str(CSV_PATH),
        help="Path to Chrome passwords CSV (CLI mode).",
    )

    # System audit mode
    audit_parser = subparsers.add_parser("system-audit", help="Run safe system audit checks.")
    audit_parser.add_argument(
        "--passwd",
        type=str,
        default="",
        help="Path to passwd-style file (e.g. /etc/passwd export).",
    )
    audit_parser.add_argument(
        "--sshd",
        type=str,
        default="",
        help="Path to sshd_config file.",
    )
    audit_parser.add_argument(
        "--env",
        type=str,
        default="",
        help="Path to .env or config file with secrets.",
    )

    # API mode
    api_parser = subparsers.add_parser("api", help="Run FastAPI server with /scan and /system-audit.")
    api_parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="API host.",
    )
    api_parser.add_argument(
        "--port",
        type=int,
        default=8001,  # port 8001 as requested
        help="API port.",
    )

    args = parser.parse_args()

    if args.mode == "scan" or args.mode is None:
        # CLI password scan
        main_cli(Path(getattr(args, "csv", str(CSV_PATH))))
    elif args.mode == "system-audit":
        passwd_path = Path(args.passwd) if args.passwd else None
        sshd_path = Path(args.sshd) if args.sshd else None
        env_path = Path(args.env) if args.env else None
        main_system_audit(passwd_path, sshd_path, env_path)
    elif args.mode == "api":
        uvicorn.run(
            "check_passwords_pwned:app",
            host=args.host,
            port=args.port,
            reload=False,
        )
