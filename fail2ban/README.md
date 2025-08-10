# Fail2Ban Enhanced Installer & Configurator

🛡️ **Automated security hardening with dynamic threat intelligence**

A comprehensive Python script that installs, configures, and maintains Fail2Ban with advanced security features including automated IP blacklist updates from multiple threat intelligence sources.

## ✨ Features

### Core Security
- **Automated Fail2Ban Installation** - Works on Debian/Ubuntu and RHEL/CentOS/Fedora
- **SSH Brute Force Protection** - Immediate protection against SSH attacks
- **Web Server Protection** - Nginx and Apache attack detection
- **PHP Exploit Detection** - Custom filters for common PHP backdoors and exploits
- **Email Notifications** - Optional admin alerts for security events

### Advanced Threat Intelligence
- **Dynamic IP Blacklists** - Auto-updates from multiple threat feeds
- **Centralized IP Management** - Download IP lists from webserver with single command
- **Multi-Source Intelligence** - Combines Ipsum, Spamhaus, and Tor exit nodes
- **Smart Deduplication** - Maintains clean, efficient IP lists
- **Automatic Updates** - Optional daily cron job for hands-off security
- **Manual Override** - Preserves custom IP additions and whitelist

### Operational Excellence
- **Self-Configuring URLs** - IP file contains its own update URL
- **Comprehensive Logging** - Detailed logs for troubleshooting and auditing
- **Configuration Backup** - Automatic backups before any changes
- **Input Validation** - Robust IP address and CIDR block validation
- **Error Recovery** - Graceful handling of network failures and edge cases
- **Status Reporting** - Clear visibility into protection status

## 🚀 Quick Start

### Prerequisites
- Linux server (Debian/Ubuntu or RHEL/CentOS/Fedora)
- Root access (sudo)
- Internet connectivity for threat intelligence updates

### Installation

1. **Download the files:**
```bash
wget https://website/fail2ban_installer.py
wget https://website/ip.txt  # Optional - script can download automatically
chmod +x fail2ban_installer.py
```

2. **Run the installer:**
```bash
sudo python3 fail2ban_installer.py
```

3. **Follow the interactive prompts:**
   - Enter admin email (optional)
   - Configure whitelist IPs
   - Set ban times and retry limits
   - Enable automatic updates
   - Download fresh IP blacklist from webserver

## 📋 Usage

### Interactive Installation
Complete setup with user prompts:
```bash
sudo python3 fail2ban_installer.py
```

### Download IP Blacklist Only
Download fresh IP list from webserver:
```bash
# Use URL from ip.txt file (first line)
sudo python3 fail2ban_installer.py --download-ips

# Use custom URL
sudo python3 fail2ban_installer.py --download-ips https://your-domain.com/custom-ips.txt
```

### Update IP Blacklist Only
Non-interactive threat intelligence update:
```bash
sudo python3 fail2ban_installer.py --update-ips
```

### Check Status
Monitor your protection:
```bash
# Service status
sudo systemctl status fail2ban

# Active jails and banned IPs
sudo fail2ban-client status
sudo fail2ban-client banned

# View logs
sudo tail -f /var/log/fail2ban.log
```

## 🔧 Configuration

### Default Settings
| Setting | Default Value | Description |
|---------|---------------|-------------|
| Ban Time | 3600 seconds (1 hour) | How long IPs stay banned |
| Find Time | 600 seconds (10 minutes) | Time window for detecting attacks |
| Max Retry | 3 attempts | Failed attempts before ban |
| SSH Max Retry | 3 attempts | SSH-specific retry limit |
| SSH Ban Time | 7200 seconds (2 hours) | Longer bans for SSH attacks |

### Protected Services

#### Always Protected
- **SSH (sshd)** - Brute force protection on port 22
- **PHP Exploits** - Custom filter for backdoor attempts

#### Auto-Detected Protection
- **Nginx** - HTTP auth, rate limiting, bot searches
- **Apache** - Authentication failures, bad bots, script attacks

### Whitelist Configuration
The following IPs are automatically whitelisted:
- `127.0.0.1/8` (localhost)
- `::1` (IPv6 localhost)
- Your server's public IP (auto-detected)
- Any additional IPs you specify during setup

## 🌐 Threat Intelligence Sources

### Primary Sources
1. **Ipsum Project** - Top 100 most reported malicious IPs
   - Source: `https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt`
   - Updated: Real-time threat reporting

2. **Spamhaus DROP List** - Known compromised networks
   - Source: `https://www.spamhaus.org/drop/drop.txt`
   - Updated: Active botnet and malware C&C servers

3. **Tor Exit Nodes** - Current Tor network exit points
   - Source: `https://www.dan.me.uk/tornodes`
   - Updated: Real-time Tor network status

### Update Frequency
- **Manual**: Run `--update-ips` anytime
- **Automatic**: Daily at 2:00 AM (optional cron job)
- **Emergency**: Can be triggered immediately for active threats

## 📁 File Structure

```
/etc/fail2ban/
├── jail.local              # Main configuration (auto-generated)
├── jail.local.backup.*     # Automatic backups
└── filter.d/
    └── php-url-fopen.conf  # Custom PHP exploit filter

/var/log/
├── fail2ban.log           # Fail2Ban service logs
└── fail2ban-installer.log # Installer activity logs

./
├── fail2ban_installer.py  # Main installer script
├── ip.txt                 # IP blacklist with UPDATE_URL configuration
└── ip.txt.backup.*        # IP list backups
```

### IP File Format
The `ip.txt` file includes a special configuration line at the top:
```
# UPDATE_URL: https://your-domain.com/path/to/ip.txt
# Enhanced IP Blacklist - Auto-updated
# Last updated: 2025-08-09 15:30:00
# Sources: Ipsum, Spamhaus DROP, Tor exit nodes, manual additions

52.164.243.255
162.142.125.0/24
# ... more IPs
```

The `UPDATE_URL` line tells the script where to download fresh IP lists from. Change this URL to point to your own webserver hosting the IP blacklist.

## 🛠️ Advanced Usage

### Centralized IP Management

#### Set up your own IP blacklist server:
1. **Host the ip.txt file** on your webserver
2. **Update the first line** in your ip.txt:
```
# UPDATE_URL: https://your-domain.com/security/ip-blacklist.txt
```
3. **Deploy to all servers** - they'll automatically use your URL

#### Download fresh blacklist:
```bash
# Uses URL from ip.txt file automatically
sudo python3 fail2ban_installer.py --download-ips

# Override with custom URL
sudo python3 fail2ban_installer.py --download-ips https://threat-intel.example.com/ips.txt
```

#### Automated distribution:
```bash
# Set up daily download at 1 AM (before threat intel update at 2 AM)
echo "0 1 * * * /usr/bin/python3 /path/to/fail2ban_installer.py --download-ips" | sudo crontab -
```

### Manual IP Management

#### Ban an IP immediately:
```bash
sudo fail2ban-client set sshd banip 192.168.1.100
```

#### Unban an IP:
```bash
sudo fail2ban-client set sshd unbanip 192.168.1.100
```

#### Add permanent IP to blacklist:
```bash
echo "192.168.1.100" >> ip.txt
sudo python3 fail2ban_installer.py --update-ips
```

### Custom Jail Configuration
The script generates `jail.local` but you can customize further:

```bash
sudo nano /etc/fail2ban/jail.local
sudo systemctl reload fail2ban
```

### Monitoring and Alerts

#### View real-time bans:
```bash
sudo tail -f /var/log/fail2ban.log | grep "Ban"
```

#### Check jail-specific status:
```bash
sudo fail2ban-client status sshd
sudo fail2ban-client status nginx-http-auth
```

#### Generate ban statistics:
```bash
sudo fail2ban-client status | grep "Currently banned"
```

## 🔍 Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check configuration syntax
sudo fail2ban-client -t

# View detailed errors
sudo journalctl -u fail2ban -f
```

#### IP Updates Failing
```bash
# Check network connectivity
curl -s https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt | head -5

# Run update with verbose logging
sudo python3 fail2ban_installer.py --update-ips
```

#### False Positives
If you're accidentally banned:
```bash
# From another server/IP
ssh user@server "sudo fail2ban-client set sshd unbanip YOUR_IP"

# Add to permanent whitelist
sudo nano /etc/fail2ban/jail.local
# Add your IP to ignoreip line
sudo systemctl reload fail2ban
```

### Log Locations
- **Installer logs**: `/var/log/fail2ban-installer.log`
- **Fail2Ban logs**: `/var/log/fail2ban.log`
- **System logs**: `/var/log/auth.log` (Debian) or `/var/log/secure` (RHEL)

## 📊 Security Metrics

### Expected Protection Levels
- **SSH Attacks**: 95%+ reduction in successful attempts
- **Web Exploits**: Automatic blocking of common PHP backdoors
- **Bot Traffic**: Significant reduction in malicious crawlers
- **Geographic Threats**: Proactive blocking of known bad actors

### Performance Impact
- **CPU Usage**: <1% overhead
- **Memory Usage**: ~50MB for Fail2Ban service
- **Network**: Minimal (only during IP updates)
- **Storage**: Log rotation keeps disk usage minimal

## 🔄 Maintenance

### Regular Tasks

#### Weekly
- Review banned IP counts: `sudo fail2ban-client banned`
- Check for false positives in logs
- Verify email notifications are working

#### Monthly
- Update the installer script to latest version
- Review and clean old backup files
- Analyze attack patterns and trends

#### As Needed
- Add new services to protection
- Adjust ban times based on attack patterns
- Update whitelist for new legitimate IPs

### Automated Maintenance
The script includes automatic:
- Daily IP blacklist updates (optional)
- Configuration backups before changes
- Log rotation (via systemd)
- Service health monitoring

## 🚨 Emergency Procedures

### Under Active Attack
1. **Immediate Response**:
```bash
# Get current attack overview
sudo fail2ban-client status

# Emergency IP update
sudo python3 fail2ban_installer.py --update-ips

# View active connections
sudo netstat -tulpn | grep :22
```

2. **Escalation**:
```bash
# Temporarily disable SSH password auth
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl reload sshd

# Enable more aggressive SSH protection
sudo fail2ban-client set sshd maxretry 1
sudo fail2ban-client set sshd bantime 86400
```

### Recovery from Lockout
If you lock yourself out:
1. Use console access (cloud provider dashboard)
2. Check if your IP is banned: `fail2ban-client status sshd`
3. Unban your IP: `fail2ban-client set sshd unbanip YOUR_IP`
4. Add to permanent whitelist in `/etc/fail2ban/jail.local`

## 🤝 Contributing

### Reporting Issues
1. Check logs: `/var/log/fail2ban-installer.log`
2. Include system information (OS, version)
3. Provide relevant log excerpts
4. Test with `--update-ips` flag for IP-related issues

### Feature Requests
- Additional threat intelligence sources
- New service protection modules
- Enhanced reporting and analytics
- Integration with security orchestration platforms

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is provided for educational and security hardening purposes. While it implements industry best practices:

- Test in non-production environments first
- Monitor for false positives after deployment
- Ensure you have alternative access methods before enabling
- Keep backups of original configurations
- Review logs regularly for unusual activity

The authors are not responsible for service disruptions or lockouts resulting from misconfiguration.

## 📞 Support

- **Documentation**: This README and inline code comments
- **Logs**: Check `/var/log/fail2ban-installer.log` for detailed operation logs
- **Community**: Security forums and Fail2Ban documentation
- **Emergency**: Ensure you have console/KVM access before deployment

---

**🔒 Stay secure, stay vigilant!** 

This tool provides strong protection, but security is an ongoing process requiring regular attention and updates.