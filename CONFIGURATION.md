# Private deployment configuration

The repository already has a `.gitignore`. It ignores `.env` and private `.env.*`
variants; `.env.example` is a tracked template with blank values. Real deployment
addresses, usernames, chat IDs and installation paths belong only in `.env` or
the environment of the deployed service. Existing credential stores remain the
source for passwords, API tokens and SSH private keys; do not copy those into docs.

Copy `.env.example` to `.env` on a new authorized checkout and fill the needed
keys privately. Environment variables override `.env`. Set `TOOLS_ENV_FILE` if
the private configuration is outside this checkout. Never commit, log or paste
its contents. A `${KEY}` reference in Markdown is a lookup instruction, not a
literal command to run without loading that setting first.

Python scripts can add the repository `scripts` directory to `sys.path`, then:

```python
from repo_env import load_env, require
load_env()
ssh_target = require('LOCALNET_SSH_TARGET')
# Pass values as argument-list entries, not interpolated shell commands.
```

`python scripts/repo_env.py` checks presence without printing values.
`python scripts/audit_private_config.py` checks tracked/new publishable text for
known private deployment values and accidental credential-file inclusion.
It is a focused guard, not a guarantee that every possible secret is detected.

## Where to look

| Need | Keys |
| --- | --- |
| Local model/ComfyUI host | LOCALNET_HOST, LOCALNET_SSH_TARGET, LOCALNET_SSH_ALIAS |
| OpenClaw gateway host | OPENCLAW_HOST, OPENCLAW_SSH_TARGET |
| Host-local installation paths | SERVICE_USER_HOME, OPENWEBUI_PACKAGE_DIR |
| Telegram conversation | TELEGRAM_DM_ID, TELEGRAM_BOT_USERNAME |
| Private WebUI archive channel | TELEGRAM_WEBUI_CHANNEL_ID, LOCALNET_HTTPS_URL |
| ComfyUI/MCP endpoints | COMFYUI_JOB_API_URL, LOCALNET_MCP_URL, OPENCLAW_MCP_URL |
| Catalog synchronization | AI_SKILLS_REMOTE_ROOT, LOCALNET_SSH_ALIAS |
| DNS operator checkout | DNS_OPERATOR_CHECKOUT, DNS_LOCAL_CHECKOUT, DNS_SSH_ALIAS |

Host-local paths refer to the host that runs that service. Do not interpret a
remote home directory as a path on the Windows workstation. Populate machine-
appropriate values per deployment. Code should use `Path.home()` for the current
account where possible.

The AI-Skills sync publishes portable docs with unresolved `${KEY}` references.
It must not publish `.env`, expand private values into docs, or include credentials.
Provision private settings separately over the existing authenticated connection.
The private localnet copy belongs at the tools checkout root, outside AI-Skills.

The installed OpenClaw skill copy is a deployment artifact. Its source of truth is
`AI-Skills/comfyui/render/SKILL.md`. Service configuration can resolve real endpoint
values at deployment; it must not be copied back into tracked examples.

These changes remove current hardcoded values; they do not rewrite Git history.
