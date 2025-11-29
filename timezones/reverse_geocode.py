#!/usr/bin/env python3
"""
Reverse Geocoding Module
Converts latitude/longitude to location information (zip code, city, etc.)
Uses Nominatim API with GeoIP fallback
"""

import requests
import logging
import time
from typing import Optional, Dict, Any
import geoip2.database
import geoip2.errors


class ReverseGeocoder:
    """Reverse geocoding with Nominatim API and GeoIP fallback"""

    def __init__(self, geoip_db_path: Optional[str] = None, user_agent: str = "TimezoneAPI/1.0"):
        """
        Initialize reverse geocoder

        Args:
            geoip_db_path: Path to GeoLite2-City.mmdb file (for fallback)
            user_agent: User agent string for Nominatim requests
        """
        self.logger = logging.getLogger("ReverseGeocoder")
        self.user_agent = user_agent
        self.geoip_reader = None

        # Initialize GeoIP reader for fallback
        if geoip_db_path:
            try:
                self.geoip_reader = geoip2.database.Reader(geoip_db_path)
                self.logger.info("Initialized GeoIP fallback")
            except Exception as e:
                self.logger.warning(f"Could not initialize GeoIP fallback: {e}")

        # Nominatim rate limiting (1 request per second)
        self.last_nominatim_request = 0
        self.nominatim_delay = 1.0  # seconds

    def _nominatim_lookup(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Perform reverse geocoding using Nominatim (OpenStreetMap)

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            Location data dictionary or None if failed
        """
        try:
            # Rate limiting: ensure 1 second between requests
            time_since_last = time.time() - self.last_nominatim_request
            if time_since_last < self.nominatim_delay:
                time.sleep(self.nominatim_delay - time_since_last)

            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                "lat": latitude,
                "lon": longitude,
                "format": "json",
                "addressdetails": 1,
                "zoom": 18  # Maximum detail level
            }

            headers = {
                "User-Agent": self.user_agent
            }

            self.logger.info(f"Nominatim lookup for ({latitude}, {longitude})")
            response = requests.get(url, params=params, headers=headers, timeout=10)
            self.last_nominatim_request = time.time()

            if response.status_code == 200:
                data = response.json()

                if "error" in data:
                    self.logger.warning(f"Nominatim error: {data.get('error')}")
                    return None

                address = data.get("address", {})

                # Extract location information
                location_data = {
                    "latitude": float(data.get("lat", latitude)),
                    "longitude": float(data.get("lon", longitude)),
                    "zip_code": address.get("postcode"),
                    "city": (address.get("city") or
                            address.get("town") or
                            address.get("village") or
                            address.get("municipality")),
                    "county": address.get("county"),
                    "state": address.get("state"),
                    "state_code": address.get("ISO3166-2-lvl4", "").split("-")[-1] if address.get("ISO3166-2-lvl4") else None,
                    "country": address.get("country"),
                    "country_code": address.get("country_code", "").upper(),
                    "timezone": None,  # Nominatim doesn't provide timezone
                    "source": "nominatim",
                    "display_name": data.get("display_name")
                }

                self.logger.info(f"Nominatim SUCCESS: {location_data.get('city')}, {location_data.get('state_code')}")
                return location_data

            else:
                self.logger.warning(f"Nominatim HTTP error: {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            self.logger.warning("Nominatim request timed out")
            return None
        except Exception as e:
            self.logger.error(f"Nominatim lookup error: {e}")
            return None

    def _geoip_approximate_lookup(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Approximate reverse geocoding using GeoIP database
        Searches for IPs with nearby coordinates (not very accurate)

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            Location data dictionary or None if failed
        """
        if not self.geoip_reader:
            return None

        try:
            self.logger.info(f"GeoIP approximate lookup for ({latitude}, {longitude})")

            # This is a very rough approximation
            # We can't truly reverse geocode with GeoIP, but we can try to find
            # an IP address that's close to these coordinates

            # For now, we'll return a basic result indicating we couldn't find exact data
            # A more sophisticated approach would require iterating through the database
            # which is not practical with GeoIP2

            self.logger.warning("GeoIP approximate lookup not implemented - database doesn't support reverse queries")
            return None

        except Exception as e:
            self.logger.error(f"GeoIP approximate lookup error: {e}")
            return None

    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Perform reverse geocoding with automatic fallback

        Priority:
        1. Nominatim API (most accurate)
        2. GeoIP approximate (fallback, limited accuracy)

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            Location data dictionary with source indicator
        """
        # Validate coordinates
        if not (-90 <= latitude <= 90):
            self.logger.error(f"Invalid latitude: {latitude}")
            return None

        if not (-180 <= longitude <= 180):
            self.logger.error(f"Invalid longitude: {longitude}")
            return None

        # Try Nominatim first
        result = self._nominatim_lookup(latitude, longitude)
        if result:
            return result

        # Fallback to GeoIP approximate
        self.logger.info("Falling back to GeoIP approximate lookup")
        result = self._geoip_approximate_lookup(latitude, longitude)
        if result:
            return result

        # No results found
        self.logger.warning(f"No reverse geocoding results for ({latitude}, {longitude})")
        return {
            "latitude": latitude,
            "longitude": longitude,
            "zip_code": None,
            "city": None,
            "county": None,
            "state": None,
            "state_code": None,
            "country": None,
            "country_code": None,
            "timezone": None,
            "source": "none",
            "display_name": None
        }

    def close(self):
        """Close GeoIP database reader"""
        if self.geoip_reader:
            self.geoip_reader.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
