# Local Open WebUI image route repair — 2026-09-19

Host: localnet / ${LOCALNET_SSH_TARGET}. Open WebUI 0.11.3.

Existing ComfyUI had been stopped since September17. Started it via
~/bin/startComfyUI.sh; Intel Arc A750 XPU confirmed. Existing DreamShaper8
workflow, model files and chat-tool server were preserved.

Installed middleware:
${OPENWEBUI_PACKAGE_DIR}/utils/middleware.py

Changes:
- Explicit features.image_generation forces per-request legacy execution so
  image generation runs independently of native tool-calling support in the
  selected text model. The configured ComfyUI checkpoint produces the image.
- Missing user prompt in stored history falls back to submitted message history.
- Image exceptions log a traceback instead of being hidden at debug level.

A temporary llama31-8b-int4 model-wide legacy override was removed after the
per-request fix. Normal text chats retain their original model configuration.
Open WebUI was restarted to load the middleware. Both backend / and public
HTTPS / returned200 afterward; user confirmed the picture renders in their chat.

Validation:3 isolated prompt regression cases passed. Direct image API as test1
created a visually checked512x512 house image. Full /api/chat/completions with
image_generation=true and explicit function_calling=native generated and saved
image attachments to test1 chat8761c836-735e-486e-b0e3-001b3b408805.

The native Image control creates still images using DreamShaper8. The separate
existing ComfyUI chat-tool video workflow has Wan2.1 T2V1.3B, UMT5 and VAE present
and reports ready; video generation was not retested in this repair.

Backup: ~/.local/state/image-repair-20260919/middleware-before.py and
llama-model-before.json. Patch scripts here record exact changes, but are
one-shot patches, not unattended updaters. A WebUI upgrade can overwrite the
middleware; re-evaluate the patches against the upgraded source and retest.

## Account enforcement update

Native still-image generation now uses the approved worker workflow through
`gpu_video_api.native_webui`, then saves a native attachment under the verified
owner quota. Existing OpenAPI render tools use signed owner delegation through
`legacy_render_bridge`; do not restore direct unauthenticated ComfyUI submissions.
ComfyUI is private and mutation-authenticated. Public model/MCP requests use the
account connection API. See the GPU package docs/NATIVE_INGRESS_USAGE.md for
installation checks, usage history, retained reservations and admission recovery.
Keep the explicit Image-control middleware behavior described above. After an
upgrade test both the image endpoint and chat attachment path again.


## Default model and final check

Qwen 3.5 9B is the configured WebUI default for general chat, coding and
ComfyUI assistance. Model ID remains qwen3.5-9b-int4; native tool calling and
image-generation capability are enabled. Existing conversations and explicit
user model choices are preserved. The final comparison found Qwen more useful
than the installed Llama/TinyLlama variants for ComfyUI node explanations.
A real structured tool-call response and saved-chat PNG were verified; this
is not a claim that arbitrary generated workflows are validated automatically.
Use the current inventory/tools to check exact node schemas before executing.

Change the default through native admin configs/models API (preserving other
settings), not by replacing complete provider configs. Read it back through
the running service. The account portal wording should remain user-focused;
keep advanced API setup in optional details or developer documentation.
