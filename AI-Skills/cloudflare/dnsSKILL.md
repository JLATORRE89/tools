---
name: shared-cloudflare-dns
description: Manage project DNS using Jason's existing Cloudflare operator access through ssh emailreseller. Use for domain record inspection, scoped DNS changes, and DNS diagnosis during website outages in projects on this workstation.
---

# Shared Cloudflare DNS

## Existing access

- Use the configured OpenSSH alias `ssh emailreseller`; do not use scripted passwords or temporary password files.
- The Cloudflare API token is on that server at `~/.config/email-reseller/cloudflare-api-token`. Use it there, in memory. Never print it, include it in command arguments/logs, or copy it into another project or workstation file.
- Token file permissions should be 0600 with parent directory 0700. Verify presence and permissions without displaying contents. Verify access to the requested zone; access to one zone does not establish access to all domains.
- Reference implementation: `C:/projects/emailresellerserver/scripts/onboard_domain.py`.
- Operator documentation: `C:/projects/emailresellerserver/docs/DOMAIN_ONBOARDING.md`.
- Production checkout: `/home/jason/email-servers/emailresellerserver`.

Read the relevant reference before using its commands. The onboarding CLI combines DNS with mail provisioning; it is not a general website DNS CLI. For website-only tasks, use scoped Cloudflare API operations on the SSH server rather than mail-onboarding `apply`. Consult current official Cloudflare API documentation for operations being implemented.

## Workflow

Read the target project's `AGENTS.md` and `TASKS.md`, then log the task before substantial work. Identify the domain and hosting destination from that project's configuration. The email server is the DNS operator host, not necessarily the website origin.

Inspect the exact zone and relevant existing records, including pagination, record IDs, TTLs, and proxy settings. Prepare a concrete before/after plan. A request to inspect DNS authorizes inspection; a request to fix or configure it may already authorize the necessary scoped changes. Use existing session authorization without repeatedly asking for approval. Loading this skill alone does not authorize mutations.

For authorized changes:

- Save the affected records and intended changes in a protected remote journal before writing; keep credentials out of it.
- Preserve unrelated records, especially MX, SPF, DKIM, DMARC, verification records, and existing mail-host proxy settings.
- Recheck the affected records before applying. Stop and replan on conflicting concurrent changes rather than overwriting them.
- Apply only the necessary changes, reuse matching records, and preserve attributes that are not part of the request.
- If a write times out or its result is uncertain, read back the actual state before retrying. Do not blindly repeat record creation or deletion.
- Retain enough before/after state for targeted rollback. Roll back only your changes and only if the live record still matches your applied state.

Do not expand token permissions, create zones, change registrar nameservers, or provision mail unless required and authorized by the current task. If access is missing, report the specific missing zone/permission without exposing credentials.

Verify the API result and public DNS. For proxied website records, public A/AAAA answers show Cloudflare addresses; verify the configured origin through the API. Verify HTTPS when relevant and distinguish propagation delays from failed changes. Record completion or handoff, changed files/records, validation, and remaining blockers in the target project's `TASKS.md`.

## Website outages

A 502 is not sufficient evidence of incorrect DNS. Check public resolution, TLS, proxy routing, origin response, and application service availability before changing records. Derive SSH access and ports from the target project's deployment configuration.

If the application uses a systemd user service, inspect its logs and `loginctl show-user <site-user> -p Linger`. A service that runs only during SSH sessions may stop after logout. When repairing that lifecycle issue, verify the public endpoint after disconnecting; a successful request during an SSH session is insufficient.
