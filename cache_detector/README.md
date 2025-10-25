# Proxy Cache Detector & Purge Tool

A comprehensive Python tool for detecting and purging cache from various proxy servers and CDNs.

## Quick Start

### Installation

**Windows:**
```cmd
install.bat
```

**Linux/macOS:**
```bash
chmod +x install.sh
./install.sh
```

### Activate Virtual Environment

After installation, activate the virtual environment:

**Windows:**
```cmd
venv\Scripts\activate
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

### Basic Usage

```bash
# Detect cache
python proxy_cache_detector.py detect https://example.com

# Purge Varnish cache
python proxy_cache_detector.py purge-varnish https://example.com/page

# Get help
python proxy_cache_detector.py --help
```

## Documentation

📄 **[Full Documentation](docs/README.md)** - Complete guide with all features

⚡ **[Quick Reference](docs/QUICK_REFERENCE.md)** - Command cheat sheet

💡 **[Getting Started](docs/GETTING_STARTED.md)** - Step-by-step tutorial

🖥️ **[Platform Compatibility](docs/PLATFORM_COMPATIBILITY.md)** - Windows, Linux, macOS details

📝 **[Project Summary](docs/PROJECT_SUMMARY.md)** - Technical overview

📑 **[Documentation Index](docs/INDEX.md)** - All documentation

## Features

✅ **Detects** 8+ types of proxy/cache servers (Varnish, Nginx, Squid, Cloudflare, etc.)
✅ **Tests** if content is being cached
✅ **Purges** cache with multiple methods
✅ **Cross-platform** - Windows, Linux, macOS
✅ **Easy to use** - Simple command-line interface

## Supported Cache Systems

- Varnish Cache
- Nginx (proxy_cache, fastcgi_cache)
- Squid
- Apache Traffic Server (ATS)
- Cloudflare CDN
- HAProxy (detection only)
- Apache mod_cache
- Generic HTTP caches

## Requirements

- Python 3.6+ (Python 3.8+ recommended)
- Virtual environment (automatically created by installer)
- `requests` library (automatically installed)

## License

This tool is provided as-is for cache management purposes.
