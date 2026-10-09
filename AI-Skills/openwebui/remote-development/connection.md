# Connection choices and current status

As inspected 2026-09-19, localnet has desktop VS Code and the installed Open WebUI
package contains routers/terminals.py and utils/terminals.py. This does not prove
that a terminal connection is configured. No code-server/OpenVSCode system
service was found. This skill does not claim an editor or execution backend has
been deployed, connected, or tested.

For coding directly in Open WebUI chat, its Open Terminal integration supplies
workspace files and command tools. Configure the dedicated admin integration,
keep its API key server-side, and restrict which users may access the workspace.
Use a model with tested native tool calls. Inspect the installed version before
following newer documentation or changing settings.

For a browser editor, Open WebUI Computer supplies an editor, terminal, Git and
AI workspace and can integrate as a provider in Open WebUI. If the requirement
is specifically the VS Code interface/extensions, evaluate code-server instead.
Choose the interface before installing a second backend unnecessarily.

Keep the service private and authenticated, with only intended project folders
accessible. A workspace path in a prompt does not constrain shell access. Use
an appropriate OS account or isolated runtime to enforce the actual boundary.
Do not mount SSH credentials or deployment secrets into a general coding workspace.
Store private endpoint settings outside the published skill catalog.

Acceptance test after setup: open a disposable project in the browser, have the
AI read it, make one small change, verify the same edit appears in the editor,
and run a focused test. Verify other WebUI users cannot access the workspace.

Official references:
- https://docs.openwebui.com/features/open-terminal/setup/connecting/
- https://docs.openwebui.com/ecosystem/computer/
- https://coder.com/docs/code-server/guide
