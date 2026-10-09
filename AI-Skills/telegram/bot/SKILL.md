---
name: telegram-local-bot
description: Maintain Jason's OpenClaw Telegram bot, its bounded local-model history, ComfyUI rendering skill, and private Open WebUI conversation mirror.
---
# Telegram local bot

Bot: @${TELEGRAM_BOT_USERNAME}. Authorized DM${TELEGRAM_DM_ID}. Session:
`agent:main:telegram:direct:${TELEGRAM_DM_ID}` on ThinkPad ${OPENCLAW_SSH_TARGET}.

Read [operations](operations.md) for history, mirror services and verification.
For render requests use [ComfyUI rendering](../../comfyui/render/SKILL.md).
For connection diagnosis use [OpenClaw MCP](../../openclaw/localnet-mcp/SKILL.md).

Keep existing Telegram credentials, pairing policy and unrelated sessions.
The DM intentionally uses localnet/qwen3.5-9b-int4 with verified tool calling.
The installed comfyui-render skill is model-visible and user-invocable. Use it
for natural-language picture/video requests; preserve one job per request and
pending job IDs.

For context timeouts inspect session overrides and provider timeout first.
HistoryLimit=0 means unlimited in the installed runtime; use the existing
DM-specific historyLimit=1 for a small recent-turn window. Archive transcripts
before resetting only the targeted session. Stored Telegram/WebUI history is
separate from the prompt window.

Verify inbound and outbound separately. A CLI-generated outbound pong is not
proof that a fresh incoming Telegram message was handled. Ask the user for an
actual test only when that missing inbound event blocks final verification.
