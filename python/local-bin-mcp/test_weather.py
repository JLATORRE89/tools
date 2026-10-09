import asyncio
import unittest
from unittest.mock import patch

import weather_mcp_tools as weather


class Response:
    def __init__(self, value): self.value = value
    def raise_for_status(self): pass
    def json(self): return self.value


class Client:
    calls = []
    places = []
    def __init__(self, **kwargs): pass
    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass
    async def get(self, url, params):
        self.calls.append((url, params))
        if "geocoding" in url:
            return Response({"results": self.places})
        return Response({"timezone": "America/New_York", "current": {"temperature_2m": 70},
            "current_units": {}, "daily": {"time": ["2026-09-19"], "temperature_2m_max": [75]}, "daily_units": {}})


class WeatherTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        weather._cache.clear()
        Client.calls = []
        Client.places = [{"name": "Example", "admin1": "State", "country_code": "US", "country": "United States", "latitude": 1, "longitude": 2}]

    async def test_zip_country_filter_and_cache(self):
        with patch.object(weather.httpx, "AsyncClient", Client):
            result = await weather.get_weather("12345")
            self.assertEqual(result["country_code"], "US")
            self.assertEqual(Client.calls[0][1]["countryCode"], "US")
            self.assertTrue((await weather.get_weather("12345"))["cached"])
            self.assertEqual(len(Client.calls), 2)

    async def test_wrong_country_never_silently_used(self):
        Client.places[0]["country_code"] = "DE"
        with patch.object(weather.httpx, "AsyncClient", Client):
            self.assertEqual((await weather.get_weather("12345"))["status"], "needs_clarification")
            self.assertEqual(len(Client.calls), 1)

    async def test_ambiguous_city_asks(self):
        Client.places.append({**Client.places[0], "admin1": "Another state"})
        with patch.object(weather.httpx, "AsyncClient", Client):
            self.assertEqual((await weather.get_weather("Example"))["status"], "needs_clarification")


if __name__ == "__main__":
    unittest.main()
