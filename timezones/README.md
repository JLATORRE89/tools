````markdown
# Timezone API

FastAPI service that returns timezone information based on IP address. This is a replacement for worldtimeapi.org when their API is down.

## Features

- 🌍 IP to timezone lookup using GeoIP2 database
- 🕐 Current time in the detected timezone
- 🔄 UTC offset calculation
- 📍 Detailed location information
- 🚀 Fast and lightweight FastAPI server
- 🔒 CORS enabled for cross-origin requests

## Installation

### Option 1: Podman (Recommended for CloudPanel)

**Quick Setup:**
```bash
cd timezones
chmod +x setup-podman.sh
./setup-podman.sh
````

The script will:

* Install Podman (if needed)
* Download GeoIP database
* Build container image
* Start the service
* Generate systemd service (optional)

**Manual Podman Setup:**

```bash
# Build image
podman build -t timezone-api:latest .

# Run container
podman run -d \
    --name timezone-api \
    -p 8000:8000 \
    -v ./geodb:/app/geodb:ro,z \
    -e TZ=UTC \
    --restart unless-stopped \
    timezone-api:latest
```

**Using podman-compose:**

```bash
pip3 install podman-compose
podman-compose up -d
```

### Option 2: Docker

**Quick Setup:**

```bash
cd timezones
chmod +x setup-docker.sh
./setup-docker.sh
```

**Using docker-compose:**

```bash
docker-compose up -d
```

### Option 3: Native Python

**Install Dependencies:**

```bash
cd timezones
pip3 install -r requirements.txt
```

**Download GeoIP2 Database:**

```bash
python3 download_geodb.py
```

**Run the Server:**

```bash
# Development mode
python3 main.py

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Get Timezone for Client IP (Auto-detect)

```http
GET /timezone/auto
```

**Example:**

```bash
curl http://localhost:8000/timezone/auto
```

**Response:**

```json
{
  "ip": "8.8.8.8",
  "timezone": "America/Los_Angeles",
  "utc_offset": "-08:00",
  "current_time": "2024-01-15T10:30:45.123456-08:00",
  "abbreviation": "PST",
  "is_dst": false
}
```

### Get Timezone for Specific IP

```http
GET /timezone/{ip}
```

**Example:**

```bash
curl http://localhost:8000/timezone/8.8.8.8
```

**Response:**

```json
{
  "ip": "8.8.8.8",
  "timezone": "America/Los_Angeles",
  "utc_offset": "-08:00",
  "current_time": "2024-01-15T10:30:45.123456-08:00",
  "abbreviation": "PST",
  "is_dst": false
}
```

### Health Check (Global)

```http
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T18:30:45.123456",
  "service": "timezone-api"
}
```

### Health Check (Timezone API)

```http
GET /timezone/health
```

**Response (example):**

```json
{
  "service": "timezone-api",
  "version": "1.1.0",
  "status": "ok",
  "geodb_loaded": true,
  "current_time_utc": "2025-11-28T20:22:45.123456+00:00"
}
```

### About / Attribution

```http
GET /timezone/about
```

Returns service metadata and the required MaxMind attribution:

> "This product includes GeoLite2 data created by MaxMind, available from [https://www.maxmind.com](https://www.maxmind.com)."

---

## Using This API from Other VoidGuard Services

In production, the Timezone API is exposed internally at:

* **Base URL:** `https://licenses.voidguardsecurity.com/timezone`

### Common Endpoints

* **Auto-detect client IP timezone**

  ```http
  GET /timezone/auto
  ```

  Example (from another backend):

  ```bash
  curl "https://licenses.voidguardsecurity.com/timezone/auto"
  ```

* **Timezone for a specific IP**

  ```http
  GET /timezone/{ip}
  ```

  Example:

  ```bash
  curl "https://licenses.voidguardsecurity.com/timezone/8.8.8.8"
  ```

* **Healthcheck**

  ```http
  GET /timezone/health
  ```

  Returns JSON with `status`, `geodb_loaded`, and `current_time_utc`.
  Use this for monitoring and readiness checks.

* **About / Attribution**

  ```http
  GET /timezone/about
  ```

  Returns service metadata and the required MaxMind attribution.

### Python Example (requests)

```python
import requests

BASE_URL = "https://licenses.voidguardsecurity.com/timezone"

def get_timezone_for_ip(ip: str) -> dict:
    resp = requests.get(f"{BASE_URL}/{ip}", timeout=5)
    resp.raise_for_status()
    return resp.json()

def get_client_timezone() -> dict:
    resp = requests.get(f"{BASE_URL}/auto", timeout=5)
    resp.raise_for_status()
    return resp.json()
```

Other VoidGuard services (e.g., licensing, logging, analytics) should call this API instead of talking directly to the GeoLite2 database.

---

## Production Deployment

### CloudPanel with Podman (Recommended)

1. **Run the setup script:**

   ```bash
   cd /opt/timezone-api
   ./setup-podman.sh
   ```

2. **Install systemd service (for auto-start):**

   ```bash
   sudo cp timezone-api-podman.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable timezone-api-podman
   sudo systemctl start timezone-api-podman
   ```

3. **Configure CloudPanel reverse proxy:**

   * Create new site: `time.voidguardsecurity.com`
   * Add to Vhost configuration (inside `server` block):

     ```nginx
     location / {
         proxy_pass http://127.0.0.1:8000;
         proxy_set_header Host $host;
         proxy_set_header X-Real-IP $remote_addr;
         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
         proxy_set_header X-Forwarded-Proto $scheme;
     }
     ```
   * Enable SSL certificate

4. **Check status:**

   ```bash
   podman ps
   sudo systemctl status timezone-api-podman
   ```

### Using systemd (Native Python)

1. **Copy files to production directory:**

   ```bash
   sudo mkdir -p /opt/timezone-api
   sudo cp -r * /opt/timezone-api/
   ```

2. **Create virtual environment:**

   ```bash
   cd /opt/timezone-api
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Install systemd service:**

   ```bash
   sudo cp timezone-api.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable timezone-api
   sudo systemctl start timezone-api
   ```

4. **Check status:**

   ```bash
   sudo systemctl status timezone-api
   ```

### Using Nginx Reverse Proxy

Add this to your Nginx configuration:

```nginx
server {
    listen 80;
    server_name timezone-api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Client Examples

### JavaScript/Fetch

```javascript
// Auto-detect client timezone
fetch('http://localhost:8000/timezone/auto')
  .then(response => response.json())
  .then(data => {
    console.log(`Timezone: ${data.timezone}`);
    console.log(`Current Time: ${data.current_time}`);
    console.log(`UTC Offset: ${data.utc_offset}`);
  });

// Get timezone for specific IP
fetch('http://localhost:8000/timezone/8.8.8.8')
  .then(response => response.json())
  .then(data => console.log(data));
```

### Python

```python
import requests

# Auto-detect
response = requests.get('http://localhost:8000/timezone/auto')
data = response.json()
print(f"Timezone: {data['timezone']}")
print(f"Current Time: {data['current_time']}")

# Specific IP
response = requests.get('http://localhost:8000/timezone/8.8.8.8')
data = response.json()
print(data)
```

### cURL

```bash
# Auto-detect
curl http://localhost:8000/timezone/auto

# Specific IP
curl http://localhost:8000/timezone/8.8.8.8

# Pretty print
curl http://localhost:8000/timezone/8.8.8.8 | jq
```

## Configuration

### Change Port

Edit `main.py` or run with:

```bash
uvicorn main:app --host 0.0.0.0 --port 9000
```

### CORS Settings

Modify CORS settings in `main.py` to restrict origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)
```

## Troubleshooting

### Database Not Found

```text
⚠️  GeoIP2 database not found. Please download it first.
```

**Solution:** Run `python3 download_geodb.py` or manually download the database.

### Port Already in Use

**Solution:** Change the port in `main.py` or kill the process using port 8000:

```bash
sudo lsof -i :8000
sudo kill -9 <PID>
```

### Permission Denied

**Solution:** Make sure the user running the service has read access to the database file:

```bash
chmod 644 geodb/GeoLite2-City.mmdb
```

## Updating GeoIP Database

MaxMind updates the GeoLite2 database regularly. To update:

```bash
python3 download_geodb.py
sudo systemctl restart timezone-api
```

Or set up automatic updates with cron:

```bash
# Update database monthly
0 0 1 * * cd /opt/timezone-api && python3 download_geodb.py && systemctl restart timezone-api
```

## License

This service uses the free GeoLite2 database from MaxMind. Make sure to comply with their license terms:
[https://www.maxmind.com/en/geolite2/eula](https://www.maxmind.com/en/geolite2/eula)

## Support

For issues or questions, check the logs:

```bash
# Development
# (if running via uvicorn directly)
# Check console output

# Production (systemd)
sudo journalctl -u timezone-api -f
```
```