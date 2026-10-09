# Telegram archive channel

Installed 2026-09-18. Channel: ${LOCALNET_HTTPS_URL}/channels/${TELEGRAM_WEBUI_CHANNEL_ID}

Continue chatting with @${TELEGRAM_BOT_USERNAME} in Telegram. The private Open WebUI
`telegram` channel archives new incoming text and successfully sent replies,
labelled Jason · Telegram and Assistant · Telegram. Only Jason is a channel
member. This is one-way mirroring; messages entered in WebUI do not send to
Telegram. Existing history has not been imported. Attachments receive a text
placeholder where event metadata is available; original files remain in Telegram.

The archive is independent of model context. Telegram DM ${TELEGRAM_DM_ID} remains
pinned to localnet/qwen3.5-9b-int4 with historyLimit=1 (the installed runtime
retains a small recent-turn window, not the full transcript). The 32,768 context
window, 300-second localnet timeout and global OpenAI default are unchanged.
Telegram credentials, pairing policy and unrelated sessions are unchanged.

## Runtime

ThinkPad ${OPENCLAW_SSH_TARGET}:
- Hook: ~/.openclaw/hooks/telegram-openwebui-mirror/{HOOK.md,handler.mjs,handler.ts}
- Config addition: hooks.internal.entries.telegram-openwebui-mirror.enabled=true
- Worker: ~/.local/lib/telegram-openwebui-mirror/worker.py
- User service: telegram-openwebui-mirror.service (enabled)
- Private state: ~/.local/state/telegram-openwebui-mirror/
  config.json contains two secret, channel-scoped webhook URLs; never publish it.
  localnet-ca.pem pins the existing localnet TLS trust, outbox/ stores pending
  messages, sent.sqlite records delivery receipts.
- Logs: journalctl --user -u telegram-openwebui-mirror

The hook only queues the default-account DM ${TELEGRAM_DM_ID}. The worker posts to
native Open WebUI channel webhooks over verified HTTPS. It retries queued
messages after temporary outages; successfully recorded receipts suppress
repeated events. A crash after remote acceptance but before receipt persistence
can cause a duplicate. No new network listener, model call or Telegram polling
client was added. Gateway hook configuration hot-reloaded without a restart.

Localnet backups: ~/.local/state/telegram-openwebui-mirror/webui-before-channel.sqlite
and channels-config-before.json. Channels were enabled if previously disabled.
ThinkPad pre-mirror config backup: state directory/openclaw-before-mirror.json.
Do not restore entire databases/configs over later changes just to disable this.

## Disable

On ThinkPad, with OpenClaw's normal PATH:
    openclaw hooks --agent main disable telegram-openwebui-mirror
    systemctl --user disable --now telegram-openwebui-mirror
This leaves archived messages intact and Telegram replies functioning.
Channel webhooks can be revoked from the channel's WebUI settings if retiring it.

## Verification

Five hook tests and five Linux worker tests passed. Live gateway run
7e483d05-37eb-4731-87cf-9fd093577470 generated pong using localnet in 31.058s,
without fallback or compaction. Telegram message 732 was sent successfully;
worker receipt mapped it to WebUI message 39b278c4-d145-4590-8853-d999604b28e6.
Read-only database inspection confirmed the content and private membership.
A fresh user-originated Telegram ping is still needed to confirm live incoming
message mirroring; inbound normalization/filtering is covered by unit tests.

Weather: [country-aware lookup](../weather/SKILL.md) uses the localnet get_weather MCP tool. Bare five-digit ZIP codes default to the US; ambiguous matches require clarification. It avoids the unconfigured web_search provider.
