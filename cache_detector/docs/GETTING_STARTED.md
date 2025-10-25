# Getting Started with Proxy Cache Detector

## Platform Support

This tool works on **all platforms**:
- ✅ **Windows** (10, 11, Server)
- ✅ **Linux** (All distributions)
- ✅ **macOS** (Intel & Apple Silicon)

**Choose your platform below:**

---

## Windows Quick Start (2 minutes)

### Step 1: Install
```cmd
REM Option 1: Use the installer
install.bat

REM Option 2: Manual installation
pip install -r requirements.txt
```

### Step 2: Test Detection
```cmd
python proxy_cache_detector.py detect https://example.com
```

### Step 3: View Help
```cmd
python proxy_cache_detector.py --help
```

---

## Linux/macOS Quick Start (2 minutes)

### Step 1: Install
```bash
# Option 1: Use the installer
chmod +x install.sh
./install.sh

# Option 2: Manual installation
pip3 install -r requirements.txt
```

### Step 2: Test Detection
```bash
python3 proxy_cache_detector.py detect https://example.com
```

### Step 3: View Help
```bash
python3 proxy_cache_detector.py --help
```

---

## Platform Notes

**Windows:**
- Use `python` instead of `python3`
- Use Command Prompt or PowerShell
- No backslash line continuation (put args on one line)

**Linux/macOS:**
- Use `python3` for explicit Python 3
- Can make script executable: `chmod +x proxy_cache_detector.py`
- Then run directly: `./proxy_cache_detector.py`

**All Platforms:**
- Requires Python 3.6+ (Python 3.8+ recommended)
- Only dependency: `requests` library
- No special privileges required

## What This Tool Does

✅ **Detects** which proxy servers are caching your website
✅ **Tests** if your content is actually being cached
✅ **Purges** cache when you need to update content
✅ **Supports** Varnish, Nginx, Squid, Apache Traffic Server, Cloudflare, and more

## Common Tasks

### "Is my site being cached?"

**Windows:**
```cmd
python proxy_cache_detector.py detect https://yoursite.com
```

**Linux/macOS:**
```bash
python3 proxy_cache_detector.py detect https://yoursite.com
```

**Look for:**
- `Is Cached: YES` - Your site IS cached
- `Detected Proxies:` - Which caching systems are active
- `Evidence:` - Proof of caching (like increasing Age header)

### "I updated my site, purge the old version"

**For Varnish (Windows):**
```cmd
python proxy_cache_detector.py purge-varnish https://yoursite.com/updated-page
```

**For Varnish (Linux/macOS):**
```bash
python3 proxy_cache_detector.py purge-varnish https://yoursite.com/updated-page
```

**For Nginx (Windows):**
```cmd
python proxy_cache_detector.py purge-nginx https://yoursite.com/updated-page
```

**For Nginx (Linux/macOS):**
```bash
python3 proxy_cache_detector.py purge-nginx https://yoursite.com/updated-page
```

**For Cloudflare (Windows):**
```cmd
python proxy_cache_detector.py purge-cloudflare --zone-id YOUR_ZONE_ID --token YOUR_API_TOKEN --urls https://yoursite.com/updated-page
```

**For Cloudflare (Linux/macOS):**
```bash
python3 proxy_cache_detector.py purge-cloudflare \
    --zone-id YOUR_ZONE_ID \
    --token YOUR_API_TOKEN \
    --urls https://yoursite.com/updated-page
```

### "Check multiple pages"

**Windows:**
```cmd
python proxy_cache_detector.py detect https://yoursite.com https://yoursite.com/about https://yoursite.com/contact
```

**Linux/macOS:**
```bash
python3 proxy_cache_detector.py detect \
    https://yoursite.com \
    https://yoursite.com/about \
    https://yoursite.com/contact
```

## Understanding the Output

### Detection Output Example:
```
URL: https://example.com
Status: 200 → 200
Detected Proxies: Varnish, Nginx (with caching)
Is Cached: YES
Evidence:
  - Age increased from 45s to 48s
  - X-Cache indicates HIT
Cache-Control: public, max-age=3600
Age: 45 → 48
```

**What it means:**
- ✅ Site is definitely cached
- ✅ Running Varnish and Nginx
- ✅ Cache age is increasing (proof of caching)
- ✅ X-Cache shows HIT (serving from cache)

### Purge Output Example:
```
Varnish PURGE: SUCCESS
Message: Purged successfully
```

**What it means:**
- ✅ Cache was successfully cleared
- ✅ Next request will fetch fresh content

## When to Use This Tool

### Development
- ✅ Test if your cache configuration is working
- ✅ Verify cache headers are set correctly
- ✅ Debug why content isn't caching

### Production
- ✅ Purge cache after deploying updates
- ✅ Clear cache for specific pages
- ✅ Monitor cache effectiveness

### Troubleshooting
- ✅ Find out why pages are loading slowly
- ✅ Check if cache is serving stale content
- ✅ Verify proxy configuration

## File Guide

📄 **proxy_cache_detector.py** - The main tool (start here!)
📘 **README.md** - Complete documentation (read when you have time)
⚡ **QUICK_REFERENCE.md** - Command cheat sheet (bookmark this!)
💡 **examples.py** - Working code examples (run to see it work)
📝 **PROJECT_SUMMARY.md** - Technical overview (for developers)

## Basic Workflow

```
1. Detect cache
   ↓
2. Is it cached?
   ├─ YES → Great! Check cache hit rate
   └─ NO → Fix cache configuration
   
3. Need to update?
   ↓
4. Purge cache
   ↓
5. Verify with detect again
```

## Common Issues & Solutions

### "Connection refused"
**Problem:** Can't connect to proxy server
**Solution:** 
- Check if proxy is running: `systemctl status varnish`
- Verify host/port settings

### "Method not allowed (405)"
**Problem:** PURGE method is disabled
**Solution:** 
- Check proxy configuration allows PURGE
- Verify your IP is in the allowed ACL

### "Not cached"
**Problem:** Content isn't being cached
**Solution:**
- Check Cache-Control headers
- Verify proxy configuration
- Look for Set-Cookie headers (usually prevents caching)

## Next Steps

1. ✅ **Try it now** - Run detection on your site
2. 📖 **Read README.md** - Learn all features
3. 💻 **Run examples.py** - See practical examples
4. ⚡ **Bookmark QUICK_REFERENCE.md** - Keep commands handy

## Need Help?

1. Check error message
2. Review README.md
3. Look at examples.py
4. Check proxy server logs

## One-Line Commands for Copy-Paste

### Windows
```cmd
REM Install
pip install requests

REM Detect your site
python proxy_cache_detector.py detect https://yoursite.com

REM Purge Varnish
python proxy_cache_detector.py purge-varnish https://yoursite.com/page

REM Purge Nginx
python proxy_cache_detector.py purge-nginx https://yoursite.com/page

REM Check if tool is working
python proxy_cache_detector.py --help
```

### Linux/macOS
```bash
# Install
pip3 install requests

# Detect your site
python3 proxy_cache_detector.py detect https://yoursite.com

# Purge Varnish
python3 proxy_cache_detector.py purge-varnish https://yoursite.com/page

# Purge Nginx
python3 proxy_cache_detector.py purge-nginx https://yoursite.com/page

# Check if tool is working
python3 proxy_cache_detector.py --help
```

## Tips

💡 Use `--delay 5` for slower sites
💡 Multiple URLs can be tested at once
💡 PURGE requires proper proxy configuration
💡 Start with detection before trying purge
💡 Check proxy logs if purge fails

## That's It!

You're ready to use the Proxy Cache Detector. Start with:

**Windows:**
```cmd
python proxy_cache_detector.py detect https://yoursite.com
```

**Linux/macOS:**
```bash
python3 proxy_cache_detector.py detect https://yoursite.com
```

## Additional Resources

📄 **README.md** - Detailed documentation
⚡ **QUICK_REFERENCE.md** - Quick command reference
🖥️ **PLATFORM_COMPATIBILITY.md** - Platform-specific details
💻 **examples.py** - Working code examples