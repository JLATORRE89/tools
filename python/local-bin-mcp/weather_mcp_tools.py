"""Bounded, country-aware weather lookup without an unconfigured search provider."""
import asyncio
import copy
import re
import time

import httpx

_cache = {}
_lock = asyncio.Lock()


async def get_weather(location: str, country_code: str = "") -> dict:
    """Current weather and three-day forecast. Bare five-digit ZIPs default to US.

    Use an explicit two-letter country code for another country. Ambiguous
    matches return needs_clarification; ask the user rather than guessing.
    """
    location = location.strip()
    country_code = country_code.strip().upper()
    if not 2 <= len(location) <= 100 or (country_code and not re.fullmatch(r"[A-Z]{2}", country_code)):
        raise ValueError("Provide a city/postal code and optional two-letter country code")
    if not country_code and re.fullmatch(r"\d{5}", location):
        country_code = "US"
    key = (location.casefold(), country_code)
    async with _lock:
        cached = _cache.get(key)
        if cached and time.monotonic() < cached[0]:
            result = copy.deepcopy(cached[1])
            result["cached"] = True
            return result
        async with httpx.AsyncClient(timeout=12, trust_env=False, follow_redirects=False) as client:
            params = {"name": location, "count": 3, "language": "en", "format": "json"}
            if country_code:
                params["countryCode"] = country_code
            response = await client.get("https://geocoding-api.open-meteo.com/v1/search", params=params)
            response.raise_for_status()
            places = response.json().get("results", [])
            places = [p for p in places if not country_code or p.get("country_code") == country_code]
            if not places:
                return {"status": "needs_clarification", "reason": "No matching location in the requested country", "country_code": country_code}
            choices = {(p["name"], p.get("admin1", ""), p.get("country_code", "")) for p in places}
            if len(choices) > 1:
                return {"status": "needs_clarification", "choices": [", ".join(c) for c in sorted(choices)]}
            place = places[0]
            response = await client.get("https://api.open-meteo.com/v1/forecast", params={
                "latitude": place["latitude"], "longitude": place["longitude"], "timezone": "auto",
                "temperature_unit": "fahrenheit", "wind_speed_unit": "mph", "precipitation_unit": "inch",
                "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m,precipitation",
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max",
                "forecast_days": 3})
            response.raise_for_status()
            forecast = response.json()
        daily = forecast["daily"]
        result = {"status": "ok", "location": ", ".join(x for x in [place["name"], place.get("admin1"), place.get("country")] if x),
                  "country_code": place["country_code"], "timezone": forecast["timezone"],
                  "current": forecast["current"], "current_units": forecast["current_units"],
                  "days": [{key: values[index] for key, values in daily.items()} for index in range(len(daily["time"]))],
                  "daily_units": forecast["daily_units"], "source": "https://open-meteo.com/", "cached": False}
        if len(_cache) >= 128:
            _cache.pop(next(iter(_cache)))
        _cache[key] = (time.monotonic() + 600, copy.deepcopy(result))
        return result


def register(mcp):
    mcp.tool(annotations={"readOnlyHint": True})(get_weather)
