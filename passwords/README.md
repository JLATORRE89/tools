
---

## `README.md`

````markdown
# Password & System Security Scanner

A combined tool to:

1. Check your **own passwords** (from a Chrome-exported CSV or other password CSV) against the [Have I Been Pwned](https://haveibeenpwned.com/Passwords) Pwned Passwords API using the k-anonymity model.
2. Run a **safe system audit** on:
   - `/etc/passwd`-style user listings (no hashes)
   - `sshd_config` hardening
   - `.env` / KEY=VALUE secret config files (local, offline checks)

No password hashes (`/etc/shadow`, SAM, etc.) are ever read or processed.  
No secrets from system-audit are sent to external services.

---

## Features

### Password Breach Scan

- Accepts a **Chrome-style CSV** export:
  - Columns like: `name`, `url`, `username`, `password`
- Checks **each unique password** against the Pwned Passwords API.
- Groups reused passwords and shows:
  - Breach count
  - Severity: `SAFE`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
- Outputs:
  - `pwned_report.csv` – flat per-account table
  - `pwned_report.html` – interactive HTML:
    - Clickable sortable headers
    - Quick filter box
    - Reused password groups section (passwords anonymized)

### System Audit (Safe)

- `/etc/passwd`-style file:
  - Counts total users
  - Lists UID 0 users
  - Counts users with interactive shells
  - Flags issues like multiple UID 0 accounts

- `sshd_config`:
  - Flags risky settings:
    - `PermitRootLogin yes`
    - `PasswordAuthentication yes`
    - `PermitEmptyPasswords yes`
    - `ChallengeResponseAuthentication yes`

- `.env` / KEY=VALUE config:
  - Looks for keys containing:
    - `password`, `passwd`, `secret`, `token`, `apikey`, `api_key`, `key`
  - Flags values that are:
    - Very short (`< 12` chars)
    - Default-ish (e.g. `password`, `changeme`, `123456`, `admin`, `test`)
  - **All checks are local**; nothing is sent to external APIs.

---

## Installation

```bash
pip install fastapi uvicorn requests
````

You’ll also need Python 3.8+.

---

## CLI Usage

### 1. Password Scan (Chrome CSV → HTML/CSV reports)

Export passwords from Chrome:

1. Chrome → Settings → Autofill → Password Manager
2. Export passwords → save as `Chrome Passwords.csv`

Then run:

```bash
python check_passwords_pwned.py scan --csv "C:\Users\OfficePC\Documents\Chrome Passwords.csv"
```

Outputs:

* `pwned_report.csv`
* `pwned_report.html`

Open `pwned_report.html` in your browser:

* Click headers (e.g., Severity, Breach Count, Reuse Count) to sort.
* Use the Quick Filter box to search by site, domain, username, or severity.
* Check the “Reused Passwords” table to see which clusters to fix first.

If you omit `--csv`, it uses the default `CSV_PATH` in the script.

---

### 2. System Audit (CLI)

You explicitly provide non-sensitive files:

```bash
python check_passwords_pwned.py system-audit \
  --passwd "/etc/passwd" \
  --sshd "/etc/ssh/sshd_config" \
  --env "/opt/myapp/.env"
```

You can omit any of the three flags if you don’t want to audit that piece, e.g.:

```bash
python check_passwords_pwned.py system-audit --sshd "/etc/ssh/sshd_config"
```

The tool prints a console report:

* `/etc/passwd`-style summary & issues
* `sshd_config` issues (if any)
* `.env` weak secrets

> ⚠️ This mode **never** reads `/etc/shadow`, SAM, or any password hash store.

---

## API Usage

Start the API server:

```bash
python check_passwords_pwned.py api --host 127.0.0.1 --port 8001
```

Available endpoints:

### `GET /help`

Returns plain-text help describing all endpoints and how to export files:

```bash
curl http://127.0.0.1:8001/help
```

---

### `POST /scan`

Upload a Chrome-style passwords CSV and get JSON back.

Example (Linux/macOS):

```bash
curl -X POST "http://127.0.0.1:8001/scan" \
  -H "accept: application/json" \
  -F "file=@ChromePasswords.csv"
```

Response structure:

```json
{
  "summary": {
    "total_unique_passwords": 25,
    "compromised_passwords": 4,
    "safe_passwords": 21,
    "total_accounts": 60,
    "reused_password_groups": 3
  },
  "reused_passwords": [
    {
      "password_id": "A1B2C3D4E5",
      "reuse_count": 5,
      "breach_count": 1200,
      "severity": "CRITICAL",
      "accounts": [
        {
          "site_name": "Gmail",
          "url": "https://accounts.google.com",
          "username": "you@example.com"
        }
      ]
    }
  ],
  "accounts": [
    {
      "status": "COMPROMISED",
      "severity": "HIGH",
      "breach_count": 350,
      "reuse_count": 5,
      "site_name": "Gmail",
      "url": "https://accounts.google.com",
      "username": "you@example.com"
    }
  ]
}
```

> Note: JSON includes **no plaintext passwords**.

---

### `POST /system-audit`

Safe system audit via API.

Example (Linux/macOS):

```bash
curl -X POST "http://127.0.0.1:8001/system-audit" \
  -F "passwd_file=@/etc/passwd" \
  -F "sshd_file=@/etc/ssh/sshd_config" \
  -F "env_file=@/opt/myapp/.env"
```

Example (PowerShell):

```powershell
curl -X POST "http://127.0.0.1:8001/system-audit" `
  -F "passwd_file=@'C:\temp\passwd.audit'" `
  -F "sshd_file=@'C:\temp\sshd_config.audit'" `
  -F "env_file=@'C:\projects\myapp\.env'"
```

Response:

```json
{
  "audit": {
    "passwd": {
      "summary": {
        "total_users": 23,
        "uid0_users": 1,
        "login_shell_users": 5
      },
      "uid0_users": [ ... ],
      "login_shell_users": [ ... ],
      "issues": [ ... ]
    },
    "sshd_config": {
      "settings": { ... },
      "issues": [ ... ]
    },
    "env_file": {
      "total_variables": 18,
      "weak_variables": [
        { "key": "DB_PASSWORD", "length": 8, "reason": "too short" }
      ]
    }
  }
}
```

---

## How to Export Files Safely

### passwd_file

On Linux:

```bash
sudo cp /etc/passwd ./passwd.audit
```

Upload `passwd.audit` as `passwd_file`.

> This file contains usernames, UIDs, shells, etc. It does **not** contain password hashes.

---

### sshd_file

On Linux:

```bash
sudo cp /etc/ssh/sshd_config ./sshd_config.audit
```

Upload `sshd_config.audit` as `sshd_file`.

---

### env_file

Copy your application env/config:

```bash
cp /opt/myapp/.env ./myapp.env
```

Upload `myapp.env` as `env_file`.

> The system-audit endpoint **never** sends your file contents to external APIs. All checks are local.

---

## Security Notes

* Do **NOT** use this tool on:

  * `/etc/shadow`
  * Windows SAM
  * Any password hash dumps
* Designed for:

  * Your **own** credentials (browser password exports, password manager exports)
  * Systems you control (your servers, your configs)
* Pwned Passwords lookups use the k-anonymity API and only send the **first 5 chars of the SHA-1 hash**, not the full password or full hash.

---

## License / Disclaimer

* Use at your own risk.
* Always review findings before taking action.
* Do not run this against systems or credentials you do not own or administer.

```