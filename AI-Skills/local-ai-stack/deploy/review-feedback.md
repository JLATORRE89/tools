# Lessons from the 2026-09-19 deployment review

Read for Local AI Stack implementation, review and deployment work. These are
observed corrections, not a substitute for reviewing the current code.

## Regressions the first review missed

- Monopoly's probe already returned the badge to maximum. Its caller then used
  the old pre-probe value and tapped again, potentially resetting to x1. Return
  immediately after success. A failed probe cannot use an old cached value to
  tap through a newly appeared popup. Confirm the maximum before rolling.
- Tests originally asserted the erroneous extra tap. Check the user-visible
  invariant, not whether a mock repeats implementation behavior. Include a
  caller-plus-probe regression and interrupted-probe behavior.
- OAuth callback tests manually supplied an Authorization header. A real Google
  browser redirect cannot send WebUI's localStorage token that way. The minimal
  GET callback page must complete an authenticated POST; test browser navigation.
- SELECT followed by DELETE was called atomic without a transaction that locks
  before the SELECT. Use BEGIN IMMEDIATE or an atomic SQL operation and test
  competing state consumers. Sequential replay tests do not cover the race.
- Google sign-in must leave the account iframe using top-level navigation.
  Validate resumable-upload destinations before streaming private data. A
  resumable endpoint does not mean the client implements interrupted retries.

## Completion and communication

- A green delegated review can miss defects. Inspect diffs and reproduce the
  intended user flow before accepting it. Distinguish tests, live deployment,
  real-provider validation and blockers in reports.
- Missing Google OAuth configuration blocks activation, not deployment of an
  intentionally disabled feature the user asked to install. Do not invent an
  extra approval step for already authorized reversible deployment.
- Localnet could not SSH to the ThinkPad, but the supervising workstation's
  existing authenticated connection worked. Report the failed route accurately;
  do not generalize it into "the gateway is offline."
- Compile even small Python changes. A permission-hardening edit in primary
  review omitted a colon; a real gateway download caught it. Primary review
  needs tests too.
- Use neutral account-status copy. Preferred disabled developer message:
  "Developer access isn’t currently enabled for your account. You can request
  access below." Keep accurate internal audit states; user-facing wording does
  not need to imply blame or disciplinary action.
- Keep account/storage UI focused on what users can do and who can access
  their files. Keep API authentication, manifests and ownership-check mechanics
  in developer documentation unless they help the user make a decision.
- Synchronize reviewed remote source back to its Windows project and update
  relevant shared skills. Skills are instructions, not trained model weights.
  Do not claim RAG availability without verifying index ingestion and retrieval.

Never copy credentials, private deployment values, account tokens or user media
into these lessons. Preserve the project's protected configuration conventions.

Product language: describe plans as resource-based compute access rather than
monthly token allowances. Explain CPU, RAM, shared GPU capacity and separate
storage allowances in a help section. Do not imply unlimited context, guaranteed
GPU shares or active dedicated workspaces while those remain unimplemented.

WebUI browser regression: current browser completions may send message IDs without a messages array. Early image-intent hooks must read the owner-checked saved branch, not assume direct-API fixtures reflect browser payloads. Verify both ordinary text chat and an image-edit command using the browser after routing changes. Endpoint health and synthetic messages arrays are insufficient.
