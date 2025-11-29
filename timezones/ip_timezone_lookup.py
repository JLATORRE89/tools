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
import logging
from logging.handlers import TimedRotatingFileHandler


def setup_logger(log_dir: str = "./logs") -> logging.Logger:
    """
    Set up logger with weekly rotation

    Args:
        log_dir: Directory to store log files

    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    # Create logger
    logger = logging.getLogger("IPTimezoneLookup")
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # File handler with weekly rotation (W0 = Monday)
    log_file = os.path.join(log_dir, "ip_timezone_lookup.log")
    file_handler = TimedRotatingFileHandler(
        log_file,
        when="W0",  # Rotate every Monday
        interval=1,
        backupCount=4,  # Keep 4 weeks of logs
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


class IPTimezoneLookup:
    def __init__(self, db_path: str = None, log_dir: str = "./logs"):
        """
        Initialize IP timezone lookup

        Args:
            db_path: Path to GeoLite2-City.mmdb file. If not provided, will look in common locations.
            log_dir: Directory to store log files (default: ./logs)
        """
        self.logger = setup_logger(log_dir)
        self.db_path = db_path or self._find_database()
        self.reader = None

        if self.db_path and os.path.exists(self.db_path):
            try:
                self.reader = geoip2.database.Reader(self.db_path)
                self.logger.info(f"Loaded GeoIP2 database from: {self.db_path}")
                print(f"[OK] Loaded GeoIP2 database from: {self.db_path}")
            except Exception as e:
                self.logger.error(f"Error loading GeoIP2 database: {e}")
                print(f"[ERROR] Error loading GeoIP2 database: {e}")
                self.reader = None
        else:
            self.logger.warning("GeoIP2 database not found")
            print("[WARNING] GeoIP2 database not found. Please download it first.")
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
            self.logger.warning(f"No database available, using fallback for IP: {ip}")
            return self._fallback_timezone(ip)

        try:
            response = self.reader.city(ip)

            # Get timezone from location
            if response.location.time_zone:
                self.logger.info(f"IP {ip} -> Timezone: {response.location.time_zone}")
                return response.location.time_zone

            # Fallback: try to determine from country
            if response.country.iso_code:
                tz = self._country_to_timezone(response.country.iso_code)
                self.logger.info(f"IP {ip} -> Country {response.country.iso_code} -> Timezone: {tz}")
                return tz

            self.logger.warning(f"No timezone found for IP: {ip}")
            return None

        except geoip2.errors.AddressNotFoundError:
            # IP not found in database
            self.logger.warning(f"IP not found in database: {ip}, using fallback")
            return self._fallback_timezone(ip)
        except Exception as e:
            self.logger.error(f"Error looking up IP {ip}: {e}")
            print(f"Error looking up IP {ip}: {e}")
            return None

    def get_location_info(self, ip: str) -> dict:
        """
        Get detailed location information for an IP address
        including ZIP code and county/state subdivision.
        """
        if not self.reader:
            self.logger.warning(f"No database available for location info lookup: {ip}")
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

            location_data = {
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

            self.logger.info(f"IP {ip} -> {response.city.name}, {state_code}, {response.country.iso_code} ({response.location.time_zone})")
            return location_data

        except geoip2.errors.AddressNotFoundError:
            self.logger.warning(f"IP not found in database for location info: {ip}")
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
            self.logger.error(f"Error getting location info for {ip}: {e}")
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
