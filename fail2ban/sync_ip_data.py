#!/usr/bin/env python3
"""
IP Data Sync Script
Copies ip_addresses.db and ip.txt to /home/vgs-lic with proper ownership
"""

import os
import sys
import shutil
import subprocess
import time
from pathlib import Path


class IPDataSync:
    def __init__(self):
        self.source_dir = "/root"
        self.dest_dir = "/home/vgs-lic"
        self.target_user = "vgs-lic"
        self.target_group = "vgs-lic"

        self.files_to_sync = [
            "ip_addresses.db",
            "ip.txt"
        ]

        self.log_file = "/var/log/ip_data_sync.log"

    def log(self, message, level="INFO"):
        """Log messages to console and file"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {level}: {message}"
        print(log_message)

        try:
            with open(self.log_file, "a") as f:
                f.write(log_message + "\n")
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")

    def check_root(self):
        """Check if running as root"""
        if os.geteuid() != 0:
            self.log("This script must be run as root (use sudo)", "ERROR")
            sys.exit(1)

    def check_user_exists(self):
        """Check if target user exists"""
        try:
            result = subprocess.run(
                ["id", self.target_user],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.log(f"User '{self.target_user}' exists")
                return True
            else:
                self.log(f"User '{self.target_user}' does not exist", "ERROR")
                return False
        except Exception as e:
            self.log(f"Error checking user: {e}", "ERROR")
            return False

    def ensure_dest_dir(self):
        """Ensure destination directory exists"""
        dest_path = Path(self.dest_dir)

        if not dest_path.exists():
            try:
                self.log(f"Creating destination directory: {self.dest_dir}")
                dest_path.mkdir(parents=True, exist_ok=True)

                # Set ownership on the directory
                subprocess.run(
                    ["chown", f"{self.target_user}:{self.target_group}", str(dest_path)],
                    check=True
                )
                self.log(f"Created and set ownership for {self.dest_dir}")
                return True
            except Exception as e:
                self.log(f"Error creating destination directory: {e}", "ERROR")
                return False
        else:
            self.log(f"Destination directory exists: {self.dest_dir}")
            return True

    def copy_file(self, filename):
        """Copy a single file from source to destination"""
        source_file = Path(self.source_dir) / filename
        dest_file = Path(self.dest_dir) / filename

        # Check if source file exists
        if not source_file.exists():
            self.log(f"Source file not found: {source_file}", "WARNING")
            return False

        try:
            # Create backup of existing destination file if it exists
            if dest_file.exists():
                backup_file = f"{dest_file}.backup.{int(time.time())}"
                shutil.copy2(dest_file, backup_file)
                self.log(f"Backed up existing file to: {backup_file}")

                # Set ownership on backup
                subprocess.run(
                    ["chown", f"{self.target_user}:{self.target_group}", backup_file],
                    check=True
                )

            # Copy the file
            self.log(f"Copying {source_file} to {dest_file}")
            shutil.copy2(source_file, dest_file)

            # Set ownership
            subprocess.run(
                ["chown", f"{self.target_user}:{self.target_group}", str(dest_file)],
                check=True
            )

            # Set permissions (644 - read/write for owner, read for others)
            os.chmod(dest_file, 0o644)

            # Get file size for logging
            file_size = dest_file.stat().st_size
            self.log(f"Successfully copied {filename} ({file_size} bytes)")

            return True

        except Exception as e:
            self.log(f"Error copying {filename}: {e}", "ERROR")
            return False

    def verify_ownership(self, filename):
        """Verify file ownership"""
        dest_file = Path(self.dest_dir) / filename

        if not dest_file.exists():
            return False

        try:
            result = subprocess.run(
                ["stat", "-c", "%U:%G", str(dest_file)],
                capture_output=True,
                text=True,
                check=True
            )
            owner = result.stdout.strip()
            expected = f"{self.target_user}:{self.target_group}"

            if owner == expected:
                self.log(f"✅ {filename}: ownership verified ({owner})")
                return True
            else:
                self.log(f"❌ {filename}: incorrect ownership ({owner}, expected {expected})", "WARNING")
                return False

        except Exception as e:
            self.log(f"Error verifying ownership for {filename}: {e}", "ERROR")
            return False

    def sync_all(self):
        """Sync all files"""
        self.log("=" * 60)
        self.log("IP Data Sync - Starting")
        self.log("=" * 60)

        # Check prerequisites
        self.check_root()

        if not self.check_user_exists():
            return False

        if not self.ensure_dest_dir():
            return False

        # Sync each file
        success_count = 0
        fail_count = 0

        for filename in self.files_to_sync:
            if self.copy_file(filename):
                if self.verify_ownership(filename):
                    success_count += 1
                else:
                    fail_count += 1
            else:
                fail_count += 1

        # Summary
        self.log("\n" + "=" * 60)
        self.log("Sync Summary")
        self.log("=" * 60)
        self.log(f"Source directory: {self.source_dir}")
        self.log(f"Destination directory: {self.dest_dir}")
        self.log(f"Target ownership: {self.target_user}:{self.target_group}")
        self.log(f"Successfully synced: {success_count} file(s)")

        if fail_count > 0:
            self.log(f"Failed: {fail_count} file(s)", "WARNING")

        self.log("=" * 60)

        return fail_count == 0


def main():
    """Main function"""
    try:
        syncer = IPDataSync()
        success = syncer.sync_all()
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nSync cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
