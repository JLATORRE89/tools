# Local Qwen tool calling

The managed OpenVINO API now accepts tool schemas and tool-result history,
uses the native chat template, and converts Qwen XML/JSON calls into OpenAI
`tool_calls` (including streamed deltas). Unknown tools and incomplete calls
fail closed. Four parser regression tests cover typed arguments, JSON calls,
ordinary text and malformed/unknown calls. Tool executors remain responsible
for validating arguments and enforcing their existing permissions.

Resolve host settings from the tools root CONFIGURATION.md and ignored .env.
The companion module belongs beside the managed API module on the model host.
`integration.patch` records the installed API changes; inspect compatibility
and back up the installed file before applying it to another version. It is
not an automatic deployment script. Restart only the model API after a change.
Run `python -m unittest test_openvino_tools` from this folder.

Verified 2026-09-19: a real local Qwen tool call and replayed tool result passed.
OpenClaw's targeted Telegram session then called the local MCP video inventory
with provider localnet, without a cloud fallback. Only after those checks was
`models.providers.localnet.models.0.compat.supportsTools` set to true. The
existing model choice, Telegram credentials and pairing policy were preserved.

## Performance update (2026-09-19)

performance.patch adds two scoped changes to the managed model server:
- stop generation after a complete tool-call delimiter, retaining the closing
  marker so the strict parser can validate it; no malformed-call acceptance.
- optional OPENVINO_COMPILE_CACHE disk cache, configured through a restricted
  service environment file. The model still unloads between requests to leave
  GPU memory available for rendering. The first cache build is slow; subsequent
  loads reuse compiled artifacts. Clear/rebuild after incompatible runtime/model changes.

The controlled native weather-tool benchmark returned the correct US location
with actual temperature/rain data. With warm disk cache, tool generation took
3.68 seconds and result summarization 5.19 seconds, versus about 49 + 15.5
seconds before caching. The weather lookup took about 1.1 seconds. This is a
local API benchmark, not a fresh Telegram end-to-end latency measurement.

Large Wan video rendering left substantial idle CPU memory in ComfyUI; sharing
the same AI memory slice with chat caused an OOM kill during an initial test.
Idle test state was cleared and both services restored. Memory limits were
retained; do not solve GPU contention by blindly disabling their safeguards.
