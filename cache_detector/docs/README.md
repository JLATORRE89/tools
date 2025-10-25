# Proxy Cache Detector & Purge Tool

A comprehensive Python tool for detecting and purging cache from various proxy servers and CDNs.

## Supported Proxy Servers

### Detection Support
- ✅ **Varnish Cache** - Full detection and purge support
- ✅ **Nginx** (proxy_cache, fastcgi_cache) - Full detection and purge support (requires ngx_cache_purge module)
- ✅ **Squid** - Full detection and purge support
- ✅ **Apache Traffic Server (ATS)** - Full detection and purge support
- ✅ **Apache mod_cache** - Detection support
- ✅ **Cloudflare CDN** - Full detection and purge support (via API)
- ✅ **HAProxy** - Detection support (HAProxy is a load balancer, not a cache)
- ✅ **Generic HTTP Caches** - Basic detection and purge via PURGE method

## Features

### Cache Detection
- Automatically detects proxy servers in the request chain
- Tests if content is being cached by comparing two sequential requests
- Analyzes cache-related HTTP headers:
  - `Cache-Control`, `Surrogate-Control`
  - `Age` (cache age)
  - `X-Cache`, `X-Cache-Hits`, `X-Cache-Lookup`
  - `Via` (proxy chain)
  - `X-Varnish`, `X-Served-By`
  - `CF-Cache-Status` (Cloudflare)
  - `X-Nginx-Cache`
  - `ETag` and `Date` headers
- Provides evidence of caching behavior

### Cache Purging
Multiple purge methods for different proxy servers:
- **Varnish**: PURGE method with optional cache tags
- **Nginx**: Via purge endpoint (requires ngx_cache_purge module)
- **Squid**: PURGE method through proxy
- **Apache Traffic Server**: PURGE method
- **Cloudflare**: API-based purging (single URLs or entire cache)
- **Generic**: Standard HTTP PURGE method for compatible caches

## Installation

### Cross-Platform Support

This tool is **fully cross-platform** and works on:
- ✅ **Windows** (10, 11, Server)
- ✅ **Linux** (Ubuntu, Debian, RHEL, Fedora, Arch, etc.)
- ✅ **macOS** (Intel & Apple Silicon)
- ✅ **BSD** and **containers**

See [PLATFORM_COMPATIBILITY.md](PLATFORM_COMPATIBILITY.md) for detailed platform-specific instructions.

### Quick Start

#### Windows
```cmd
# Install dependencies
pip install -r requirements.txt

# Or use the installer
install.bat

# Run the tool
python proxy_cache_detector.py detect https://example.com
```

#### Linux
```bash
# Install dependencies
pip3 install -r requirements.txt

# Or use the installer
chmod +x install.sh
./install.sh

# Make executable (optional)
chmod +x proxy_cache_detector.py

# Run the tool
./proxy_cache_detector.py detect https://example.com
# or
python3 proxy_cache_detector.py detect https://example.com
```

#### macOS
```bash
# Install Python 3 if needed
brew install python3

# Install dependencies
pip3 install -r requirements.txt

# Or use the installer
chmod +x install.sh
./install.sh

# Run the tool
python3 proxy_cache_detector.py detect https://example.com
```

### Requirements
- Python 3.6 or higher (Python 3.8+ recommended)
- `requests` library (automatically installed with requirements.txt)

### Manual Installation
```bash
# All platforms
pip install requests

# Or use requirements.txt
pip install -r requirements.txt
```

## Usage

**Note:** On Windows, use `python` instead of `python3` in all commands below.

### 1. Detect Cache Configuration

Test if a URL is being cached:

**Linux/macOS:**
```bash
python3 proxy_cache_detector.py detect https://example.com
```

**Windows:**
```cmd
python proxy_cache_detector.py detect https://example.com
```

Test multiple URLs:

**Linux/macOS:**
```bash
python3 proxy_cache_detector.py detect \
    https://example.com \
    https://example.com/api/data \
    https://example.com/images/logo.png
```

**Windows:**
```cmd
python proxy_cache_detector.py detect https://example.com https://example.com/api/data https://example.com/images/logo.png
```

Custom delay between requests (default 3 seconds):
```bash
# All platforms
python3 proxy_cache_detector.py detect https://example.com --delay 5
```

Custom timeout (default 10 seconds):
```bash
# All platforms
python3 proxy_cache_detector.py detect https://example.com --timeout 15
```

Using a proxy server:
```bash
# All platforms (HTTP proxy)
python3 proxy_cache_detector.py detect https://example.com --proxy http://proxy.example.com:8080

# SOCKS5 proxy
python3 proxy_cache_detector.py detect https://example.com --proxy socks5://proxy.example.com:1080

# Proxy with authentication
python3 proxy_cache_detector.py detect https://example.com --proxy http://user:pass@proxy.example.com:8080
```

### 2. Purge Varnish Cache

Basic purge:
```bash
python3 proxy_cache_detector.py purge-varnish https://example.com/page
```

With custom host and port:
```bash
python3 proxy_cache_detector.py purge-varnish https://example.com/page \
    --host 192.168.1.10 \
    --port 6081
```

Purge with cache tags (CloudPanel/Varnish):
```bash
python3 proxy_cache_detector.py purge-varnish https://example.com \
    --cache-tags "tag1,tag2,tag3"
```

### 3. Purge Nginx Cache

Requires ngx_cache_purge module:
```bash
python3 proxy_cache_detector.py purge-nginx https://example.com/page
```

Custom purge endpoint:
```bash
python3 proxy_cache_detector.py purge-nginx https://example.com/page \
    --purge-path /cache-purge
```

### 4. Purge Squid Cache

```bash
python3 proxy_cache_detector.py purge-squid https://example.com/page
```

With custom host and port:
```bash
python3 proxy_cache_detector.py purge-squid https://example.com/page \
    --host 192.168.1.20 \
    --port 3128
```

### 5. Purge Apache Traffic Server

```bash
python3 proxy_cache_detector.py purge-ats https://example.com/page
```

With custom configuration:
```bash
python3 proxy_cache_detector.py purge-ats https://example.com/page \
    --host 127.0.0.1 \
    --port 8080
```

### 6. Purge Cloudflare Cache

Purge specific URLs (up to 30 per request):
```bash
python3 proxy_cache_detector.py purge-cloudflare \
    --zone-id YOUR_ZONE_ID \
    --token YOUR_API_TOKEN \
    --urls https://example.com/page1 https://example.com/page2
```

Purge entire cache (use with caution):
```bash
python3 proxy_cache_detector.py purge-cloudflare \
    --zone-id YOUR_ZONE_ID \
    --token YOUR_API_TOKEN \
    --purge-everything
```

### 7. Generic PURGE Method

Try the standard HTTP PURGE method (works with many caches):
```bash
python3 proxy_cache_detector.py purge-generic https://example.com/page
```

### 8. Using a Proxy Server

All commands support the `--proxy` option to route requests through a proxy server:

```bash
# HTTP proxy
python3 proxy_cache_detector.py detect https://example.com --proxy http://proxy.example.com:8080

# SOCKS5 proxy (requires requests[socks] package)
python3 proxy_cache_detector.py detect https://example.com --proxy socks5://proxy.example.com:1080

# Proxy with authentication
python3 proxy_cache_detector.py purge-varnish https://example.com/page \
    --proxy http://username:password@proxy.example.com:8080

# Using proxy with purge commands
python3 proxy_cache_detector.py purge-cloudflare \
    --zone-id YOUR_ZONE_ID \
    --token YOUR_API_TOKEN \
    --urls https://example.com/page \
    --proxy http://corporate-proxy.com:3128
```

**Note:** For SOCKS proxy support, install the optional dependency:
```bash
pip install requests[socks]
```

## Output Examples

### Cache Detection Output
```
>>> Testing https://example.com/api/data

================================================================================
CACHE DETECTION RESULTS
================================================================================

URL: https://example.com/api/data
Status: 200 → 200
Detected Proxies: Varnish, Nginx (with caching)
Is Cached: YES
Evidence:
  - Age increased from 45s to 48s
  - X-Cache indicates HIT
Cache-Control: public, max-age=3600
Age: 45 → 48
X-Cache: HIT → HIT
Via: 1.1 varnish (Varnish/6.0)
Date Delta: 3.0 seconds
--------------------------------------------------------------------------------
```

### Purge Operation Output
```
Varnish PURGE: SUCCESS
Message: Purged successfully
```

## Understanding Detection

### Cache Evidence
The tool looks for several indicators that content is cached:

1. **Age Header Increases**: If the `Age` header increases between requests, content is served from cache
2. **X-Cache HIT**: Many caches set `X-Cache: HIT` when serving cached content
3. **Cloudflare Status**: `CF-Cache-Status: HIT` indicates Cloudflare cache hit
4. **ETag Consistency**: Same ETag with minimal date change suggests caching
5. **Via Header**: Shows the proxy chain and often includes proxy software names

### Detected Proxies
The tool identifies proxy types based on:
- **Varnish**: `X-Varnish` header or "varnish" in `Via` header
- **Nginx**: `X-Nginx-Cache` header or "nginx" in `Server` header with cache indicators
- **Squid**: "squid" in `Via` or `X-Cache` headers
- **Apache Traffic Server**: "ATS" in `Via` or `Server` headers
- **Cloudflare**: `CF-Cache-Status` header or "cloudflare" in `Server` header
- **Apache mod_cache**: "apache" in `X-Cache` header

## Configuration Notes

### Varnish Configuration
For Varnish purging to work, your VCL must allow PURGE requests:

```vcl
acl purge {
    "localhost";
    "127.0.0.1";
    # Add your IP addresses
}

sub vcl_recv {
    if (req.method == "PURGE") {
        if (!client.ip ~ purge) {
            return(synth(405, "Not allowed."));
        }
        return (purge);
    }
}
```

### Nginx Configuration
For Nginx cache purging, you need the ngx_cache_purge module:

```nginx
location ~ /purge(/.*) {
    allow 127.0.0.1;
    deny all;
    proxy_cache_purge cache_zone $1$is_args$args;
}
```

### Squid Configuration
Enable PURGE in squid.conf:

```
acl Purge method PURGE
http_access allow localhost Purge
http_access allow localnet Purge
http_access deny Purge
```

### Apache Traffic Server Configuration
PURGE is enabled by default but restricted to localhost. To allow from other IPs, configure in remap.config:

```
map http://example.com http://backend.example.com @action=allow @src_ip=127.0.0.1
```

### Cloudflare API Setup
1. Get your Zone ID from Cloudflare dashboard
2. Create an API token with "Cache Purge" permissions
3. Use the token with the purge-cloudflare command

## Troubleshooting

### "Connection refused"
- Verify the proxy server is running
- Check the host and port settings
- Ensure firewall rules allow connections

### "405 Method Not Allowed" or "403 Forbidden"
- Your IP may not be in the allowed ACL
- PURGE method may be disabled in configuration
- Check proxy server logs for details

### "404 Not Found" on Nginx purge
- ngx_cache_purge module may not be installed
- Check the purge-path configuration
- Verify the URL path matches cached content

### No cache detected but content is cached
- Cache may not set standard headers
- Try increasing the delay between requests
- Check for Set-Cookie headers (usually prevents caching)

## Advanced Usage

### Scripting
Use the tool in scripts for automated cache management:

```bash
#!/bin/bash
# Purge multiple URLs from Varnish
urls=(
    "https://example.com/page1"
    "https://example.com/page2"
    "https://example.com/api/data"
)

for url in "${urls[@]}"; do
    python3 proxy_cache_detector.py purge-varnish "$url"
done
```

### Python Module Usage
You can also import and use the classes directly:

```python
from proxy_cache_detector import ProxyCacheDetector, ProxyCachePurger

# Detect cache
detector = ProxyCacheDetector()
result = detector.test_caching('https://example.com')
print(f"Detected: {result['detected_proxies']}")
print(f"Is cached: {result['is_cached']}")

# Purge cache
purger = ProxyCachePurger()
result = purger.purge_varnish('https://example.com')
print(f"Success: {result['success']}")
```

## Platform-Specific Notes

### Windows
- Use `python` instead of `python3` in commands
- No line continuation with backslash `\` - put all arguments on one line
- Both PowerShell and Command Prompt work
- Ensure Python is in your PATH environment variable

### Linux/macOS
- Use `python3` for explicit Python 3 usage
- Can make script executable: `chmod +x proxy_cache_detector.py`
- Then run directly: `./proxy_cache_detector.py`
- Use backslash `\` for line continuation in bash

### All Platforms
- If behind a corporate proxy, set `HTTP_PROXY` and `HTTPS_PROXY` environment variables
- The tool requires outbound network access on standard HTTP/HTTPS ports
- No special privileges (root/Administrator) required

## Comparison with PowerShell Version

This Python version improves upon the original PowerShell script:

✅ Cross-platform (Windows, Linux, macOS)
✅ More proxy server support (7+ types)
✅ Cache purging capabilities (6 methods)
✅ Better cache detection logic
✅ API integration (Cloudflare)
✅ Structured output and error handling
✅ Extensible class-based design
✅ Command-line interface with subcommands

## Contributing

Feel free to extend this tool to support additional proxy servers or CDN providers!

## License

This tool is provided as-is for cache management purposes.

## References

- [Varnish Cache Documentation](http://varnish-cache.org/docs/)
- [Nginx Cache Purge Module](https://www.getpagespeed.com/server-setup/ngx_cache_purge-closing-the-gap-with-varnish)
- [Apache Traffic Server Docs](https://docs.trafficserver.apache.org/)
- [Squid Cache Wiki](http://wiki.squid-cache.org/)
- [Cloudflare API Documentation](https://developers.cloudflare.com/api/)
- [CloudPanel Varnish Guide](https://www.cloudpanel.io/docs/v2/frontend-area/varnish-cache/)