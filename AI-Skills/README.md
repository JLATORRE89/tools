# Shared AI skills

Task-specific instructions organized by vendor. Agents working in the projects on this workstation can use this catalog to select a skill and read its full instructions only when needed.

## Catalog

| Vendor | Skill | When to load | File |
| --- | --- | --- | --- |
| Cloudflare | Shared DNS management | Inspect or configure a project's DNS, or diagnose a website outage where DNS may be involved, using Jason's existing operator access. | [cloudflare/dnsSKILL.md](cloudflare/dnsSKILL.md) |

## Load a skill when needed

1. Read the target project's agent instructions and scan this catalog's descriptions at task start. Recheck the catalog if the task changes.
2. When the user names a skill, or a description matches the work, open that skill's file before following its workflow. For example, a DNS task loads `C:/Projects/tools/AI-Skills/cloudflare/dnsSKILL.md`.
3. Read additional references or scripts only when the selected workflow needs them. Resolve relative links against the skill file's directory. Do not load the whole library.
4. Briefly tell the user which skill you are using. Reuse instructions already read in the current task unless the file changes.
5. Continue within the user's existing authorization. Reading a skill does not authorize unrelated changes. User instructions take precedence over skill guidance, subject to the agent's higher-priority instructions.

If no description matches, continue with the project's normal workflow. If a required skill is missing or inaccessible, report the specific missing path and continue independent work; do not claim to have used it.

## Add another vendor or skill

- Create a vendor folder, such as `microsoft` or `aws`, when adding its first skill.
- Put each workflow in a descriptive file such as `<topic>SKILL.md`. Include a stable `name`, a clear `description`, and the workflow, following the existing DNS file's frontmatter format.
- Add a row to the catalog with a precise trigger and a relative file link. Update the row when renaming or moving a skill.
- Keep credentials out of this library. Reference existing authorized access in the relevant skill.

New catalog entries become available through the existing project references; individual projects do not need a new instruction block for each vendor.

## Agent integration

The project-root `AGENTS.md` files under `C:/Projects` link to this catalog. This setup relies on an agent reading those instructions and having filesystem access to this library. For a new project, add the same `Shared AI skills` block to its `AGENTS.md`. Agents running on another machine need access to a corresponding copy and paths adjusted for that machine.

The vendor files are loaded through explicit file references. Codex's native skill discovery uses a directory containing `SKILL.md` in a recognized skill location; a custom name such as `dnsSKILL.md` does not register itself in the skill picker. See [OpenAI's skill documentation](https://learn.chatgpt.com/docs/build-skills).

Start a new agent session to pick up changed startup instructions. Other agent applications must be configured to read `AGENTS.md` or explicitly pointed to this catalog. See [Codex instruction discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

## Localnet copy

A Linux-adapted catalog is installed at `/ai/tools/AI-Skills/README.md` on `ssh localnet`. Jason's Claude and Codex startup instructions on that host point to it. The Windows task `AI-Skills Sync to localnet` updates the catalog every 15 minutes and at login while Jason is signed in and localnet is reachable. Windows is the source of truth; unexpected edits on localnet stop synchronization for review. See [localnet setup notes](LOCALNET.md) for operation, backups, and the configured DNS operator connection.
