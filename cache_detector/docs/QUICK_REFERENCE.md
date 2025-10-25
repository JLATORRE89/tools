# Quick Reference Guide

## Platform Note

**Windows:** Use `python` instead of `python3` in all commands below.
**Linux/macOS:** Use `python3` as shown.

## Installation

### Windows
```cmd
pip install -r requirements.txt
REM Or use installer: install.bat
```

### Linux/macOS
```bash
pip3 install -r requirements.txt
chmod +x proxy_cache_detector.py
# Or use installer: ./install.sh
```

## Common Commands

### Detect Cache
```bash
# Single URL
python3 proxy_cache_detector.py detect https://example.com

# Multiple URLs
python3 proxy_cache_detector.py detect https://example.com https://example.com/api

# With custom delay
python3 proxy_cache_detector.py detect https://example.com --delay 5
```

### Purge Varnish
```bash
# Basic
python3 proxy_cache_detector.py purge-varnish https://example.com/page

# With cache tags
python3 proxy_cache_detector.py purge-varnish https://example.com --cache-tags "tag1,tag2"

# Custom host/port
python3 proxy_cache_detector.py purge-varnish https://example.com --host 192.168.1.10 --port 6081
```

### Purge Nginx
```bash
# Basic
python3 proxy_cache_detector.py purge-nginx https://example.com/page

# Custom purge path
python3 proxy_cache_detector.py purge-nginx https://example.com --purge-path /cache-purge
```

### Purge Squid
```bash
python3 proxy_cache_detector.py purge-squid https://example.com/page --host 127.0.0.1 --port 3128
```

### Purge Apache Traffic Server
```bash
python3 proxy_cache_detector.py purge-ats https://example.com/page --host 127.0.0.1 --port 8080
```

### Purge Cloudflare
```bash
# Specific URLs
python3 proxy_cache_detector.py purge-cloudflare \
    --zone-id ZONE_ID \
    --token API_TOKEN \
    --urls https://example.com/page1 https://example.com/page2

# Everything (caution!)
python3 proxy_cache_detector.py purge-cloudflare \
    --zone-id ZONE_ID \
    --token API_TOKEN \
    --purge-everything
```

### Generic Purge
```bash
python3 proxy_cache_detector.py purge-generic https://example.com/page
```

## Batch Operations

### Purge Multiple URLs

**Windows (PowerShell):**
```powershell
# Read from file
Get-Content urls.txt | ForEach-Object {
    python proxy_cache_detector.py purge-varnish $_
}

# Array of URLs
$urls = @(
    "https://site1.com"
    "https://site2.com"
    "https://site3.com"
)
foreach ($url in $urls) {
    python proxy_cache_detector.py purge-varnish $url
}
```

**Windows (Batch Script):**
```batch
@echo off
for /F "tokens=*" %%A in (urls.txt) do (
    python proxy_cache_detector.py purge-varnish "%%A"
)
```

**Linux/macOS (Bash):**
```bash
#!/bin/bash
for url in $(cat urls.txt); do
    python3 proxy_cache_detector.py purge-varnish "$url"
done
```

### Detect Multiple Sites

**Windows (PowerShell):**
```powershell
$urls = "https://site1.com", "https://site2.com", "https://site3.com"
python proxy_cache_detector.py detect $urls
```

**Linux/macOS (Bash):**
```bash
#!/bin/bash
urls=(
    "https://site1.com"
    "https://site2.com"
    "https://site3.com"
)
python3 proxy_cache_detector.py detect "${urls[@]}"
```

## Proxy Server Ports (Defaults)

| Proxy Server           | Default Port | Config Location (Linux)          | Config Location (Windows)              |
|------------------------|--------------|----------------------------------|----------------------------------------|
| Varnish                | 6081         | /etc/varnish/default.vcl         | C:\Program Files\Varnish\etc\          |
| Nginx                  | 80/443       | /etc/nginx/nginx.conf            | C:\nginx\conf\nginx.conf               |
| Squid                  | 3128         | /etc/squid/squid.conf            | C:\squid\etc\squid.conf                |
| Apache Traffic Server  | 8080         | /etc/trafficserver/              | C:\ats\etc\trafficserver\              |
| HAProxy                | 80/443       | /etc/haproxy/haproxy.cfg         | C:\haproxy\haproxy.cfg                 |

**Note:** Windows paths may vary depending on installation method.

## Cache Headers Explained

| Header                | Description                                    |
|-----------------------|------------------------------------------------|
| `Cache-Control`       | Caching directives (max-age, no-cache, etc.)  |
| `Surrogate-Control`   | Cache directives for proxies only             |
| `Age`                 | Time in seconds object has been in cache      |
| `X-Cache`             | HIT/MISS status from cache                    |
| `Via`                 | Proxy chain information                       |
| `X-Varnish`           | Varnish-specific cache information            |
| `CF-Cache-Status`     | Cloudflare cache status                       |
| `ETag`                | Entity tag for cache validation               |

## Return Codes

| Code | Meaning                                           |
|------|---------------------------------------------------|
| 200  | Success / Cache HIT                               |
| 204  | Success / No Content                              |
| 404  | Not Found / Not in cache                          |
| 405  | Method Not Allowed / PURGE not supported          |
| 403  | Forbidden / IP not in ACL                         |

## Troubleshooting

### Can't connect to proxy

**Windows:**
```cmd
REM Check if service is running
sc query VarnishCache
sc query nginx
sc query Squid

REM Check listening ports
netstat -ano | findstr ":6081 :3128 :8080"
```

**Linux/macOS:**
```bash
# Check if service is running
sudo systemctl status varnish
sudo systemctl status nginx
sudo systemctl status squid

# Check listening ports
sudo netstat -tlnp | grep -E '(6081|3128|8080)'
# Or on macOS
sudo lsof -i :6081,3128,8080
```

### PURGE forbidden

**Windows:**
```cmd
REM Check Varnish config
varnishd -C -f "C:\Program Files\Varnish\etc\default.vcl" | findstr "acl purge"

REM Check Nginx config
nginx -T | findstr "cache_purge"
```

**Linux/macOS:**
```bash
# Check ACL in Varnish
sudo varnishd -C -f /etc/varnish/default.vcl | grep -A 10 "acl purge"

# Check Nginx config
sudo nginx -T | grep -A 5 "cache_purge"

# Check Squid ACL
sudo grep -A 5 "acl Purge" /etc/squid/squid.conf
```

### Check cache is working

**Windows (PowerShell):**
```powershell
# Multiple requests should show increasing Age
curl.exe -I https://example.com | Select-String "Age"
Start-Sleep -Seconds 2
curl.exe -I https://example.com | Select-String "Age"
```

**Linux/macOS:**
```bash
# Multiple requests should show increasing Age
curl -I https://example.com | grep Age
sleep 2
curl -I https://example.com | grep Age
```

## Python Module Usage

```python
from proxy_cache_detector import ProxyCacheDetector, ProxyCachePurger

# Detect
detector = ProxyCacheDetector()
result = detector.test_caching('https://example.com')
print(result['detected_proxies'])

# Purge
purger = ProxyCachePurger()
result = purger.purge_varnish('https://example.com')
print(result['success'])
```

## Environment Variables (Optional)

**Windows (Command Prompt):**
```cmd
set VARNISH_HOST=127.0.0.1
set VARNISH_PORT=6081
set SQUID_HOST=127.0.0.1
set SQUID_PORT=3128

REM Use in commands
python proxy_cache_detector.py purge-varnish https://example.com --host %VARNISH_HOST% --port %VARNISH_PORT%
```

**Windows (PowerShell):**
```powershell
$env:VARNISH_HOST = "127.0.0.1"
$env:VARNISH_PORT = "6081"

python proxy_cache_detector.py purge-varnish https://example.com --host $env:VARNISH_HOST --port $env:VARNISH_PORT
```

**Linux/macOS:**
```bash
# Set defaults for your environment
export VARNISH_HOST="127.0.0.1"
export VARNISH_PORT="6081"
export SQUID_HOST="127.0.0.1"
export SQUID_PORT="3128"

# Use in scripts
python3 proxy_cache_detector.py purge-varnish https://example.com \
    --host $VARNISH_HOST \
    --port $VARNISH_PORT
```

## Useful One-Liners

**Windows (PowerShell):**
```powershell
# Check if URL is cached
python proxy_cache_detector.py detect https://example.com | Select-String "Is Cached"

# Purge and verify
python proxy_cache_detector.py purge-varnish https://example.com
Start-Sleep -Seconds 1
python proxy_cache_detector.py detect https://example.com

# Test multiple endpoints
@("/", "/api", "/images") | ForEach-Object {
    python proxy_cache_detector.py detect "https://example.com$_"
}
```

**Linux/macOS:**
```bash
# Check if URL is cached
python3 proxy_cache_detector.py detect https://example.com | grep "Is Cached"

# Purge and verify
python3 proxy_cache_detector.py purge-varnish https://example.com && \
    sleep 1 && \
    python3 proxy_cache_detector.py detect https://example.com

# Test multiple endpoints
for path in / /api /images; do
    python3 proxy_cache_detector.py detect "https://example.com$path"
done
```

## Help

**All Platforms:**
```bash
# General help (use 'python' on Windows, 'python3' on Linux/macOS)
python3 proxy_cache_detector.py --help

# Command-specific help
python3 proxy_cache_detector.py detect --help
python3 proxy_cache_detector.py purge-varnish --help
```