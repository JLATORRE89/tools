#!/usr/bin/env python3
"""
IP Address Merger Script
Merges unique IP addresses from multiple ip.txt files and stores them in an SQLite database.
"""

import os
import re
import sqlite3
from pathlib import Path
from typing import Set
import argparse


def is_valid_ip(ip: str) -> bool:
    """Validate if a string is a valid IPv4 address."""
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip):
        return False

    parts = ip.split('.')
    return all(0 <= int(part) <= 255 for part in parts)


def read_ips_from_file(filepath: Path) -> Set[str]:
    """Read and extract valid IP addresses from a file."""
    ips = set()
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line and is_valid_ip(line):
                    ips.add(line)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return ips


def find_ip_files(directory: str) -> list:
    """Find all ip.txt* files in the directory."""
    dir_path = Path(directory)
    ip_files = []

    # Find ip.txt and ip.txt.backup.* files
    for file in dir_path.glob('ip.txt*'):
        if file.is_file():
            ip_files.append(file)

    return sorted(ip_files)


def create_database(db_path: str):
    """Create SQLite database and IP addresses table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ip_addresses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT UNIQUE NOT NULL,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_ip_address ON ip_addresses(ip_address)
    ''')

    conn.commit()
    return conn


def get_existing_ips(conn: sqlite3.Connection) -> Set[str]:
    """Get all existing IP addresses from database."""
    cursor = conn.cursor()
    cursor.execute('SELECT ip_address FROM ip_addresses')
    return {row[0] for row in cursor.fetchall()}


def insert_ips(conn: sqlite3.Connection, ips: Set[str]):
    """Insert new IP addresses into database."""
    cursor = conn.cursor()
    inserted = 0

    for ip in ips:
        try:
            cursor.execute('''
                INSERT INTO ip_addresses (ip_address)
                VALUES (?)
                ON CONFLICT(ip_address) DO UPDATE SET last_updated = CURRENT_TIMESTAMP
            ''', (ip,))
            if cursor.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"Error inserting IP {ip}: {e}")

    conn.commit()
    return inserted


def write_consolidated_ip_file(ips: Set[str], output_path: str):
    """Write all unique IP addresses to a consolidated ip.txt file."""
    try:
        # Sort IPs for consistent output
        sorted_ips = sorted(ips, key=lambda ip: [int(part) for part in ip.split('.')])

        with open(output_path, 'w', encoding='utf-8') as f:
            for ip in sorted_ips:
                f.write(f"{ip}\n")

        return len(sorted_ips)
    except Exception as e:
        print(f"Error writing consolidated IP file: {e}")
        return 0


def remove_backup_files(ip_files: list, output_file: str):
    """Remove backup ip.txt files, keeping only the consolidated ip.txt."""
    removed_count = 0
    errors = []

    for filepath in ip_files:
        # Don't remove the main consolidated ip.txt file
        if str(filepath) == output_file:
            continue

        # Remove backup files (ip.txt.backup.*)
        if '.backup.' in filepath.name or filepath.name != os.path.basename(output_file):
            try:
                os.remove(filepath)
                removed_count += 1
            except Exception as e:
                errors.append(f"  {filepath.name}: {e}")

    return removed_count, errors


def main():
    parser = argparse.ArgumentParser(
        description='Merge IP addresses from multiple ip.txt files into SQLite database'
    )
    parser.add_argument(
        '--directory',
        default='/root',
        help='Directory containing ip.txt files (default: /root)'
    )
    parser.add_argument(
        '--database',
        default='ip_addresses.db',
        help='SQLite database file path (default: ip_addresses.db)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output'
    )
    parser.add_argument(
        '--output',
        help='Output file path for consolidated ip.txt (default: ip.txt in source directory)'
    )
    parser.add_argument(
        '--keep-backups',
        action='store_true',
        help='Keep backup files instead of removing them after merge'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("IP Address Merger")
    print("=" * 60)

    # Find all ip.txt files
    print(f"\nSearching for ip.txt files in: {args.directory}")
    ip_files = find_ip_files(args.directory)

    if not ip_files:
        print(f"No ip.txt files found in {args.directory}")
        return

    print(f"Found {len(ip_files)} ip.txt file(s)")

    # Collect all unique IPs from files
    all_ips = set()
    for filepath in ip_files:
        file_ips = read_ips_from_file(filepath)
        if args.verbose and file_ips:
            print(f"  {filepath.name}: {len(file_ips)} IPs")
        all_ips.update(file_ips)

    print(f"\nTotal unique IPs found in files: {len(all_ips)}")

    # Create/connect to database
    print(f"\nConnecting to database: {args.database}")
    conn = create_database(args.database)

    # Get existing IPs from database
    existing_ips = get_existing_ips(conn)
    print(f"Existing IPs in database: {len(existing_ips)}")

    # Find new IPs to add
    new_ips = all_ips - existing_ips
    print(f"New IPs to add: {len(new_ips)}")

    # Insert new IPs
    if new_ips:
        print("\nInserting new IP addresses...")
        inserted = insert_ips(conn, all_ips)
        print(f"Successfully processed {inserted} IP address(es)")
    else:
        print("\nNo new IP addresses to add - database is up to date")

    # Final statistics
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM ip_addresses')
    total_count = cursor.fetchone()[0]

    conn.close()

    # Write consolidated ip.txt file
    output_file = args.output if args.output else os.path.join(args.directory, 'ip.txt')
    print(f"\nWriting consolidated IP list to: {output_file}")
    written_count = write_consolidated_ip_file(all_ips, output_file)
    print(f"Successfully wrote {written_count} IP address(es) to {output_file}")

    # Remove backup files unless --keep-backups is specified
    if not args.keep_backups:
        print(f"\nRemoving backup files...")
        removed_count, errors = remove_backup_files(ip_files, output_file)
        print(f"Successfully removed {removed_count} backup file(s)")
        if errors:
            print("Errors encountered:")
            for error in errors:
                print(error)
    else:
        print("\nKeeping backup files (--keep-backups specified)")

    print("\n" + "=" * 60)
    print(f"Total IP addresses in database: {total_count}")
    print(f"Total IP addresses in {output_file}: {written_count}")
    if not args.keep_backups:
        print(f"Backup files removed: {removed_count}")
    print("=" * 60)


if __name__ == '__main__':
    main()
