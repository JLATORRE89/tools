# OpenClaw ? localnet MCP ? ComfyUI

Installed2026-09-19. OpenClaw ThinkPad user from ${OPENCLAW_SSH_TARGET} connects to existing localnet
MCP via http://127.0.0.1:18765/mcp using streamable-http. The enabled user unit
openclaw-localnet-mcp-tunnel.service forwards that port over SSH to localnet's
127.0.0.1:8765. MCP remains bound to loopback, with no new LAN/public listener.
The dedicated ~/.ssh/openclaw_localnet_mcp key is restricted on localnet to
port forwarding to127.0.0.1:8765; command execution is denied. Host key was
verified against localnet's live host public key before registration.

OpenClaw config: mcp.servers.localnet, request timeout180s, connect timeout15s.
MCP runtime reloaded via openclaw mcp reload; no gateway restart required.
Backup: ThinkPad ~/.openclaw/openclaw.json.before-localnet-mcp-20260919.

Localnet code: ~/projects/local-bin-mcp/comfyui_mcp_tools.py, registered from
bin_tools_mcp_http.py. Original file preserved as
bin_tools_mcp_http.py.before-comfyui-20260919. Service local-bin-mcp restarted.
Existing three script tools/allowlist were preserved. Five additional tools:
- list_comfyui_artifacts
- list_comfyui_video_artifacts
- generate_comfyui_image
- generate_comfyui_video
- get_comfyui_job

Adapters call existing http://127.0.0.1:8770 API; existing validation, job
isolation and resource guards remain in that service. Generation returns a
job ID; poll get_comfyui_job until completed/failed and use returned HTTPS URLs.
Image defaults:DreamShaper8,512x512,24steps. Video defaults:Wan2.1 T2V1.3B,
512x512,17frames,8fps,20steps. Rendering is local Intel Arc XPU.

Verified OpenClaw MCP probe discovers8tools. MCP calls across the ThinkPad
SSH tunnel generated image jobff48e6d4-0f8b-4050-a8a6-c00c9ef0ef72, completed
in3.49s, no quality failures, outputOpenWebUI-Chat_00003_.png. OpenClaw agent
rune6b8da76-0705-4df9-9143-fa465c462035 independently called
localnet.list_comfyui_video_artifacts successfully; terminal receipt confirms
that exact tool.

A subsequent actual OpenClaw MCP video job completed in 105.34 seconds:
976f0225-9bdd-4ab7-a07b-864396b68b03. Wan 2.1 T2V 1.3B, 256x256,
17 frames at 8fps, 20 steps. ffprobe verified a playable H.264 MP4 (2.125s).
The low-resolution first frame showed distorted architecture/tree shapes;
this proves the render path, not acceptable final visual quality.

The local Qwen API now supports native tools. The Telegram session itself
successfully called localnet__list_comfyui_video_artifacts with localnet as
provider. OpenClaw supportsTools=true; see the tools repository's
python/openvino-tool-calling for protocol source, tests and integration patch.
The comfyui-render skill is installed and eligible for the main agent.


Disable connection: openclaw mcp unset localnet; openclaw mcp reload;
systemctl --user disable --now openclaw-localnet-mcp-tunnel on ThinkPad.
Remove only the openclaw-localnet-mcp authorized_keys line on localnet if retiring
access. Preserve other SSH keys and MCP clients.

The Open WebUI skill named Local AI Stack is separate: model/tool instructions
stored in its skill table, not a network connector. It was inspected, not changed.
