# Build a website on Local AI Stack

Deployed on localnet on 2026-09-20. Retailer compatibility is not yet verified.
Use `/api/v1/gpu-api` on the configured HTTPS service origin. Existing
`/api/v1/gpu-openclaw` clients remain compatible. No chat session is required.

Create an account connection key with `render` and `storage` scopes in account
settings. Send `Authorization: Bearer <connection-key>` from your website's
backend. Keys expire and can be revoked through the existing account controls.
Keep keys in your server's secret environment, never frontend JavaScript.
Your backend authenticates its own users; a connection key represents its
owning subscription account, not every visitor's separate account. To preserve
separate subscriber ownership, each subscriber needs their own connection key.
Do not accept a caller-supplied owner ID or share one key between subscriptions.
Direct cross-origin browser access is intentionally not enabled.

| Method and path (relative to the API base) | Purpose | Scope |
| --- | --- | --- |
| GET `/account` | Current account allowance and entitlements | storage |
| GET `/workflows` | Installed workflow IDs, parameters and reference counts | render |
| POST `/products/preview` | `{"url":"https://shop.example/product"}` → candidate image URLs | render |
| POST `/products/image` | Same JSON with a selected image URL → normalized WebP bytes | render |
| POST `/assets?filename=references.zip` | Raw binary upload → `asset.id` | storage |
| POST `/jobs` | Submit approved workflow; returns job manifest (202) | render; storage for asset input |
| GET `/jobs/{job_id}` | Owned job status and output asset links | render |
| GET `/assets/{asset_id}/content` | Download an owned output | storage |

`POST /jobs` example:
```json
{"workflow":"operator-configured-workflow","values":{"prompt":"Put the shirt, pants and shoes on a mannequin."},"asset_id":"uploaded-asset-uuid","request_id":"stable-request-uuid"}
```
Persist the request UUID before submitting. Reuse it with the exact same payload
after a lost response; do not generate a new ID for a retry. Jobs enter the
existing scheduler and account checks. A 202 means accepted, not completed.
Poll every few seconds and inspect `status`; only use output assets after success.
Errors include 400 invalid input, 401 invalid/expired key, 403 missing scope or
entitlement, 404 inaccessible asset/job, 409 conflicting submission, 413 storage
or upload limit, 422 blocked/unsupported product import, and 429 busy capacity.
Worker failures may return 502/503. Never blindly retry a submission with a new ID.

Fashion workflows with `reference_count` require a ZIP_STORED archive containing
exactly `0.png` through `N-1.png`: RGB PNG images, each at most 1024 pixels per
side and 4 MiB, archive at most 32 MiB, at most eight references. Clothing comes
first; the person photo goes last for try-on. The count must match the workflow.
The example prepares this bundle from selected product image URLs. Single-image
workflows without `reference_inputs` may instead accept an ordinary image asset;
follow the operator's workflow documentation.

Product previews are temporary bytes. Uploading references or saving outputs
uses hosted storage allowance. GPU model weights remain shared infrastructure.
Retailer text is not sent to the model. Images are fetched through the same
bounded public-HTTPS importer as chat, without forwarding account credentials.
Choose the correct product/color from the previews before importing.

The API does not make an absent fashion model available. Only submit workflow
IDs returned by discovery and verified for the intended task. Accurate garment
transfer, identity preservation and billboard layout remain unverified locally.
No renderer or new GPU allowance is activated by this API change.

See `examples/fashion_website.py` for a complete backend-side client. It uses
environment variables `LOCAL_AI_API_BASE` (ending `/api/v1/gpu-api`),
`LOCAL_AI_CONNECTION_KEY`, and `LOCAL_AI_FASHION_WORKFLOW`.
First use `--product URL` to discover candidates. Then use `--image URL` once per
selected garment, plus a stable `--request-id UUID`, to upload, submit, poll and
download the resulting files. Keep the printed bundle asset ID for retries.
Use `--asset-id UUID` to retry without creating another uploaded bundle.

## JavaScript / Node.js

`examples/fashion_website.mjs` is a backend-side JavaScript client with no npm
dependencies. Run it with Node.js 22 or newer and the same three environment
variables described above. It is also listed in the developer area's example
downloads once this source version is deployed. Never place the connection key
in a browser bundle or a public environment variable.

```sh
# Inspect candidate product images; select the correct item and color yourself.
node fashion_website.mjs --product "https://retailer.example/product"

# Download a selected candidate as normalized WebP (does not submit a job).
node fashion_website.mjs --image "https://retailer.example/selected-image.webp" --output shirt.webp

# Upload a prepared bundle, submit, poll and download outputs.
node fashion_website.mjs --bundle references.zip --request-id YOUR_SAVED_UUID --prompt "Put the shirt, pants and shoes on a mannequin."

# Resume an existing job without submitting or uploading again.
node fashion_website.mjs --job-id YOUR_JOB_UUID --output fashion-output
```

Prepare `references.zip` according to the PNG/ZIP_STORED format above. The
JavaScript example deliberately uses a prebuilt bundle instead of adding image
conversion dependencies; simply zipping WebP files will not work. The Python
example can perform conversion and bundle creation. For retries use the printed
`--asset-id` and the same `--request-id`, workflow and prompt. Uploaded reference
assets remain in hosted storage until removed through account storage controls.

You can also import `LocalAI` into a website backend:
```js
import { LocalAI } from './fashion_website.mjs';
const api = new LocalAI(process.env.LOCAL_AI_API_BASE, process.env.LOCAL_AI_CONNECTION_KEY);
const candidates = await api.products(productUrl);
// Return candidates to your signed-in user for selection.
// Upload their prepared bundle, then enqueue a job with a persisted request ID.
```
For production websites, submit from the backend and return the job ID to the
browser immediately; poll through your backend rather than keeping a web request
open for the full render. The CLI waits for convenience. Downloads refuse to
overwrite existing files and never send your key to output URLs supplied by a job.

Direct-image fallback: `/products/preview` also accepts HTTPS PNG/JPEG/WebP image URLs and returns `source_type: image`. When the retailer returns a robot challenge, use Copy image address on the product photo and paste that URL into the picker. The challenge is not bypassed; automatic search discovery is not configured.
