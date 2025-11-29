#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for reverse geocoding functionality
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from reverse_geocode import ReverseGeocoder
from reverse_geocode_cache import ReverseGeocodeCache

def test_reverse_geocode():
    """Test reverse geocoding with various coordinates"""

    # Test coordinates (lat, lon, expected location)
    test_cases = [
        (40.7128, -74.0060, "New York, NY"),
        (34.0522, -118.2437, "Los Angeles, CA"),
        (41.8781, -87.6298, "Chicago, IL"),
        (29.7604, -95.3698, "Houston, TX"),
        (51.5074, -0.1278, "London, UK"),
    ]

    print("🧪 Testing Reverse Geocoding\n")
    print("=" * 80)

    # Initialize cache and geocoder
    cache = ReverseGeocodeCache(db_path="./test_geocode_cache.db")
    geocoder = ReverseGeocoder(user_agent="TestScript/1.0")

    for lat, lon, description in test_cases:
        print(f"\n📍 Testing: {description}")
        print(f"   Coordinates: ({lat}, {lon})")

        # Check cache first
        cached = cache.get(lat, lon)
        if cached:
            print(f"   ✅ Found in cache!")
            print(f"   Zip: {cached.get('zip_code')}")
            print(f"   City: {cached.get('city')}, {cached.get('state_code')}")
            print(f"   Country: {cached.get('country')}")
            continue

        # Perform lookup
        result = geocoder.reverse_geocode(lat, lon)

        if result:
            print(f"   Source: {result.get('source')}")
            print(f"   Zip: {result.get('zip_code')}")
            print(f"   City: {result.get('city')}, {result.get('state_code')}")
            print(f"   County: {result.get('county')}")
            print(f"   Country: {result.get('country')} ({result.get('country_code')})")
            print(f"   Timezone: {result.get('timezone')}")

            # Cache successful results
            if result.get('source') == 'nominatim':
                cache.set(lat, lon, result, source='nominatim')
                print(f"   ✅ Cached for future use")
        else:
            print(f"   ❌ Failed to geocode")

        print("-" * 80)

    # Show cache stats
    print("\n📊 Cache Statistics:")
    stats = cache.get_stats()
    print(f"   Total entries: {stats.get('total_entries', 0)}")
    print(f"   By source: {stats.get('by_source', {})}")

    geocoder.close()
    print("\n✅ Test complete!")

if __name__ == "__main__":
    try:
        test_reverse_geocode()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
