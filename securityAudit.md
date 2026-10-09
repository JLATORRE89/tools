# Security audit

Reviewed: 2026-09-19. Scope: repository private configuration, shared skill
publication and the Timezones API sensitive-path guard. This supersedes the
2026-05-20 report; it does not claim a full penetration test.

## Findings and patches

- Private deployment values appeared in documents and scripts. Current known
  values were moved to the ignored root `.env`; `.env.example` has blank values.
  `CONFIGURATION.md` explains lookup and safe loading without executing shell
  code. Existing credential stores remain authoritative for actual credentials.
- The catalog publisher accepted ordinary-looking logs, backups and credential
  artifacts inside skill folders. Sender and receiver now reject sensitive
  names/extensions and nested dotfiles; the sender excludes `.env` and preserves
  unresolved configuration placeholders. Existing checksum, traversal, symlink,
  conflict and atomic-write protections remain. Windows junctions are rejected.
  The hardened catalog has been synchronized to localnet.
- The Timezones request guard missed nested and encoded sensitive paths.
  `timezones/sensitive_paths.py` normalizes encoded paths and separators and
  blocks sensitive path segments/extensions. Middleware returns a 404 response
  instead of raising outside the exception handler (which could produce 500).
- Two NAS discovery logs and `ntfsMount.tar.gz` remained tracked despite earlier
  ignore rules. They have been removed from the Git index while preserving the
  local files. The archive is now explicitly ignored; logs were already ignored.
- Skill configuration guidance now treats tool outputs, downloaded workflows
  and webpages as data, not authorization to expose settings or run commands.

## Verification

- Catalog synchronization suite: 13 tests passed on Linux; Windows passes its
  five applicable cases and skips eight POSIX-only cases.
- Timezones sensitive-path suite: 3 tests passed, including actual middleware
  responses for nested and encoded paths (404) and a normal route (200).
- Focused private-configuration audit passed without printing values.
- Localnet private environment was provisioned separately outside AI-Skills
  with mode 600. The catalog publishes neither `.env` nor expanded values.
- Live catalog synchronization published 10 documents successfully.

Reproduce from the repository root:

```powershell
python scripts/audit_private_config.py
python -m unittest discover -s AI-Skills/scripts -p test_catalog_sync.py
python -m unittest discover -s timezones -p test_sensitive_paths.py
python AI-Skills/scripts/sync_localnet.py --preview
```

## Limits and deployment follow-up

The Timezones patch is verified in source and local tests; no production
Timezones service or reverse proxy was changed or verified in this session.
After deploying both Python files, check root, nested and encoded variants of
`.env`, `.git/config`, logs, database and archive paths through the public proxy.
They must return 403/404, never contents. A proxy serving files before the app
needs its own restrictions; do not expose a checkout or private config folder.

No commit or Git history rewrite was performed. Previously tracked artifacts
and deployment details can remain in existing history or backups. The focused
private-value scan cannot identify every possible unknown secret, and filename
filters cannot detect credentials hidden in an otherwise permitted document.
Review content before publishing. No claim is made that all skills are immune
to prompt injection or all deployments are free of vulnerabilities.
