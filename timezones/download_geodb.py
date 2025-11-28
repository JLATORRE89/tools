#!/usr/bin/env python3
"""
GeoLite2 Database Downloader
Downloads and extracts the free GeoLite2-City database from MaxMind
"""

import os
import sys
import requests
import tarfile
import shutil
from pathlib import Path


def download_geolite2_city():
    """
    Download GeoLite2-City database

    Note: MaxMind now requires a license key for downloads.
    This script provides instructions for manual download.
    """
    print("=" * 60)
    print("GeoLite2-City Database Setup")
    print("=" * 60)

    db_dir = Path("./geodb")
    db_file = db_dir / "GeoLite2-City.mmdb"

    # Check if already exists
    if db_file.exists():
        print(f"✅ Database already exists: {db_file}")
        choice = input("Download a fresh copy? (y/n): ").lower()
        if choice != 'y':
            print("Using existing database.")
            return True

    print("\n📥 Downloading GeoLite2-City Database...")
    print("\nMaxMind now requires a free license key to download GeoLite2 databases.")
    print("\nPlease follow these steps:")
    print("\n1. Sign up for a free MaxMind account:")
    print("   https://www.maxmind.com/en/geolite2/signup")
    print("\n2. Generate a license key:")
    print("   https://www.maxmind.com/en/accounts/current/license-key")
    print("\n3. Download GeoLite2-City database:")
    print("   https://download.maxmind.com/app/geoip_download")
    print("   - Select: GeoLite2 City")
    print("   - Format: GeoIP2 Binary (.mmdb)")
    print("\n4. Choose download method:")
    print("   a) Enter download URL with license key")
    print("   b) Manual download (place file in ./geodb/)")
    print()

    choice = input("Enter 'a' for URL download or 'b' for manual: ").lower()

    if choice == 'a':
        print("\nThe download URL format is:")
        print("https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=YOUR_LICENSE_KEY&suffix=tar.gz")
        print()
        url = input("Paste your download URL: ").strip()

        if not url:
            print("❌ No URL provided. Please try manual download.")
            return manual_download_instructions(db_dir)

        return download_from_url(url, db_dir)

    else:
        return manual_download_instructions(db_dir)


def download_from_url(url: str, db_dir: Path):
    """Download and extract database from URL"""
    try:
        # Create directory
        db_dir.mkdir(parents=True, exist_ok=True)

        # Download file
        print("Downloading database... (this may take a minute)")
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()

        tar_file = db_dir / "GeoLite2-City.tar.gz"

        with open(tar_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print("✅ Download complete")

        # Extract tar.gz
        print("Extracting database...")
        with tarfile.open(tar_file, 'r:gz') as tar:
            # Find the .mmdb file in the archive
            mmdb_file = None
            for member in tar.getmembers():
                if member.name.endswith('.mmdb'):
                    mmdb_file = member
                    break

            if mmdb_file:
                # Extract just the .mmdb file
                tar.extract(mmdb_file, db_dir)

                # Move to final location
                extracted_path = db_dir / mmdb_file.name
                final_path = db_dir / "GeoLite2-City.mmdb"

                shutil.move(str(extracted_path), str(final_path))

                # Clean up
                tar_file.unlink()

                # Remove extracted directory if it exists
                extracted_dir = db_dir / mmdb_file.name.split('/')[0]
                if extracted_dir.exists() and extracted_dir.is_dir():
                    shutil.rmtree(extracted_dir)

                print(f"✅ Database installed: {final_path}")
                return True
            else:
                print("❌ Could not find .mmdb file in archive")
                return False

    except requests.RequestException as e:
        print(f"❌ Download failed: {e}")
        print("\nPlease try manual download.")
        return manual_download_instructions(db_dir)
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def manual_download_instructions(db_dir: Path):
    """Provide manual download instructions"""
    db_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("Manual Download Instructions")
    print("=" * 60)
    print("\n1. Download GeoLite2-City database from:")
    print("   https://dev.maxmind.com/geoip/geolite2-free-geolocation-data")
    print()
    print("2. Extract the .tar.gz file")
    print()
    print("3. Find the GeoLite2-City.mmdb file inside")
    print()
    print(f"4. Copy it to: {db_dir.absolute()}/GeoLite2-City.mmdb")
    print()
    print("5. Run the API server: python3 main.py")
    print("=" * 60)

    return False


def check_database_exists():
    """Check if database exists in common locations"""
    possible_paths = [
        "./geodb/GeoLite2-City.mmdb",
        "./GeoLite2-City.mmdb",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Found database: {path}")
            return True

    return False


if __name__ == "__main__":
    print("🌍 GeoLite2 Database Downloader\n")

    if check_database_exists():
        print("Database already exists!")
        choice = input("Download fresh copy? (y/n): ").lower()
        if choice != 'y':
            print("Keeping existing database.")
            sys.exit(0)

    success = download_geolite2_city()

    if success:
        print("\n✅ Setup complete! You can now run the API server.")
        print("   python3 main.py")
    else:
        print("\n⚠️  Please complete manual download before running the server.")

    sys.exit(0 if success else 1)
