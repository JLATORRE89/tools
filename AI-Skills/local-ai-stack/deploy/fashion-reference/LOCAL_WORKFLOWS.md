# Local workflows and Fashion controls

In **Account & Developer > Account > Plugins**, enable **Fashion** to show
**Add clothing from a link** directly above the chat message box. This is saved
in the signed-in user's WebUI settings and is off until enabled. Turning it on
does not change plan permissions, upload quotas, or GPU admission controls.

Opening ComfyUI through the account entry page loads **Local XPU starter**.
It uses the installed DreamShaper checkpoint with no LoRA and a complete landscape
prompt. The previous graph is retained as a separate workflow by the frontend;
a session backup is also stored as `local-ai-previous-workflow` in sessionStorage.
Saved templates are not deleted. The **Local XPU starter** button opens it again.
Local starter and Video Cutter JSON files are in the ComfyUI workflows folder.

**Video Cutter** opens a standalone workflow. Select **Choose my stored video**,
choose a video previously uploaded through Account > Storage, set comma-separated
spoken marker keywords, and press **Run**. Status appears inside the node. Results
are in Account > Storage. Video segments and Flowblade XML require matching marker
pairs; a recording without suitable markers may produce only subtitles.
This is marker-based editing, not an unrestricted visual timeline editor.

The frontend uses `/api/v1/gpu-cutter/jobs` and its job-status route with native
WebUI authentication. The backend derives ownership from the signed-in account,
forwards to `gpu_video_api_package` on the asset's storage node, and preserves
worker permission, admission and storage checks. Credentials are never saved in
workflow JSON. The Flowblade cutter remains a separately deployed proprietary
module; this addon contains only the bridge. Its current advertised backend is
CPU, not GPU; GPU inference uses the local XPU through ComfyUI.

Deployment: `deploy/comfy-local-workflows` is a ComfyUI custom frontend extension.
Copy it to `custom_nodes/local_ai_workflows` and restart only when idle.
The account bridge ships in the GPU worker WebUI addon. The ComfyUI account-entry
URL includes `local_starter=1`. The stock service is launched with
`--disable-api-nodes`; cloud-provider templates cannot execute. Templates requiring
uninstalled models still need a compatible installed model; they are not silently
rewritten. Do not add `--cpu` or change existing CPU/RAM reservations.

Verification on 2026-09-20: account toggle persisted, disabled button absent,
button docked immediately before the composer form, starter graph loaded and
rendered successfully on Intel XPU, Video Cutter node loaded, authenticated worker
cut produced a video segment/SRT/Flowblade XML. Proprietary source stays separate.

Rollback: restore the previous wheel and `defaultWorkflow.json` from the deployment
backup, remove the newly added custom extension and `local-only.conf` service
override, reload systemd, and restart the idle service. Preserve user workflows.
