#!/usr/bin/env python3
"""
IP to Timezone Lookup Module
Uses GeoIP2 database to map IP addresses to timezones
"""

import geoip2.database
import geoip2.errors
from pathlib import Path
import os
import requests
import tarfile
import shutil


class IPTimezoneLookup:
    def __init__(self, db_path: str = None):
        """
        Initialize IP timezone lookup

        Args:
            db_path: Path to GeoLite2-City.mmdb file. If not provided, will look in common locations.
        """
        self.db_path = db_path or self._find_database()
        self.reader = None

        if self.db_path and os.path.exists(self.db_path):
            try:
                self.reader = geoip2.database.Reader(self.db_path)
                print(f"✅ Loaded GeoIP2 database from: {self.db_path}")
            except Exception as e:
                print(f"❌ Error loading GeoIP2 database: {e}")
                self.reader = None
        else:
            print("⚠️  GeoIP2 database not found. Please download it first.")
            print("   Run: python3 download_geodb.py")

    def _find_database(self) -> str:
        """Find GeoLite2-City database in common locations"""
        possible_paths = [
            "./GeoLite2-City.mmdb",
            "./geodb/GeoLite2-City.mmdb",
            "/usr/share/GeoIP/GeoLite2-City.mmdb",
            "/var/lib/GeoIP/GeoLite2-City.mmdb",
            str(Path.home() / "GeoLite2-City.mmdb"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        return None

    def get_timezone(self, ip: str) -> str:
        """
        Get timezone for an IP address

        Args:
            ip: IP address (IPv4 or IPv6)

        Returns:
            Timezone name (e.g., 'America/New_York') or None if not found
        """
        if not self.reader:
            # Fallback to basic mapping if no database
            return self._fallback_timezone(ip)

        try:
            response = self.reader.city(ip)

            # Get timezone from location
            if response.location.time_zone:
                return response.location.time_zone

            # Fallback: try to determine from country
            if response.country.iso_code:
                return self._country_to_timezone(response.country.iso_code)

            return None

        except geoip2.errors.AddressNotFoundError:
            # IP not found in database
            return self._fallback_timezone(ip)
        except Exception as e:
            print(f"Error looking up IP {ip}: {e}")
            return None

    def get_location_info(self, ip: str) -> dict:
        """
        Get detailed location information for an IP address
        including ZIP code and county/state subdivision.
        """
        if not self.reader:
            return {
                "ip": ip,
                "timezone": self._fallback_timezone(ip),
                "country": None,
                "country_code": None,
                "city": None,
                "zip_code": None,
                "county": None,
                "state_code": None,
                "latitude": None,
                "longitude": None,
                "continent": None
            }

        try:
            response = self.reader.city(ip)

            # ZIP / postal code
            zip_code = response.postal.code if response.postal and response.postal.code else None

            # County / state (GeoLite uses subdivisions list)
            county = None
            state_code = None
            if response.subdivisions and len(response.subdivisions) > 0:
                county = response.subdivisions[0].name
                state_code = response.subdivisions[0].iso_code

            return {
                "ip": ip,
                "timezone": response.location.time_zone,
                "country": response.country.name,
                "country_code": response.country.iso_code,
                "city": response.city.name,
                "zip_code": zip_code,
                "county": county,
                "state_code": state_code,
                "latitude": response.location.latitude,
                "longitude": response.location.longitude,
                "continent": response.continent.name
            }

        except geoip2.errors.AddressNotFoundError:
            return {
                "ip": ip,
                "timezone": self._fallback_timezone(ip),
                "country": None,
                "country_code": None,
                "city": None,
                "zip_code": None,
                "county": None,
                "state_code": None,
                "latitude": None,
                "longitude": None,
                "continent": None
            }
        except Exception as e:
            print(f"Error getting location info for {ip}: {e}")
            return None

    def _fallback_timezone(self, ip: str) -> str:
        """
        Fallback timezone determination based on IP range
        This is a very basic approximation
        """
        # Default to UTC for private/local IPs
        if ip.startswith(("127.", "10.", "192.168.", "172.")):
            return "UTC"

        # Default to UTC for unknown IPs
        return "UTC"

    def _country_to_timezone(self, country_code: str) -> str:
        """
        Map country code to primary timezone
        This is a simplified mapping - countries may have multiple timezones
        """
        country_timezone_map = {
            "US": "America/New_York",
            "GB": "Europe/London",
            "DE": "Europe/Berlin",
            "FR": "Europe/Paris",
            "JP": "Asia/Tokyo",
            "CN": "Asia/Shanghai",
            "IN": "Asia/Kolkata",
            "AU": "Australia/Sydney",
            "BR": "America/Sao_Paulo",
            "CA": "America/Toronto",
            "MX": "America/Mexico_City",
            "RU": "Europe/Moscow",
            "ZA": "Africa/Johannesburg",
            "AR": "America/Argentina/Buenos_Aires",
            "IT": "Europe/Rome",
            "ES": "Europe/Madrid",
            "NL": "Europe/Amsterdam",
            "SE": "Europe/Stockholm",
            "NO": "Europe/Oslo",
            "DK": "Europe/Copenhagen",
            "FI": "Europe/Helsinki",
            "PL": "Europe/Warsaw",
            "CH": "Europe/Zurich",
            "AT": "Europe/Vienna",
            "BE": "Europe/Brussels",
            "GR": "Europe/Athens",
            "PT": "Europe/Lisbon",
            "IE": "Europe/Dublin",
            "NZ": "Pacific/Auckland",
            "SG": "Asia/Singapore",
            "HK": "Asia/Hong_Kong",
            "KR": "Asia/Seoul",
            "TH": "Asia/Bangkok",
            "MY": "Asia/Kuala_Lumpur",
            "ID": "Asia/Jakarta",
            "PH": "Asia/Manila",
            "VN": "Asia/Ho_Chi_Minh",
            "TR": "Europe/Istanbul",
            "IL": "Asia/Jerusalem",
            "SA": "Asia/Riyadh",
            "AE": "Asia/Dubai",
            "EG": "Africa/Cairo",
            "NG": "Africa/Lagos",
            "KE": "Africa/Nairobi",
        }

        return country_timezone_map.get(country_code, "UTC")

    def close(self):
        """Close the database reader"""
        if self.reader:
            self.reader.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
