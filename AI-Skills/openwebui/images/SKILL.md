---
name: openwebui-local-images
description: Diagnose or restore local Open WebUI picture generation through the existing ComfyUI pipeline, including Image-control routing and missing prompt errors.
---
# Open WebUI local images

Localnet ${LOCALNET_SSH_TARGET} serves WebUI8080, ComfyUI8188, ComfyUI job API8770
and MCP8765. Read [repair notes](repair.md) before changing installed code.

Check service readiness, test1 permissions and configured image workflow.
Start the existing ComfyUI service with ~/bin/startComfyUI.sh when needed;
it checks Intel XPU availability and keeps existing memory limits.

The explicit Image control must execute the configured ComfyUI image workflow
independently of native tool calling by the selected text model. A configured
checkpoint is the renderer; changing the chat model is not a replacement for
connecting the image pipeline. Preserve normal text-chat model defaults.

Verify through both /api/v1/images/generations and the saved chat completion
path with image_generation=true. Confirm persisted image attachments and a
visible image, not merely HTTP200 or generated function-call text. If stored
chat history has no current user prompt, fall back to submitted messages.

Local AI Stack is an instruction skill in WebUI's skill table. Active does not
mean attached to every model. Recommend it for local assistant models; do not
silently impose its local-only preference on unrelated/cloud models.

For package/account addon deployment and native quotas, use
[Local AI Stack deployment](../../local-ai-stack/deploy/SKILL.md).
Keep the account navigation addon and startup restoration in packaged updates.
Check model-specific prompts/tool IDs independently: renaming a contaminated
model row does not fix incorrectly attached Video Cutter instructions.
