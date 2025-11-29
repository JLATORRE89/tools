#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for forward geocoding (postal code -> location)
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from forward_geocode import ForwardGeocoder

def test_forward_geocoding():
    """Test forward geocoding with various postal codes"""

    # Test postal codes from various countries (postal_code, country_code, description)
    test_cases = [
        ("10007", "US", "New York, USA"),
        ("90210", "US", "Beverly Hills, USA"),
        ("WC2N 5DX", "GB", "London, UK"),
        ("M5H 2N2", "CA", "Toronto, Canada"),
        ("75004", "FR", "Paris, France"),
        ("168-0063", "JP", "Tokyo, Japan"),
        ("2000", "AU", "Sydney, Australia"),
        ("10178", "DE", "Berlin, Germany"),
        ("01016-020", "BR", "São Paulo, Brazil"),
        ("06000", "MX", "Mexico City, Mexico"),
    ]

    print("🌍 Testing Forward Geocoding (Postal Code -> Location)\n")
    print("=" * 100)

    geocoder = ForwardGeocoder(user_agent="TestForwardGeocodingScript/1.0")

    for postal_code, country_code, description in test_cases:
        print(f"\n📍 Testing: {description}")
        print(f"   Postal Code: {postal_code} ({country_code})")

        # Perform lookup
        result = geocoder.geocode_postal(postal_code, country_code)

        if result and result.get('source') != 'none':
            print(f"   Source: {result.get('source')}")
            print(f"   Coordinates: ({result.get('latitude')}, {result.get('longitude')})")
            print(f"   City: {result.get('city')}")
            print(f"   State/Region: {result.get('state')}")
            print(f"   Country: {result.get('country')} ({result.get('country_code')})")
            print(f"   Display: {result.get('display_name', '')[:80]}...")
        else:
            print(f"   ❌ No results found")

        print("-" * 100)

        # Rate limiting: wait 1 second between requests
        import time
        time.sleep(1)

    print("\n✅ Test complete!")

if __name__ == "__main__":
    try:
        test_forward_geocoding()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
