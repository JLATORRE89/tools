#!/usr/bin/env python3
"""
Timezone API Server
FastAPI service that returns timezone and location information based on IP address
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
from datetime import datetime
import pytz
from ip_timezone_lookup import IPTimezoneLookup
from reverse_geocode import ReverseGeocoder
from reverse_geocode_cache import ReverseGeocodeCache
from forward_geocode import ForwardGeocoder

# New imports for rate limiting
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

app = FastAPI(
    title="Timezone API",
    description="Get timezone and location information based on IP address",
    version="1.1.0"
)

# Enable CORS for all origins (customize as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Simple in-memory rate limiter
# -----------------------------


class SimpleRateLimiter:
    """
    Very simple in-memory rate limiter: N requests per window per key.
    Not distributed and resets when the process restarts.
    """

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # key -> (reset_timestamp, count)
        self._buckets: Dict[str, tuple[float, int]] = {}

    def is_allowed(self, key: str) -> tuple[bool, float]:
        """
        Returns (allowed, retry_after_seconds).
        """
        now = time.time()
        reset_ts, count = self._buckets.get(key, (now + self.window_seconds, 0))

        # Window expired -> reset counter
        if now > reset_ts:
            reset_ts = now + self.window_seconds
            count = 0

        if count >= self.max_requests:
            # Not allowed, tell client how long to wait
            retry_after = max(0.0, reset_ts - now)
            self._buckets[key] = (reset_ts, count)
            return False, retry_after

        # Allowed, increment count
        count += 1
        self._buckets[key] = (reset_ts, count)
        retry_after = max(0.0, reset_ts - now)
        return True, retry_after


def get_client_ip(request: Request) -> str:
    """
    Extract client IP, preferring X-Forwarded-For when behind Nginx.
    """
    xff = request.headers.get("x-forwarded-for")
    if xff:
        # First IP in the list is the original client
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


# Configure limits here (e.g. 120 requests/min per IP)
RATE_LIMITER = SimpleRateLimiter(max_requests=120, window_seconds=60)


class TimezoneRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Apply basic per-IP rate limiting to /timezone/* endpoints.
    Excludes /timezone/health and /timezone/about.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Only protect /timezone/* endpoints
        if path.startswith("/timezone"):
            # Exempt health + about so monitoring and attribution are always available
            if path not in ("/timezone/health", "/timezone/about") and request.method in ("GET", "HEAD"):
                client_ip = get_client_ip(request)
                allowed, retry_after = RATE_LIMITER.is_allowed(client_ip)

                if not allowed:
                    return JSONResponse(
                        status_code=HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "detail": "Too Many Requests",
                            "message": "Rate limit exceeded. Please slow down.",
                            "retry_after_seconds": int(retry_after),
                            "ip": client_ip,
                        },
                    )

        # Otherwise continue as normal
        response = await call_next(request)
        return response


# Attach rate limiting middleware
app.add_middleware(TimezoneRateLimitMiddleware)

# Initialize the IP timezone lookup service
tz_lookup = IPTimezoneLookup()

# Initialize reverse geocoding service and cache
reverse_geocoder = ReverseGeocoder(geoip_db_path=tz_lookup.db_path, user_agent="VoidGuard-TimezoneAPI/1.1")
geocode_cache = ReverseGeocodeCache(db_path="./geocode_cache.db", cache_days=90)

# Initialize forward geocoding service (postal code -> location)
forward_geocoder = ForwardGeocoder(user_agent="VoidGuard-TimezoneAPI/1.1")


class TimezoneResponse(BaseModel):
    # Core time/timezone fields
    ip: str
    timezone: str
    utc_offset: str
    current_time: str
    abbreviation: str
    is_dst: bool

    # Extended location fields (all optional)
    country: Optional[str] = None
    country_code: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
    county: Optional[str] = None
    state_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    continent: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


class ReverseGeocodeResponse(BaseModel):
    """Response model for reverse geocoding (lat/long -> location)"""
    latitude: float
    longitude: float
    zip_code: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    state: Optional[str] = None
    state_code: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    timezone: Optional[str] = None
    display_name: Optional[str] = None
    source: str  # 'cache', 'nominatim', 'geoip', or 'none'
    from_cache: bool = False


class ForwardGeocodeResponse(BaseModel):
    """Response model for forward geocoding (postal code -> location)"""
    postal_code: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    city: Optional[str] = None
    county: Optional[str] = None
    state: Optional[str] = None
    state_code: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    timezone: Optional[str] = None
    display_name: Optional[str] = None
    source: str  # 'nominatim' or 'none'
    bbox: Optional[list] = None  # Bounding box coordinates


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("Timezone API Server starting...")
    print("Loaded geolocation database (if available)")
    print("Reverse geocoding cache initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Shutting down...")
    reverse_geocoder.close()
    tz_lookup.close()


@app.get("/", response_model=dict)
async def root():
    """API root endpoint"""
    return {
        "service": "Timezone API",
        "version": "1.1.0",
        "endpoints": {
            "/timezone/{ip}": "Get timezone + location for specific IP address",
            "/timezone/auto": "Get timezone + location for client's IP (auto-detect)",
            "/reverse-geocode?lat={lat}&lon={lon}": "Get location (including zip code) from coordinates",
            "/forward-geocode?postal_code={code}&country={country}": "Get location and coordinates from postal/zip code",
            "/health": "Health check endpoint",
            "/timezone/health": "Timezone API healthcheck",
            "/timezone/about": "Service metadata and MaxMind attribution",
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "timezone-api"
    }


def get_timezone_info(ip: str, timezone_name: str, location_info: Optional[Dict[str, Any]] = None) -> TimezoneResponse:
    """
    Get detailed timezone information

    Args:
        ip: IP address
        timezone_name: Timezone name (e.g., 'America/New_York')
        location_info: Optional dict returned from IPTimezoneLookup.get_location_info()

    Returns:
        TimezoneResponse with detailed timezone + location information
    """
    try:
        tz = pytz.timezone(timezone_name)
        now = datetime.now(tz)

        # Get UTC offset
        utc_offset = now.strftime("%z")  # e.g. "-0500"
        utc_offset_formatted = f"{utc_offset[:3]}:{utc_offset[3:]}"  # e.g. "-05:00"

        # Get timezone abbreviation (e.g., EST, PST)
        abbreviation = now.strftime("%Z")

        # Check if DST is active
        is_dst = bool(now.dst())

        location_info = location_info or {}

        return TimezoneResponse(
            ip=ip,
            timezone=timezone_name,
            utc_offset=utc_offset_formatted,
            current_time=now.isoformat(),
            abbreviation=abbreviation,
            is_dst=is_dst,
            country=location_info.get("country"),
            country_code=location_info.get("country_code"),
            city=location_info.get("city"),
            zip_code=location_info.get("zip_code"),
            county=location_info.get("county"),
            state_code=location_info.get("state_code"),
            latitude=location_info.get("latitude"),
            longitude=location_info.get("longitude"),
            continent=location_info.get("continent"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting timezone info: {str(e)}"
        )


@app.get("/timezone/auto", response_model=TimezoneResponse)
async def get_timezone_auto(request: Request):
    """
    Get timezone and location information for the client's IP address (auto-detected)
    """
    # Get client IP from request
    client_ip = request.client.host

    # Check for forwarded IP (if behind proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    # Handle localhost (no GeoIP data available)
    if client_ip in ["127.0.0.1", "::1", "localhost"]:
        timezone_name = "UTC"
        location_info: Dict[str, Any] = {
            "ip": client_ip,
            "timezone": timezone_name,
            "country": None,
            "country_code": None,
            "city": None,
            "zip_code": None,
            "county": None,
            "state_code": None,
            "latitude": None,
            "longitude": None,
            "continent": None,
        }
    else:
        # Get full location info from GeoIP
        location_info = tz_lookup.get_location_info(client_ip)
        if not location_info:
            raise HTTPException(
                status_code=404,
                detail=f"Could not determine location for IP: {client_ip}"
            )

        timezone_name = location_info.get("timezone") or tz_lookup.get_timezone(client_ip)

    if not timezone_name:
        raise HTTPException(
            status_code=404,
            detail=f"Could not determine timezone for IP: {client_ip}"
        )

    return get_timezone_info(client_ip, timezone_name, location_info)


@app.get("/timezone/about", response_model=dict)
async def timezone_about():
    """
    About / attribution endpoint for the Timezone API.
    Includes required MaxMind GeoLite2 attribution.
    """
    return {
        "service": "Timezone API",
        "version": "1.1.0",
        "description": "IP to timezone and location lookup using GeoLite2 data.",
        "attribution": "This product includes GeoLite2 data created by MaxMind, available from https://www.maxmind.com.",
        "license_url": "https://www.maxmind.com"
    }


@app.get("/timezone/health", response_model=dict)
async def timezone_health():
    """
    Healthcheck endpoint for the Timezone API.

    - Verifies that the GeoIP database is loaded (if available)
    - Returns current UTC time
    - Useful for monitoring and VoidGuard internal checks
    """
    from datetime import datetime as dt_datetime, timezone as dt_timezone

    # Check if GeoIP reader is initialized
    db_loaded = getattr(tz_lookup, "reader", None) is not None

    return {
        "service": "timezone-api",
        "version": "1.1.0",
        "status": "ok" if db_loaded else "degraded",
        "geodb_loaded": db_loaded,
        "current_time_utc": dt_datetime.now(dt_timezone.utc).isoformat(),
    }


@app.get("/reverse-geocode", response_model=ReverseGeocodeResponse)
async def reverse_geocode(lat: float, lon: float):
    """
    Reverse geocode: Get location information (including zip code) from coordinates

    Query Parameters:
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)

    Returns:
        Location information including zip code, city, state, country, etc.

    Data sources (in priority order):
        1. SQLite cache (previously looked up coordinates)
        2. Nominatim/OpenStreetMap API (live lookup with rate limiting)
        3. No fallback available for pure lat/long (GeoIP doesn't support reverse queries)
    """
    # Validate coordinates
    if not (-90 <= lat <= 90):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid latitude: {lat}. Must be between -90 and 90."
        )

    if not (-180 <= lon <= 180):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid longitude: {lon}. Must be between -180 and 180."
        )

    # Check cache first
    cached_result = geocode_cache.get(lat, lon, tolerance=0.01)
    if cached_result:
        return ReverseGeocodeResponse(**cached_result)

    # Perform reverse geocoding
    result = reverse_geocoder.reverse_geocode(lat, lon)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Could not reverse geocode coordinates: ({lat}, {lon})"
        )

    # Cache the result if we got data from Nominatim
    if result.get("source") == "nominatim":
        geocode_cache.set(lat, lon, result, source="nominatim")

    # Add timezone if not provided by Nominatim
    if not result.get("timezone") and result.get("country_code"):
        # Try to determine timezone from coordinates using timezonefinder (if available)
        try:
            from timezonefinder import TimezoneFinder
            tf = TimezoneFinder()
            tz_name = tf.timezone_at(lat=lat, lng=lon)
            if tz_name:
                result["timezone"] = tz_name
        except ImportError:
            # timezonefinder not installed, use basic country mapping
            country_code = result.get("country_code")
            if country_code:
                # Use the same country->timezone mapping from ip_timezone_lookup
                tz_name = tz_lookup._country_to_timezone(country_code)
                if tz_name and tz_name != "UTC":
                    result["timezone"] = tz_name
        except Exception as e:
            # Log but don't fail the request
            print(f"Error looking up timezone for coordinates: {e}")

    return ReverseGeocodeResponse(**result)


@app.get("/forward-geocode", response_model=ForwardGeocodeResponse)
async def forward_geocode(postal_code: str, country: Optional[str] = None):
    """
    Forward geocode: Get location details and coordinates from postal/zip code

    Query Parameters:
        postal_code (required): Postal code / zip code to look up
        country (optional): ISO 3166-1 alpha-2 country code (e.g., "US", "GB", "JP")
                           Highly recommended for accurate results

    Returns:
        Location information including coordinates, city, state, country, etc.

    Examples:
        - US zip code: /forward-geocode?postal_code=10007&country=US
        - UK postcode: /forward-geocode?postal_code=WC2N 5DX&country=GB
        - Japanese: /forward-geocode?postal_code=168-0063&country=JP
        - Without country (less accurate): /forward-geocode?postal_code=10007

    Data source: Nominatim/OpenStreetMap API (rate limited: 1 req/sec)
    """
    # Validate postal code
    if not postal_code or not postal_code.strip():
        raise HTTPException(
            status_code=400,
            detail="Postal code is required"
        )

    # Perform forward geocoding
    result = forward_geocoder.geocode_postal(postal_code, country)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Could not geocode postal code: {postal_code}"
        )

    # Add timezone if we have coordinates
    if result.get("latitude") and result.get("longitude") and result.get("country_code"):
        try:
            from timezonefinder import TimezoneFinder
            tf = TimezoneFinder()
            tz_name = tf.timezone_at(lat=result["latitude"], lng=result["longitude"])
            if tz_name:
                result["timezone"] = tz_name
        except ImportError:
            # timezonefinder not installed, use basic country mapping
            country_code = result.get("country_code")
            if country_code:
                tz_name = tz_lookup._country_to_timezone(country_code)
                if tz_name and tz_name != "UTC":
                    result["timezone"] = tz_name
        except Exception as e:
            # Log but don't fail the request
            print(f"Error looking up timezone for coordinates: {e}")

    return ForwardGeocodeResponse(**result)


@app.get("/timezone/{ip}", response_model=TimezoneResponse)
async def get_timezone(ip: str):
    """
    Get timezone and location information for a specific IP address

    Args:
        ip: IP address (IPv4 or IPv6)

    Returns:
        Timezone information including current time, UTC offset, and location details
    """
    # Basic validation
    if not ip:
        raise HTTPException(
            status_code=400,
            detail="IP address is required"
        )

    # Handle localhost (no GeoIP data available)
    if ip in ["127.0.0.1", "::1", "localhost"]:
        timezone_name = "UTC"
        location_info: Dict[str, Any] = {
            "ip": ip,
            "timezone": timezone_name,
            "country": None,
            "country_code": None,
            "city": None,
            "zip_code": None,
            "county": None,
            "state_code": None,
            "latitude": None,
            "longitude": None,
            "continent": None,
        }
    else:
        # Get full location info from GeoIP
        location_info = tz_lookup.get_location_info(ip)
        if not location_info:
            raise HTTPException(
                status_code=404,
                detail=f"Could not determine location for IP: {ip}"
            )

        timezone_name = location_info.get("timezone") or tz_lookup.get_timezone(ip)

    if not timezone_name:
        raise HTTPException(
            status_code=404,
            detail=f"Could not determine timezone for IP: {ip}"
        )

    return get_timezone_info(ip, timezone_name, location_info)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8100,
        reload=True,
        log_level="info"
    )
