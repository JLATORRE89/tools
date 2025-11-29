#!/usr/bin/env python3
"""
Reverse Geocoding Cache Module
Stores lat/long -> location lookups in SQLite for faster retrieval
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class ReverseGeocodeCache:
    """SQLite-backed cache for reverse geocoding results"""

    def __init__(self, db_path: str = "./geocode_cache.db", cache_days: int = 90):
        """
        Initialize reverse geocoding cache

        Args:
            db_path: Path to SQLite database file
            cache_days: Number of days to keep cached entries (default: 90)
        """
        self.db_path = db_path
        self.cache_days = cache_days
        self.logger = logging.getLogger("ReverseGeocodeCache")
        self._init_database()

    def _init_database(self):
        """Create database table if it doesn't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS geocode_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    zip_code TEXT,
                    city TEXT,
                    county TEXT,
                    state TEXT,
                    state_code TEXT,
                    country TEXT,
                    country_code TEXT,
                    timezone TEXT,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create index for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_coords
                ON geocode_cache(latitude, longitude)
            """)

            conn.commit()
            self.logger.info(f"Initialized geocode cache database at {self.db_path}")

    def _coords_match(self, lat1: float, lon1: float, lat2: float, lon2: float, tolerance: float = 0.01) -> bool:
        """
        Check if two coordinate pairs are close enough to be considered the same location

        Args:
            lat1, lon1: First coordinate pair
            lat2, lon2: Second coordinate pair
            tolerance: Maximum difference in degrees (default: 0.01 ≈ 1km)

        Returns:
            True if coordinates match within tolerance
        """
        return abs(lat1 - lat2) <= tolerance and abs(lon1 - lon2) <= tolerance

    def get(self, latitude: float, longitude: float, tolerance: float = 0.01) -> Optional[Dict[str, Any]]:
        """
        Get cached reverse geocoding result

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            tolerance: Coordinate matching tolerance in degrees (default: 0.01)

        Returns:
            Cached location data or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Find entries within tolerance range
                cursor.execute("""
                    SELECT latitude, longitude, zip_code, city, county, state,
                           state_code, country, country_code, timezone, source, created_at
                    FROM geocode_cache
                    WHERE latitude BETWEEN ? AND ?
                    AND longitude BETWEEN ? AND ?
                    ORDER BY created_at DESC
                """, (
                    latitude - tolerance, latitude + tolerance,
                    longitude - tolerance, longitude + tolerance
                ))

                row = cursor.fetchone()

                if row:
                    # Verify exact match within tolerance
                    if self._coords_match(latitude, longitude, row[0], row[1], tolerance):
                        # Update last_accessed timestamp
                        cursor.execute("""
                            UPDATE geocode_cache
                            SET last_accessed = CURRENT_TIMESTAMP
                            WHERE latitude = ? AND longitude = ?
                        """, (row[0], row[1]))
                        conn.commit()

                        result = {
                            "latitude": row[0],
                            "longitude": row[1],
                            "zip_code": row[2],
                            "city": row[3],
                            "county": row[4],
                            "state": row[5],
                            "state_code": row[6],
                            "country": row[7],
                            "country_code": row[8],
                            "timezone": row[9],
                            "source": row[10],
                            "cached_at": row[11],
                            "from_cache": True
                        }

                        self.logger.info(f"Cache HIT for ({latitude}, {longitude})")
                        return result

                self.logger.info(f"Cache MISS for ({latitude}, {longitude})")
                return None

        except Exception as e:
            self.logger.error(f"Error reading from cache: {e}")
            return None

    def set(self, latitude: float, longitude: float, location_data: Dict[str, Any], source: str = "nominatim"):
        """
        Store reverse geocoding result in cache

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            location_data: Location information dictionary
            source: Data source (e.g., 'nominatim', 'geoip')
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if entry already exists
                cursor.execute("""
                    SELECT id FROM geocode_cache
                    WHERE latitude = ? AND longitude = ?
                """, (latitude, longitude))

                existing = cursor.fetchone()

                if existing:
                    # Update existing entry
                    cursor.execute("""
                        UPDATE geocode_cache
                        SET zip_code = ?, city = ?, county = ?, state = ?,
                            state_code = ?, country = ?, country_code = ?,
                            timezone = ?, source = ?, last_accessed = CURRENT_TIMESTAMP
                        WHERE latitude = ? AND longitude = ?
                    """, (
                        location_data.get("zip_code"),
                        location_data.get("city"),
                        location_data.get("county"),
                        location_data.get("state"),
                        location_data.get("state_code"),
                        location_data.get("country"),
                        location_data.get("country_code"),
                        location_data.get("timezone"),
                        source,
                        latitude,
                        longitude
                    ))
                    self.logger.info(f"Updated cache entry for ({latitude}, {longitude})")
                else:
                    # Insert new entry
                    cursor.execute("""
                        INSERT INTO geocode_cache
                        (latitude, longitude, zip_code, city, county, state,
                         state_code, country, country_code, timezone, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        latitude,
                        longitude,
                        location_data.get("zip_code"),
                        location_data.get("city"),
                        location_data.get("county"),
                        location_data.get("state"),
                        location_data.get("state_code"),
                        location_data.get("country"),
                        location_data.get("country_code"),
                        location_data.get("timezone"),
                        source
                    ))
                    self.logger.info(f"Added new cache entry for ({latitude}, {longitude})")

                conn.commit()

        except Exception as e:
            self.logger.error(f"Error writing to cache: {e}")

    def cleanup_old_entries(self):
        """Remove entries older than cache_days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.cache_days)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM geocode_cache
                    WHERE created_at < ?
                """, (cutoff_date.isoformat(),))

                deleted = cursor.rowcount
                conn.commit()

                if deleted > 0:
                    self.logger.info(f"Cleaned up {deleted} old cache entries")

        except Exception as e:
            self.logger.error(f"Error cleaning up cache: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Total entries
                cursor.execute("SELECT COUNT(*) FROM geocode_cache")
                total = cursor.fetchone()[0]

                # Entries by source
                cursor.execute("""
                    SELECT source, COUNT(*)
                    FROM geocode_cache
                    GROUP BY source
                """)
                by_source = dict(cursor.fetchall())

                # Oldest and newest entries
                cursor.execute("""
                    SELECT MIN(created_at), MAX(created_at)
                    FROM geocode_cache
                """)
                oldest, newest = cursor.fetchone()

                return {
                    "total_entries": total,
                    "by_source": by_source,
                    "oldest_entry": oldest,
                    "newest_entry": newest,
                    "cache_days": self.cache_days
                }

        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {}
