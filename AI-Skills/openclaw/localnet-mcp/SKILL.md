---
name: openclaw-localnet-mcp
description: Connect or troubleshoot the ThinkPad OpenClaw gateway and localnet MCP tools, including ComfyUI image/video job access.
---
# OpenClaw localnet MCP

OpenClaw runs on ${OPENCLAW_HOST} (ThinkPad), while model/render services
run on localnet${LOCALNET_HOST}. Do not confuse their loopback addresses.

Read [connection details](connection.md) for installed paths, verification and
rollback. Prefer `openclaw mcp probe localnet` and `openclaw mcp reload` before
restarting the gateway. Inspect CLI help for installed-version syntax. Keep
Telegram credentials/pairing and unrelated sessions unchanged.

For renders use [ComfyUI rendering](../../comfyui/render/SKILL.md). Tool discovery
alone is not a completed render: verify an actual MCP call and completed job.
The Telegram local model now has verified native tool calling. Its OpenVINO API
accepts tool schemas, parses Qwen calls and replays tool results. The provider
compatibility flag supportsTools=true is necessary but is not proof by itself.

Account/provider deployment procedures are in
[Local AI Stack deployment](../../local-ai-stack/deploy/SKILL.md).
Install the ComfyUI skill AND its scripts under the gateway workspace's
`skills/comfyui-render`; syncing the localnet catalog alone does not install
an OpenClaw skill. A localnet-to-ThinkPad timeout is not proof the gateway is
offline: check the supervising workstation's existing authorized connection.
After deployment compile the helper, compare hashes and download an isolated
owned fixture with gateway TLS/env settings. Remove only that test file/asset.
Do not send Telegram test messages unless included in the user's authorization.
