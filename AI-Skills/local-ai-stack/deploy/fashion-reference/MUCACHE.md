# Connect your MuCache account

Open Account settings and find **Connect MuCache**. Enter your own MuCache
license key and click **Connect MuCache**. Enable cloud metadata sync in MuCache
first. The connection is saved only after MuCache accepts a metadata query.
Use **Disconnect** to remove the stored key. Disconnecting here does not cancel
your MuCache license or delete your MuCache metadata.

The key is encrypted at rest with AES-256-GCM, authenticated against your Local
AI Stack account ID. It is never stored in chat, browser storage, URLs or API
responses. A separate, operator-provisioned 32-byte encryption key lives outside
the connection database. Protect and back up both separately; losing the vault
key requires users to reconnect. Host administrators can operate the service
and therefore remain trusted; this is not end-to-end encryption.

In chat, open **Add clothing from a link**, enter search text and choose
**Search my MuCache**. This searches saved metadata belonging to your connected
license. It is not a general web-search engine. Image records provide source
URLs; webpage records go through the existing bounded product-image importer.
Blocked or expired source links may still require an upload. Photos selected
for chat go through normal account upload quotas. No other account's cache is
searched. No MuCache files are downloaded merely by connecting.

## Operator setup

Configure `/etc/gpu-worker-workflows/mucache.json` using `deploy/mucache.json`.
The operator chooses a trusted HTTPS origin; users cannot supply a service URL.
Set `enabled` to true only after deploying the MuCache query endpoint.
`GPU_MUCACHE_CONFIG` can override the JSON location. There are no credentials in
this JSON. Provision `GPU_MUCACHE_VAULT_KEY_FILE` in the protected Open WebUI
environment, pointing to a 32-byte key readable only by the service/operator.
The owner-encrypted database is `gpu-mucache-connections.sqlite3` in WebUI DATA_DIR.
Restart WebUI after changing its environment. Configuration changes are read on
each connection/query. The workflow directory must be traversable by WebUI.

MuCache exposes `POST /api/metadata/query` (also `/meta/api/metadata/query`) with
the license in `X-License-Key`, never a URL parameter. JSON fields are `query`
(up to 240 characters), `limit` (1-50) and `offset` (0-10000). The license must be
valid and unexpired; cloud metadata sync must be enabled. Returns version 1,
items, total, limit, offset. Items include source URL, title, media type and
update time; no notes, local paths, user identifiers or license keys. The endpoint
does not archive/fetch new pages or trigger legacy scans. The pre-existing list
endpoint keeps its browser-session behavior.

The connector does not follow redirects, verifies TLS, caps responses at 512 KiB,
limits concurrent upstream requests to two per process, and sends credentials
only to the configured service. The license itself may authorize other MuCache
features; a future revocable, narrowly scoped integration token would reduce
its authority further. Never ask users to paste keys into chat.

Local account endpoints: GET/PUT/DELETE `/api/v1/gpu-mucache/connection` and POST
`/api/v1/gpu-mucache/query` with `{"query":"blue jeans"}`. These use the native
authenticated WebUI session token, not an owner ID provided in the request.
They are not yet exposed through third-party scoped connection keys or MCP.
