---
name: local-ai-stack-deploy
description: Review, synchronize and deploy Local AI Stack account, storage, GPU-worker and Open WebUI addon changes on localnet, including remote-agent handoffs and rollback.
---

# Local AI Stack deployment

Read [deployment procedure](deployment.md) for an authorized code deployment.
Read [review feedback](review-feedback.md) for the concrete regressions and
verification gaps found during the latest handoff.
Read [fashion API](fashion-reference/APPLICATION_API.md) and
[clothing search configuration](fashion-reference/PRODUCT_SEARCH.md) when
working on garment imports. That folder contains reviewed Python/JavaScript
client examples synchronized from the deployed package, plus the secret-free
search JSON. Application source remains in the authoritative project checkout.
For MuCache account connections, read [MuCache integration](fashion-reference/MUCACHE.md).
License keys belong in the encrypted per-account vault, never chat or operator
JSON. Search only metadata owned by the connected license and respect cloud-sync
settings; cached metadata is not a general web-search or retailer bypass.
Resolve hosts and credentials through the tools repository's ignored `.env`
and existing protected service environments. Do not embed values into skills.

Windows source is authoritative: the projects workspace's
`gpu_video_api_package` and tools repository. Remote working directories and
Python site-packages are deployment artifacts, not a replacement source tree.
Merge remote changes against their handoff snapshot, preserving subsequent
Windows edits. Copy reviewed source changes back before final packaging.

When the user requests implementation and deployment, a disabled feature may
still be installed with clear unavailable UI. Missing OAuth configuration blocks
activation and provider verification, not installation of tested inactive code.
Do not activate billing, subscriber containers or GPU guarantees merely because
their interfaces or documentation exist.

A delegated review is evidence, not proof. Inspect actual differences and test
the user flow. Report source completion, live installation and end-to-end
provider verification separately. Preserve pending tasks across handoffs.

For the account Fashion switch, docked clothing importer, local XPU starter and proprietary Video Cutter bridge, see [Local workflows](fashion-reference/LOCAL_WORKFLOWS.md).

For eligible-account native ComfyUI workspaces and automatic retailer fallback, see [Account editor and search](fashion-reference/ACCOUNT_COMFY_SEARCH.md). Shared administrator access remains separate. Search activation requires a real provider key; configuration JSON alone is insufficient.
