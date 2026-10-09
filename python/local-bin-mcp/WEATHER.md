# Country-aware weather tool

weather_mcp_tools.py registers get_weather on the existing local MCP server.
It uses Open-Meteo geocoding with an explicit country filter for five-digit US
ZIPs, returns clarification choices for ambiguous locations, and returns a
compact current/three-day forecast. A ten-minute bounded cache avoids repeated
fetches. No search-provider API key is needed. HTTPX is already a runtime
dependency. Open-Meteo is an external data API; preserve source attribution
and follow its usage terms (personal/noncommercial endpoint versus commercial
service). No upstream source or forecast dataset is redistributed here.

Source and documentation: https://open-meteo.com/en/docs/geocoding-api and
https://open-meteo.com/en/docs .

Tests: python -m unittest test_weather. Covers US ZIP filtering, wrong-country
rejection, ambiguity and cache reuse. Installed MCP discovery reports 12 tools;
existing ComfyUI and private Cutter registrations are preserved.

OpenClaw's local-weather skill is installed for main and visible to the model.
Only the authorized Telegram sender has web_search denied, because no provider
was configured. Country defaults and clarification behavior follow this user's
choice. The gateway hot-reloaded this policy; no gateway restart was needed.
