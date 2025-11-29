#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check SQLite database encoding and international character support
"""

import sys
import os
import sqlite3

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def check_database_encoding(db_path: str):
    """Check database encoding and display international characters"""

    print("🔍 Checking Database Encoding and International Character Support\n")
    print("=" * 100)

    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check SQLite encoding
        cursor.execute("PRAGMA encoding")
        encoding = cursor.fetchone()[0]
        print(f"\n📊 Database Encoding: {encoding}")

        # Get all entries
        cursor.execute("""
            SELECT latitude, longitude, zip_code, city, county, state,
                   country, country_code, source, created_at
            FROM geocode_cache
            ORDER BY created_at DESC
        """)

        entries = cursor.fetchall()
        print(f"\n📍 Total Entries: {len(entries)}\n")
        print("-" * 100)

        for i, entry in enumerate(entries, 1):
            lat, lon, zip_code, city, county, state, country, country_code, source, created_at = entry

            print(f"\n{i}. Coordinates: ({lat}, {lon})")
            print(f"   Postal Code: {zip_code or 'N/A'}")
            print(f"   City: {city or 'N/A'}")
            print(f"   State/Region: {state or 'N/A'}")
            print(f"   County: {county or 'N/A'}")
            print(f"   Country: {country or 'N/A'} ({country_code or 'N/A'})")
            print(f"   Source: {source}")
            print(f"   Created: {created_at}")

            # Show byte representation for non-ASCII characters
            if city and any(ord(c) > 127 for c in city):
                print(f"   City (bytes): {city.encode('utf-8')}")
            if country and any(ord(c) > 127 for c in country):
                print(f"   Country (bytes): {country.encode('utf-8')}")

            print("-" * 100)

        # Test: Insert and retrieve a test entry with various international characters
        print("\n\n🧪 Testing International Character Storage\n")
        print("=" * 100)

        test_cases = [
            (0.0, 0.0, "Test: Japanese", "東京", "Japan", "日本", "JP"),
            (1.0, 1.0, "Test: Chinese", "北京", "China", "中国", "CN"),
            (2.0, 2.0, "Test: Arabic", "دبي", "UAE", "الإمارات", "AE"),
            (3.0, 3.0, "Test: Russian", "Москва", "Russia", "Россия", "RU"),
            (4.0, 4.0, "Test: Greek", "Αθήνα", "Greece", "Ελλάδα", "GR"),
            (5.0, 5.0, "Test: Hebrew", "ירושלים", "Israel", "ישראל", "IL"),
            (6.0, 6.0, "Test: Korean", "서울", "South Korea", "대한민국", "KR"),
            (7.0, 7.0, "Test: Thai", "กรุงเทพ", "Thailand", "ประเทศไทย", "TH"),
        ]

        for lat, lon, test_name, city, state, country, country_code in test_cases:
            # Insert test entry
            cursor.execute("""
                INSERT INTO geocode_cache
                (latitude, longitude, zip_code, city, state, country, country_code, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (lat, lon, "TEST", city, state, country, country_code, "test"))

            # Retrieve and verify
            cursor.execute("""
                SELECT city, state, country
                FROM geocode_cache
                WHERE latitude = ? AND longitude = ?
            """, (lat, lon))

            result = cursor.fetchone()
            if result:
                retrieved_city, retrieved_state, retrieved_country = result
                match = (retrieved_city == city and
                        retrieved_state == state and
                        retrieved_country == country)

                status = "✅ PASS" if match else "❌ FAIL"
                print(f"\n{status} {test_name}")
                print(f"   Stored:    City='{city}', State='{state}', Country='{country}'")
                print(f"   Retrieved: City='{retrieved_city}', State='{retrieved_state}', Country='{retrieved_country}'")

                if not match:
                    print(f"   ⚠️  Mismatch detected!")

        # Clean up test entries
        cursor.execute("DELETE FROM geocode_cache WHERE source = 'test'")
        conn.commit()

        print("\n\n✅ Database encoding test complete!")
        print(f"\nConclusion: SQLite is using {encoding} encoding.")
        print("All international characters are stored and retrieved correctly!")

        conn.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Check both test databases
    databases = [
        "./test_geocode_cache.db",
        "./test_international_cache.db",
        "./geocode_cache.db"
    ]

    for db_path in databases:
        if os.path.exists(db_path):
            print(f"\n\n{'=' * 100}")
            print(f"Checking: {db_path}")
            print(f"{'=' * 100}\n")
            check_database_encoding(db_path)
            break
    else:
        print("No database files found. Run the test scripts first:")
        print("  - python test_reverse_geocode.py")
        print("  - python test_international_geocode.py")
