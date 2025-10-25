#!/usr/bin/env python3
"""
Fail2Ban Automated Installer & Configurator
Installs and configures Fail2Ban with security-focused settings
Enhanced with dynamic IP blacklist updates
"""

import os
import sys
import subprocess
import socket
import time
import requests
from pathlib import Path
import ipaddress
from urllib.parse import urlparse

class Fail2BanInstaller:
    def __init__(self):
        self.config_dir = Path("/etc/fail2ban")
        self.log_file = "/var/log/fail2ban-installer.log"
        self.nginx_logs = ["/var/log/nginx/access.log", "/var/log/nginx/error.log"]
        self.apache_logs = ["/var/log/apache2/access.log", "/var/log/apache2/error.log"]
        self.ip_file = str(self.config_dir / "ip.txt")
        self.temp_ip_file = "/tmp/updated_ips.txt"
        self.default_ip_url = self.get_update_url_from_file()
        
    def get_update_url_from_file(self):
        """Read update URL from first line of ip.txt file"""
        default_url = "https://raw.githubusercontent.com/yourusername/fail2ban-ips/main/ip.txt"
        
        if not os.path.exists(self.ip_file):
            return default_url
        
        try:
            with open(self.ip_file, 'r') as f:
                first_line = f.readline().strip()
                # Look for update URL in format: # UPDATE_URL: https://...
                if first_line.startswith('# UPDATE_URL:'):
                    url = first_line.replace('# UPDATE_URL:', '').strip()
                    if url and url.startswith('http'):
                        self.log(f"Found update URL in ip.txt: {url}")
                        return url
        except Exception as e:
            self.log(f"Error reading update URL from file: {str(e)}", "WARNING")
        
        return default_url
    
    def log(self, message, level="INFO"):
        """Log messages to console and file"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {level}: {message}"
        print(log_message)
        
        try:
            with open(self.log_file, "a") as f:
                f.write(log_message + "\n")
        except:
            pass
    
    def check_root(self):
        """Check if running as root"""
        if os.geteuid() != 0:
            self.log("This script must be run as root (use sudo)", "ERROR")
            sys.exit(1)
    
    def detect_os(self):
        """Detect operating system"""
        try:
            with open("/etc/os-release", "r") as f:
                content = f.read().lower()
                if "ubuntu" in content or "debian" in content:
                    return "debian"
                elif "centos" in content or "rhel" in content or "fedora" in content:
                    return "redhat"
                else:
                    return "unknown"
        except:
            return "unknown"
    
    def run_command(self, command, description=""):
        """Run shell command with error handling"""
        if description:
            self.log(f"Executing: {description}")
        
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.log(f"Success: {description or command}")
                return True, result.stdout
            else:
                self.log(f"Failed: {description or command} - {result.stderr}", "ERROR")
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            self.log(f"Timeout: {description or command}", "ERROR")
            return False, "Command timed out"
        except Exception as e:
            self.log(f"Exception: {str(e)}", "ERROR")
            return False, str(e)
    
    def download_url(self, url, description=""):
        """Download content from URL with error handling"""
        try:
            self.log(f"Downloading: {description or url}")
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Fail2Ban-Installer/1.0'
            })
            response.raise_for_status()
            return True, response.text
        except requests.RequestException as e:
            self.log(f"Failed to download {url}: {str(e)}", "ERROR")
            return False, str(e)
        except Exception as e:
            self.log(f"Unexpected error downloading {url}: {str(e)}", "ERROR")
            return False, str(e)
    
    def download_ip_file(self, url=None, interactive=True):
        """Download ip.txt file from webserver"""
        if not url:
            url = self.default_ip_url

        if interactive:
            print("\n=== Download IP Blacklist ===")
            download_choice = input(f"Download ip.txt from webserver? (y/n) [default: y]: ").lower()
            if download_choice and download_choice != 'y':
                self.log("IP file download skipped by user")
                return True

            custom_url = input(f"Enter custom URL (or press Enter for default):\n[{url}]: ").strip()
            if custom_url:
                url = custom_url

        self.log(f"Downloading IP blacklist from: {url}")

        # Backup existing file if it exists
        if os.path.exists(self.ip_file):
            backup_file = f"{self.ip_file}.backup.{int(time.time())}"
            try:
                subprocess.run(["cp", self.ip_file, backup_file], check=True)
                self.log(f"Backed up existing IP file to: {backup_file}")
            except Exception as e:
                self.log(f"Failed to backup existing IP file: {str(e)}", "WARNING")

        # Download the file
        success, content = self.download_url(url, "IP blacklist file")
        if not success:
            self.log("Failed to download IP file from webserver", "ERROR")
            if os.path.exists(self.ip_file):
                self.log("Using existing local ip.txt file")
                return True
            else:
                self.log("No IP file available - will create minimal list", "WARNING")
                self.create_minimal_ip_file()
                return True

        # Validate and save the downloaded content
        try:
            valid_ips = 0
            for line_num, raw_line in enumerate(content.splitlines(), 1):
                line = raw_line.strip()
                if not line or line.startswith('#'):
                    continue
                if self.validate_ip(line) or self.validate_ipv6(line):
                    valid_ips += 1
                else:
                    self.log(f"Invalid IP/CIDR format on line {line_num}: {line}", "WARNING")

            if valid_ips == 0:
                self.log("Downloaded file contains no valid IPs", "ERROR")
                return False

            with open(self.ip_file, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)

            self.log(f"✅ Downloaded IP file with {valid_ips} valid IPs")
            self.log(f"Saved to: {os.path.abspath(self.ip_file)}")
            return True

        except Exception as e:
            self.log(f"Failed to save downloaded IP file: {str(e)}", "ERROR")
            return False

    def create_minimal_ip_file(self):
        """Create a minimal IP file with essential bad actors"""
        minimal_content = """# UPDATE_URL: https://raw.githubusercontent.com/yourusername/fail2ban-ips/main/ip.txt
    # Minimal IP Blacklist - Auto-generated
    # Created when webserver download failed
    # Add your own IPs below or use --update-ips to fetch from threat feeds

    # Known attackers (add your own here)
    52.164.243.255

    # Common scanning networks
    162.142.125.0/24
    167.94.138.0/24

    # Add more IPs here as needed
    """
        try:
            with open(self.ip_file, 'w') as f:
                f.write(minimal_content)
            self.log(f"Created minimal IP file: {self.ip_file}")
        except Exception as e:
            self.log(f"Failed to create minimal IP file: {str(e)}", "ERROR")

    def validate_ip(self, ip: str) -> bool:
        """Validate an IPv4 address or IPv4 CIDR block."""
        if ip is None:
            return False
        ip = ip.strip()
        if not ip or ip.startswith('#'):
            return False

        if '/' in ip:
            try:
                ip_part, cidr_part = ip.split('/', 1)
                cidr = int(cidr_part)
                if not (0 <= cidr <= 32):
                    return False
                ip = ip_part
            except (ValueError, IndexError):
                return False

        parts = ip.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False

    def update_ip_blacklist(self, interactive=True):
        """Update IP blacklist from various threat intelligence sources"""
        self.log("🔄 Starting IP blacklist update...")

        if interactive:
            update_choice = input("\nUpdate IP blacklist from threat intelligence sources? (y/n): ").lower()
            if update_choice != 'y':
                self.log("IP blacklist update skipped by user")
                return True

        new_ips = set()

        # ---------- Source 1: Ipsum (top 100 most reported IPs) ----------
        self.log("Fetching top malicious IPs from Ipsum...")
        success, content = self.download_url(
            "https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt",
            "Ipsum threat intelligence feed"
        )
        if success:
            count = 0
            for line in content.splitlines():
                if count >= 100:
                    break
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                ip = line.split()[0]
                if self.validate_ip(ip) or self.validate_ipv6(ip):
                    new_ips.add(ip)
                    count += 1
            self.log(f"Added {count} IPs from Ipsum feed")

        # ---------- Source 2: Spamhaus DROP list ----------
        self.log("Fetching Spamhaus DROP list...")
        success, content = self.download_url(
            "https://www.spamhaus.org/drop/drop.txt",
            "Spamhaus DROP list"
        )
        if success:
            count = 0
            for raw in content.splitlines():
                line = raw.strip()
                if not line or line.startswith(';') or line.startswith('#'):
                    continue
                ip_block = line.split()[0]
                if self.validate_ip(ip_block) or self.validate_ipv6(ip_block):
                    new_ips.add(ip_block)
                    count += 1
            self.log(f"Added {count} IP blocks from Spamhaus DROP list")

        # ---------- Source 3: Tor exit nodes ----------
        self.log("Fetching Tor exit nodes...")
        success, content = self.download_url(
            "https://www.dan.me.uk/tornodes",
            "Tor exit nodes list"
        )
        if success:
            count = 0
            for raw in content.splitlines():
                line = raw.strip()
                if not line:
                    continue
                # Simple heuristic: typical lines begin with the IP
                first = line.split()[0]
                if self.validate_ip(first) or self.validate_ipv6(first):
                    new_ips.add(first)
                    count += 1
                    if count >= 50:  # keep Tor additions bounded
                        break
            self.log(f"Added {count} Tor exit nodes")

        if not new_ips:
            self.log("No new IPs retrieved from sources", "WARNING")
            return False

        # ---------- Read existing ip.txt (keep only valid entries) ----------
        existing_ips = set()
        if os.path.exists(self.ip_file):
            try:
                with open(self.ip_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for raw in f:
                        line = raw.strip()
                        if not line or line.startswith('#'):
                            continue
                        if self.validate_ip(line) or self.validate_ipv6(line):
                            existing_ips.add(line)
                        else:
                            self.log(f"Skipping invalid existing entry: {line}", "WARNING")
                self.log(f"Found {len(existing_ips)} existing valid entries in {self.ip_file}")
            except Exception as e:
                self.log(f"Error reading existing IP file: {str(e)}", "ERROR")

        # ---------- Combine, dedupe, and stats ----------
        all_ips = existing_ips.union(new_ips)
        newly_added = new_ips - existing_ips
        self.log(f"Total unique IPs after update: {len(all_ips)}")
        self.log(f"Newly added IPs: {len(newly_added)}")

        # ---------- Write back with header + preserved comments ----------
        try:
            # Create a single, reusable backup path
            backup_file = None
            if os.path.exists(self.ip_file):
                backup_file = f"{self.ip_file}.backup.{int(time.time())}"
                subprocess.run(["cp", self.ip_file, backup_file], check=True)
                self.log(f"Backed up existing IP file to: {backup_file}")

            with open(self.ip_file, 'w', encoding='utf-8', newline='\n') as f:
                # Header
                f.write("# UPDATE_URL: https://raw.githubusercontent.com/yourusername/fail2ban-ips/main/ip.txt\n")
                f.write("# Enhanced IP Blacklist - Auto-updated\n")
                f.write(f"# Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("# Sources: Ipsum, Spamhaus DROP, Tor exit nodes, manual additions\n")
                f.write("#\n")
                f.write("# Lines starting with # are ignored\n")
                f.write("# Format: One IP or CIDR block per line\n")
                f.write("#\n\n")

                # Preserve comments / blank lines from original file (if any)
                if backup_file and os.path.exists(backup_file):
                    try:
                        with open(backup_file, 'r', encoding='utf-8', errors='ignore') as backup_f:
                            original_content = backup_f.read()
                            for raw in original_content.splitlines():
                                line = raw.rstrip('\n')
                                if not line.strip() or line.lstrip().startswith('#'):
                                    f.write(line + '\n')
                                # skip IPs here — we’ll write all deduped IPs below
                    except Exception as e:
                        self.log(f"Could not restore comments from backup: {e}", "WARNING")

                f.write("\n# =================================\n")
                f.write("# AUTO-UPDATED THREAT INTELLIGENCE\n")
                f.write("# =================================\n\n")

                # Robust sort key for IPv4/IPv6 addresses and networks
                def _addr_sort_key(s: str):
                    try:
                        if '/' in s:
                            net = ipaddress.ip_network(s, strict=False)
                        else:
                            # make a /32 (v4) or /128 (v6) network for uniform sorting
                            if ':' in s:
                                net = ipaddress.ip_network(f"{s}/128", strict=False)
                            else:
                                net = ipaddress.ip_network(f"{s}/32", strict=False)
                        return (net.version, net.network_address.packed, net.prefixlen)
                    except Exception:
                        # Unknown/invalid strings go to the end, but we shouldn't have any
                        return (9, s.encode(), 999)

                for ip in sorted(all_ips, key=_addr_sort_key):
                    f.write(f"{ip}\n")

            self.log(f"✅ Updated IP blacklist saved to {self.ip_file}")

            if newly_added:
                sample_new = list(newly_added)[:10]
                self.log("Sample of newly added IPs:")
                for ip in sample_new:
                    self.log(f"  + {ip}")
                if len(newly_added) > 10:
                    self.log(f"  ... and {len(newly_added) - 10} more")

            return True

        except Exception as e:
            self.log(f"Failed to write updated IP file: {str(e)}", "ERROR")
            return False


    def ban_attacker_ips(self, ip_file, jail="sshd"):
        """Ban IPs and CIDR ranges from the specified file via Fail2Ban (firewalld backend).
        - Supports IPv4 and IPv4 CIDR (per validate_ip)
        - Uses only `fail2ban-client set <jail> banip <target>` (no raw iptables fallback)
        """
        if not os.path.exists(ip_file):
            self.log(f"IP file {ip_file} not found, skipping IP banning", "WARNING")
            return True

        self.log(f"Reading IPs from {ip_file} (jail: {jail})...")
        singles = 0
        cidrs = 0
        failed = 0

        try:
            with open(ip_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue

                    # Validate (full IPv4 or IPv4/CIDR) – prevents accidental /24 from partial matches
                    if not (self.validate_ip(line) or self.validate_ipv6(line)):
                        self.log(f"Invalid IP/CIDR format on line {line_num}: {line}", "WARNING")
                        continue

                    # Apply ban via fail2ban (relies on firewalld action in the jail)
                    success, _ = self.run_command(
                        f"fail2ban-client set {jail} banip {line}",
                        f"Banning {line}"
                    )

                    if success:
                        if '/' in line:
                            cidrs += 1
                        else:
                            singles += 1
                        # Gentle pacing
                        if (singles + cidrs) % 50 == 0:
                            time.sleep(0.1)
                    else:
                        failed += 1

        except Exception as e:
            self.log(f"Error reading IP file: {str(e)}", "ERROR")
            return False

        self.log(f"✅ Banned from {ip_file} — Singles: {singles}, CIDRs: {cidrs}")
        if failed:
            self.log(f"⚠️  Failed bans: {failed}. Check jail/action config.", "WARNING")

        return failed == 0

    def setup_ip_update_cron(self):
        """Set up automatic IP list updates via cron"""
        cron_job = f"0 2 * * * /usr/bin/python3 {os.path.abspath(__file__)} --update-ips"
        
        try:
            # Check if cron job already exists
            result = subprocess.run(
                ["crontab", "-l"], 
                capture_output=True, 
                text=True
            )
            
            if cron_job not in result.stdout:
                # Add the cron job
                current_cron = result.stdout if result.returncode == 0 else ""
                new_cron = current_cron + f"\n{cron_job}\n"
                
                process = subprocess.Popen(
                    ["crontab", "-"], 
                    stdin=subprocess.PIPE, 
                    text=True
                )
                process.communicate(input=new_cron)
                
                if process.returncode == 0:
                    self.log("✅ Added daily IP update cron job (2 AM)")
                    return True
                else:
                    self.log("Failed to add cron job", "ERROR")
                    return False
            else:
                self.log("IP update cron job already exists")
                return True
                
        except Exception as e:
            self.log(f"Error setting up cron job: {str(e)}", "ERROR")
            return False
    
    def install_fail2ban(self):
        """Install Fail2Ban based on OS"""
        self.log("Starting Fail2Ban installation...")
        
        os_type = self.detect_os()
        self.log(f"Detected OS type: {os_type}")
        
        if os_type == "debian":
            # Update package list
            success, _ = self.run_command("apt update", "Updating package list")
            if not success:
                return False
            
            # Install required packages
            success, _ = self.run_command("apt install fail2ban python3-requests curl -y", "Installing Fail2Ban and dependencies")
            if not success:
                return False
                
        elif os_type == "redhat":
            # Install EPEL repository
            self.run_command("yum install epel-release -y", "Installing EPEL repository")
            
            # Install Fail2Ban and dependencies
            success, _ = self.run_command("yum install fail2ban python3-requests curl -y", "Installing Fail2Ban and dependencies")
            if not success:
                return False
        else:
            self.log("Unsupported operating system", "ERROR")
            return False
        
        # Start and enable service
        success, _ = self.run_command("systemctl start fail2ban", "Starting Fail2Ban service")
        if not success:
            return False
            
        success, _ = self.run_command("systemctl enable fail2ban", "Enabling Fail2Ban service")
        return success
    
    def get_server_ip(self):
        """Get server's public IP address"""
        try:
            # Try to get external IP
            result = subprocess.run(
                ["curl", "-s", "ifconfig.me"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except:
            pass
        
        # Fallback to local IP
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            return "127.0.0.1"
    
    def get_user_input(self):
        """Get configuration input from user"""
        config = {}
        
        print("\n=== Fail2Ban Configuration ===")
        
        # Get admin email
        config['email'] = input("Enter admin email for notifications (optional): ").strip()
        
        # Get whitelist IPs
        server_ip = self.get_server_ip()
        print(f"\nDetected server IP: {server_ip}")
        whitelist_input = input("Enter additional IPs to whitelist (comma-separated, optional): ").strip()
        
        config['whitelist'] = ["127.0.0.1/8", "::1"]
        if server_ip and server_ip != "127.0.0.1":
            config['whitelist'].append(server_ip)
        
        if whitelist_input:
            additional_ips = [ip.strip() for ip in whitelist_input.split(",") if ip.strip()]
            config['whitelist'].extend(additional_ips)
        
        # Security settings
        config['bantime'] = input("Ban time in seconds (default: 3600 = 1 hour): ").strip() or "3600"
        config['findtime'] = input("Find time in seconds (default: 600 = 10 minutes): ").strip() or "600"
        config['maxretry'] = input("Max retry attempts (default: 3): ").strip() or "3"
        
        # Auto-update option
        auto_update = input("Enable automatic daily IP blacklist updates? (y/n): ").lower() == 'y'
        config['auto_update'] = auto_update
        
        # Detect web server
        nginx_running = self.run_command("systemctl is-active nginx", "")[0]
        apache_running = self.run_command("systemctl is-active apache2", "")[0]
        
        config['webserver'] = []
        if nginx_running:
            config['webserver'].append('nginx')
            self.log("Detected Nginx web server")
        if apache_running:
            config['webserver'].append('apache')
            self.log("Detected Apache web server")
        
        return config
    
    def create_jail_config(self, config):
        """Create jail.local configuration"""
        jail_config = f"""# Fail2Ban jail.local - Auto-generated configuration
# Generated on {time.strftime("%Y-%m-%d %H:%M:%S")}

[DEFAULT]
# Ban settings
bantime = {config['bantime']}
findtime = {config['findtime']}
maxretry = {config['maxretry']}

# Whitelist IPs (never ban these)
ignoreip = {' '.join(config['whitelist'])}

# Email notifications
"""
        
        if config.get('email'):
            jail_config += f"""destemail = {config['email']}
sender = fail2ban@{socket.getfqdn()}
action = %(action_mwl)s
"""
        else:
            jail_config += """# Email notifications disabled
action = %(action_)s
"""

        # SSH protection (always enabled)
        jail_config += """
# SSH Protection
[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3
bantime = 7200

"""

        # Web server protection
        if 'nginx' in config['webserver']:
            jail_config += self.get_nginx_jails()
        
        if 'apache' in config['webserver']:
            jail_config += self.get_apache_jails()
        
        # PHP Attack Protection (always add for web servers)
        if config['webserver']:
            jail_config += self.get_php_attack_jails()
        
        return jail_config
    
    def get_nginx_jails(self):
        """Get Nginx-specific jail configurations"""
        return """# Nginx Protection
[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-botsearch]
enabled = true
port = http,https
logpath = /var/log/nginx/access.log
maxretry = 5
bantime = 7200

"""
    
    def get_apache_jails(self):
        """Get Apache-specific jail configurations"""
        return """# Apache Protection
[apache-auth]
enabled = true
port = http,https
logpath = /var/log/apache2/error.log
maxretry = 3

[apache-badbots]
enabled = true
port = http,https
logpath = /var/log/apache2/access.log
maxretry = 3

[apache-noscript]
enabled = true
port = http,https
logpath = /var/log/apache2/access.log
maxretry = 3

"""
    
    def get_php_attack_jails(self):
        """Get PHP attack protection jails"""
        return """# PHP Attack Protection
[php-url-fopen]
enabled = true
port = http,https
filter = php-url-fopen
logpath = /var/log/nginx/access.log /var/log/apache2/access.log
maxretry = 3
bantime = 7200
findtime = 300

"""
    
    def create_php_filter(self):
        """Create PHP attack filter"""
        filter_content = """# PHP Attack Filter
# Detects common PHP exploits and backdoor attempts

[Definition]
# Block requests for common PHP backdoors and exploits
failregex = ^<HOST> -.*"(GET|POST).*(\.php\?.*=|\/wp-admin\/|\/admin|100\.php|c\.php|zero\.php|yanz\.php|zwso\.php|shell\.php|backdoor\.php|r57\.php|c99\.php|wso\.php|adminfuns\.php|simple\/function\.php).*" (404|403|301)
            ^<HOST> -.*"(GET|POST).*(eval\(|base64_decode|system\(|exec\(|shell_exec|passthru\(|chr\(hexdec).*"
            ^<HOST> -.*"(GET|POST).*(\.\./|\.\.\\\\|union.*select|<script>).*"
            ^<HOST> -.*"(GET|POST).*filterStr.*randomGifFile.*"

ignoreregex =
"""
        
        filter_path = self.config_dir / "filter.d" / "php-url-fopen.conf"
        try:
            with open(filter_path, "w") as f:
                f.write(filter_content)
            self.log(f"Created PHP attack filter: {filter_path}")
            return True
        except Exception as e:
            self.log(f"Failed to create PHP filter: {str(e)}", "ERROR")
            return False
    
    def backup_existing_config(self):
            """Backup existing configuration"""
            jail_local = self.config_dir / "jail.local"
            if jail_local.exists():
                backup_path = self.config_dir / f"jail.local.backup.{int(time.time())}"
                try:
                    subprocess.run(["cp", str(jail_local), str(backup_path)], check=True)
                    self.log(f"Backed up existing config to: {backup_path}")
                    return True
                except Exception as e:
                    self.log(f"Failed to backup config: {str(e)}", "ERROR")
                    return False
            return True
        
    def apply_configuration(self, config):
        """Apply Fail2Ban configuration"""
        self.log("Applying Fail2Ban configuration...")
        
        # Backup existing config
        if not self.backup_existing_config():
            return False
        
        # Create jail.local
        jail_config = self.create_jail_config(config)
        jail_path = self.config_dir / "jail.local"
        
        try:
            with open(jail_path, "w") as f:
                f.write(jail_config)
            self.log(f"Created jail configuration: {jail_path}")
        except Exception as e:
            self.log(f"Failed to create jail config: {str(e)}", "ERROR")
            return False
        
        # Create PHP attack filter
        if not self.create_php_filter():
            return False
        
        # Test configuration
        success, output = self.run_command("fail2ban-client -t", "Testing configuration")
        if not success:
            self.log("Configuration test failed!", "ERROR")
            return False
        
        # Restart Fail2Ban
        success, _ = self.run_command("systemctl restart fail2ban", "Restarting Fail2Ban")
        if not success:
            return False
        
        # Wait a moment for service to start
        time.sleep(3)
        
        # Verify service is running
        success, _ = self.run_command("systemctl is-active fail2ban", "Verifying service status")
        return success
    
    def show_status(self):
        """Show Fail2Ban status"""
        self.log("=== Fail2Ban Status ===")
        
        # Service status
        success, output = self.run_command("systemctl status fail2ban --no-pager", "Service Status")
        if success:
            print(output)
        
        # Jail status
        success, output = self.run_command("fail2ban-client status", "Jail Status")
        if success:
            print("\nActive Jails:")
            print(output)
        
        # Show banned IPs count
        success, output = self.run_command("fail2ban-client banned", "Currently Banned IPs")
        if success:
            banned_ips = len([line for line in output.split('\n') if line.strip()])
            self.log(f"Currently banned IPs: {banned_ips}")
    
    def install_and_configure(self):
            """Main installation and configuration process"""
            print("🛡️ Fail2Ban Automated Installer & Configurator")
            print("=" * 50)
            
            # Check prerequisites
            self.check_root()
            
            # Install Fail2Ban
            if not self.install_fail2ban():
                self.log("Installation failed!", "ERROR")
                return False
            
            self.log("✅ Fail2Ban installed successfully!")
            
            # Update IP blacklist
            self.update_ip_blacklist(interactive=True)
            
            # Get configuration
            config = self.get_user_input()
            
            # Download IP file from webserver if needed
            if not os.path.exists(self.ip_file):
                self.download_ip_file(interactive=True)
            else:
                # Ask if user wants to download fresh copy
                self.download_ip_file(interactive=True)
            
            # Apply configuration
            if not self.apply_configuration(config):
                self.log("Configuration failed!", "ERROR")
                return False
            
            self.log("✅ Configuration applied successfully!")
            
            # Ban IPs from file
            self.ban_attacker_ips(self.ip_file)
            
            # Set up automatic updates if requested
            if config.get('auto_update'):
                self.setup_ip_update_cron()
            
            # Show status
            self.show_status()
            
            print("\n🎯 Installation Complete!")
            print("=" * 50)
            print("✅ Fail2Ban is installed and configured")
            print("✅ PHP attack protection enabled")
            print(f"✅ IP blacklist loaded from {self.ip_file}")
            print("✅ SSH brute force protection active")
            print("✅ Threat intelligence feeds integrated")
            
            if config.get('email'):
                print(f"✅ Email notifications enabled: {config['email']}")
            
            if config.get('auto_update'):
                print("✅ Automatic daily IP updates scheduled")
            
            print("\n📋 Useful Commands:")
            print("• Check status: sudo fail2ban-client status")
            print("• Check banned IPs: sudo fail2ban-client banned")
            print("• Unban IP: sudo fail2ban-client set <jail> unbanip <IP>")
            print("• Check logs: sudo tail -f /var/log/fail2ban.log")
            print(f"• Update IPs manually: sudo python3 {os.path.abspath(__file__)} --update-ips")
            print(f"• Download fresh IP list: sudo python3 {os.path.abspath(__file__)} --download-ips [URL]")
            
            return True
    def validate_ipv6(self, token: str) -> bool:
        """
        True if `token` is a valid IPv6 address or IPv6 CIDR (/0–/128).
        Accepts compressed forms (e.g., 2001:db8::1). Ignores blanks/comments.
        """
        import ipaddress

        if token is None:
            return False
        s = token.strip()
        if not s or s.startswith('#'):
            return False
        try:
            if '/' in s:
                ipaddress.IPv6Network(s, strict=False)  # allow host bits
            else:
                ipaddress.IPv6Address(s)
            return True
        except ValueError:
            return False

def main():
    """Main function"""
    try:
        installer = Fail2BanInstaller()
        
        # Handle command line arguments
        if len(sys.argv) > 1:
            if sys.argv[1] == "--update-ips":
                # Non-interactive IP update mode
                installer.check_root()
                success = installer.update_ip_blacklist(interactive=False)
                if success:
                    # Reload fail2ban to apply new bans
                    installer.run_command("systemctl reload fail2ban", "Reloading Fail2Ban")
                    installer.ban_attacker_ips(installer.ip_file)
                sys.exit(0 if success else 1)
            elif sys.argv[1] == "--download-ips":
                # Download IP file only
                installer.check_root()
                url = sys.argv[2] if len(sys.argv) > 2 else None
                success = installer.download_ip_file(url, interactive=False)
                sys.exit(0 if success else 1)
            elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
                print("Fail2Ban Enhanced Installer")
                print("Usage:")
                print("  python3 fail2ban_installer.py              # Interactive installation")
                print("  python3 fail2ban_installer.py --update-ips # Update threat intelligence")
                print("  python3 fail2ban_installer.py --download-ips [URL] # Download IP file")
                print("  python3 fail2ban_installer.py --help       # Show this help")
                sys.exit(0)
        
        # Normal installation mode
        success = installer.install_and_configure()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()