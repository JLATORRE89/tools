#!/usr/bin/env python3
"""
Forward Geocoding Module
Converts postal codes (zip codes) to location information and coordinates
Uses Nominatim API
"""

import requests
import logging
import time
from typing import Optional, Dict, Any


class ForwardGeocoder:
    """Forward geocoding from postal codes to coordinates and location details"""

    def __init__(self, user_agent: str = "TimezoneAPI/1.0"):
        """
        Initialize forward geocoder

        Args:
            user_agent: User agent string for Nominatim requests
        """
        self.logger = logging.getLogger("ForwardGeocoder")
        self.user_agent = user_agent

        # Nominatim rate limiting (1 request per second)
        self.last_nominatim_request = 0
        self.nominatim_delay = 1.0  # seconds

    def _nominatim_postal_lookup(self, postal_code: str, country_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Perform forward geocoding using Nominatim (OpenStreetMap)

        Args:
            postal_code: Postal code / zip code to look up
            country_code: Optional ISO 3166-1 alpha-2 country code (e.g., "US", "GB", "JP")

        Returns:
            Location data dictionary or None if failed
        """
        try:
            # Rate limiting: ensure 1 second between requests
            time_since_last = time.time() - self.last_nominatim_request
            if time_since_last < self.nominatim_delay:
                time.sleep(self.nominatim_delay - time_since_last)

            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "postalcode": postal_code,
                "format": "json",
                "addressdetails": 1,
                "limit": 1
            }

            # Add country filter if provided
            if country_code:
                params["countrycodes"] = country_code.lower()

            headers = {
                "User-Agent": self.user_agent
            }

            self.logger.info(f"Nominatim postal code lookup for: {postal_code} ({country_code or 'any country'})")
            response = requests.get(url, params=params, headers=headers, timeout=10)
            self.last_nominatim_request = time.time()

            if response.status_code == 200:
                data = response.json()

                if not data or len(data) == 0:
                    self.logger.warning(f"No results for postal code: {postal_code}")
                    return None

                # Take the first result
                result = data[0]
                address = result.get("address", {})

                # Extract location information
                location_data = {
                    "postal_code": postal_code,
                    "latitude": float(result.get("lat", 0)),
                    "longitude": float(result.get("lon", 0)),
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
                    "display_name": result.get("display_name"),
                    "bbox": result.get("boundingbox")  # Bounding box coordinates
                }

                self.logger.info(f"Nominatim SUCCESS: {location_data.get('city')}, {location_data.get('country_code')}")
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

    def geocode_postal(self, postal_code: str, country_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Perform forward geocoding from postal code

        Args:
            postal_code: Postal code / zip code to look up
            country_code: Optional ISO 3166-1 alpha-2 country code (e.g., "US", "GB", "JP")
                         Highly recommended for accurate results, especially for common codes

        Returns:
            Location data dictionary with coordinates and details
        """
        # Validate postal code
        if not postal_code or not postal_code.strip():
            self.logger.error("Empty postal code provided")
            return None

        postal_code = postal_code.strip()

        # Try Nominatim
        result = self._nominatim_postal_lookup(postal_code, country_code)
        if result:
            return result

        # No results found
        self.logger.warning(f"No geocoding results for postal code: {postal_code}")
        return {
            "postal_code": postal_code,
            "latitude": None,
            "longitude": None,
            "city": None,
            "county": None,
            "state": None,
            "state_code": None,
            "country": None,
            "country_code": country_code.upper() if country_code else None,
            "timezone": None,
            "source": "none",
            "display_name": None,
            "bbox": None
        }
