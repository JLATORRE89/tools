---
name: character-production
description: Prepare and improve FPSGAME rigged characters using authenticated ComfyUI references, Blender conditioning packs, PBR materials and PC/Quest validation. Use for character asset production and readiness review.
---

# Character production

Work in the FPSGAME checkout. Read its AGENTS.md, RULES.md,
docs/LOCALNET_AGENT_HANDOFF.md and docs/CHARACTER_PRODUCTION_PLAN.md first.
Resolve the project checkout on the current machine; a remote snapshot may lag
the workstation. Keep credentials in the existing private account configuration.

## Choose the actual task

- Local image edit: tools/character_reference.py. New runs take --run, --source
  and --prompt-file; resume with --run only. Inputs and request UUID are saved
  before rendering. tools/account_render.py uploads images, lists workflows,
  submits jobs and downloads owned assets over authenticated HTTPS.
- Consistent source views: run tools/build_character_conditioning.py in Blender
  with --source RIGGED.glb --output NEW_DIRECTORY --size 512, then run
  tools/validate_character_conditioning.py OUTPUT. It creates four color/depth
  pairs, an editable studio and a byte-identical rigged source. It does not improve
  topology. Keep the 16-bit depth masters and camera calibration from the manifest.
- Native authoring: use the existing build_concept_operator.py, anatomical_bind.py,
  character_surface_materials.py and build_quest_operators.py in an isolated
  candidate checkout. These generators write under their checkout's assets tree;
  do not run them against production to experiment.
- Delivery: use existing asset_integration.py profiles, rig/surface validators,
  native pose captures and the owner review interface. Read
  docs/CHARACTER_REALISM_20260923.md for the latest known defects and budgets.

Read docs/CHARACTER_REFERENCE_WORKFLOW.md and docs/CHARACTER_PRODUCTION_PIPELINE.md
for commands and limitations. Check live capabilities instead of inferring support
from a template name. Separate reference/depth guidance and automatic mesh generation
were not advertised at the last check; creating a guide does not add that capability.

## Production acceptance

Capability distinctions confirmed by live tests: `chat-checkpoint-edit` is the
working image-to-image workflow used by character_reference.py. Missing ControlNet
weights do not block that route or Blender pack generation. A 512px pack changes
image resolution only; it contains the SAME source mesh, not a conditioned mesh.
anatomical_bind.py operates on geometry, not generated PNGs. Identity encoders,
LoRAs and ControlNet depth weights have different roles and are not substitutes.
Do not invent a `character-reference` workflow ID or make absent depth weights a
reason to stop independent native mesh work.

Start with the blue female operator; complete one reviewed character before
expanding the cast. Preserve source licenses, editable masters, UVs, gameplay
skeleton, attachment anchors and separately authored collision. Inspect shoulders,
elbows, knees, eyelids, mouth, hair and hand-to-weapon contact in actual poses.
Generated RGB studies are not matching PBR maps or proof of clean topology.
Use the existing Quest triangle/texture budgets and actual device performance gate.

Preserve account ownership, quotas, scheduler and CPU/RAM reservations. GPU jobs
go through account_render.py; never use raw ComfyUI or other credentials to bypass
rejections. Keep shared workflow configuration under /etc/gpu-worker-workflows.
Before installing weights/nodes, verify compatibility, license and available memory.

Keep failed and rejected candidates with reasons. Mark owner approval, native
visual review and headset acceptance separately. No automatic promotion into
production, no claim of production readiness from successful export alone.

## Local model versus tool-enabled agent

The FPSGAME localnet_ai.py helper can load this skill with --skill character-production.
That coding-model call supplies advice only: it cannot execute tools, modify files
or inspect images. A tool-enabled agent must perform and verify the operations.
Do not say this skill trains the model or enables a renderer by itself.
