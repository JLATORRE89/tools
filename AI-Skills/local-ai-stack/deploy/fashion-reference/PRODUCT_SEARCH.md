# Clothing image search configuration

Product-page imports and direct HTTPS image links work without a search provider.
Retailer pages can block automated requests. Image search is an optional fallback;
results are not guaranteed to match the exact product, seller or color.

The operator configuration is `/etc/gpu-worker-workflows/product-search.json`. Override its location
with `GPU_PRODUCT_SEARCH_CONFIG` in the Open WebUI service environment. Start with
`deploy/product-search.json`. It is disabled until a provider is configured:

```json
{
  "version": 1,
  "enabled": false,
  "provider": "brave",
  "api_key_env": "GPU_PRODUCT_SEARCH_API_KEY"
}
```

Create a Brave Search API account with image-search access. Put the API key in the
existing protected Open WebUI environment file as `GPU_PRODUCT_SEARCH_API_KEY`.
Never put the key in this JSON, source control, browser JavaScript, or chat.
Set `enabled` to `true` and restart Open WebUI after changing its environment.
JSON changes are read on the next search. The JSON alone does not create a
provider account or supply credentials. Prompt-tag and fashion-workflow JSON
files configure different features and cannot supply image-search results.

Authenticated clients call `POST /api/v1/gpu-api/products/search` with
`{"query":"men's blue straight leg jeans"}` and their scoped connection key.
The account must allow image generation. Results include `images` and `results`
with `image`, `source`, and `title`. Let the user select the correct item before
calling `/products/image` with its URL. That route validates destinations,
downloads and normalizes the image. A disabled or unavailable search returns an
actionable error; it does not silently substitute a different garment.

Without a provider, open the retailer page yourself and use **Copy image address**
on its product photo, or upload a photo. Retailer anti-bot pages are not bypassed.
