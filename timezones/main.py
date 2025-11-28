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


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🌍 Timezone API Server starting...")
    print("📊 Loaded geolocation database (if available)")


@app.get("/", response_model=dict)
async def root():
    """API root endpoint"""
    return {
        "service": "Timezone API",
        "version": "1.1.0",
        "endpoints": {
            "/timezone/{ip}": "Get timezone + location for specific IP address",
            "/timezone/auto": "Get timezone + location for client's IP (auto-detect)",
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
        port=8000,
        reload=True,
        log_level="info"
    )
