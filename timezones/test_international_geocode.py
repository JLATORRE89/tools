#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for international reverse geocoding
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from reverse_geocode import ReverseGeocoder
from reverse_geocode_cache import ReverseGeocodeCache

def test_international_geocoding():
    """Test reverse geocoding with international coordinates"""

    # Test coordinates from various countries (lat, lon, expected location)
    test_cases = [
        # United States
        (40.7128, -74.0060, "New York, USA"),
        # United Kingdom
        (51.5074, -0.1278, "London, UK"),
        # Canada
        (43.6532, -79.3832, "Toronto, Canada"),
        # France
        (48.8566, 2.3522, "Paris, France"),
        # Japan
        (35.6762, 139.6503, "Tokyo, Japan"),
        # Australia
        (-33.8688, 151.2093, "Sydney, Australia"),
        # Germany
        (52.5200, 13.4050, "Berlin, Germany"),
        # Brazil
        (-23.5505, -46.6333, "São Paulo, Brazil"),
        # India
        (28.6139, 77.2090, "New Delhi, India"),
        # Mexico
        (19.4326, -99.1332, "Mexico City, Mexico"),
    ]

    print("🌍 Testing International Reverse Geocoding\n")
    print("=" * 100)

    # Initialize cache and geocoder
    cache = ReverseGeocodeCache(db_path="./test_international_cache.db")
    geocoder = ReverseGeocoder(user_agent="TestInternationalScript/1.0")

    for lat, lon, description in test_cases:
        print(f"\n📍 Testing: {description}")
        print(f"   Coordinates: ({lat}, {lon})")

        # Check cache first
        cached = cache.get(lat, lon)
        if cached:
            print(f"   ✅ Found in cache!")
            print(f"   Postal Code: {cached.get('zip_code')}")
            print(f"   City: {cached.get('city')}")
            print(f"   State/Region: {cached.get('state')}")
            print(f"   Country: {cached.get('country')} ({cached.get('country_code')})")
            continue

        # Perform lookup
        result = geocoder.reverse_geocode(lat, lon)

        if result:
            print(f"   Source: {result.get('source')}")
            print(f"   Postal Code: {result.get('zip_code') or 'N/A'}")
            print(f"   City: {result.get('city')}")
            print(f"   State/Region: {result.get('state')}")
            print(f"   County: {result.get('county')}")
            print(f"   Country: {result.get('country')} ({result.get('country_code')})")
            print(f"   Display: {result.get('display_name', '')[:80]}...")

            # Cache successful results
            if result.get('source') == 'nominatim':
                cache.set(lat, lon, result, source='nominatim')
                print(f"   ✅ Cached for future use")
        else:
            print(f"   ❌ Failed to geocode")

        print("-" * 100)

        # Rate limiting: wait 1 second between requests
        import time
        time.sleep(1)

    # Show cache stats
    print("\n📊 Cache Statistics:")
    stats = cache.get_stats()
    print(f"   Total entries: {stats.get('total_entries', 0)}")
    print(f"   By source: {stats.get('by_source', {})}")

    geocoder.close()
    print("\n✅ Test complete!")

if __name__ == "__main__":
    try:
        test_international_geocoding()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
