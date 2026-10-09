# Account ComfyUI access and retailer fallback

Open **Account & Developer ? Open ComfyUI**, or the button in the Developer section. Every signed-in account with image generation can use this workspace; developer approval is not required. The account service checks image eligibility on each request. The shared administrator editor remains separate.

The account editor starts with Photographic scene and offers eight local XPU templates. Edit the prompt, negative prompt, seed, steps and image size. Rendering uses the authenticated GPU worker and retains existing plan, storage and scheduling controls. Arbitrary custom nodes or changes to model families require administrator-reviewed templates. This is not unrestricted access to the host's ComfyUI process.

History, workspace settings and saved workflow files are isolated by account. Workflow files are uploaded through the quota-controlled storage API. Render results stay in protected account storage and can be viewed in ComfyUI or Account ? Storage. Installed models are shared service resources, not copies charged to each user. The native editor uses same-origin login cookies; use the service's HTTPS entry point for protected network access.

## Automatic retailer fallback

Product preview in chat and the authenticated application API first reads a public HTTPS product page. If Walmart, Belk or Amazon cannot supply product images, it tries configured image search. Tracking query parameters are excluded from the derived search. Candidates are alternatives, not verified matches: users must select the correct product and color before rendering. Existing URL validation and bounded image downloads remain active.

Configuration: `/etc/gpu-worker-workflows/product-search.json`:

```json
{"version":1,"enabled":true,"provider":"brave","api_key_env":"GPU_PRODUCT_SEARCH_API_KEY"}
```

An operator must provision `GPU_PRODUCT_SEARCH_API_KEY` in the protected WebUI service environment (currently `/etc/gpu-webui.env`), retain its existing restrictive permissions, and restart `open-webui`. Keep the secret out of JSON, source, chat and browser code. JSON edits are read on the next search; environment changes require a restart. A JSON file configures the adapter; it does not create a provider subscription or key.

Current deployment has no provider key and keeps search disabled. Blocked-page imports explain that a provider is needed and offer a direct photo URL or upload. Real-provider search has not been verified. To roll back the feature activation, set `enabled` to false; direct links and uploads remain available.
