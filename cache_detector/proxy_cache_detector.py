#!/usr/bin/env python3
"""
Proxy Cache Detection and Purge Tool
Detects various proxy/cache servers and provides cache purge capabilities.

Supports:
- Varnish Cache
- Nginx (proxy_cache, fastcgi_cache)
- Squid
- Apache Traffic Server (ATS)
- Apache mod_cache
- HAProxy (detection only - no native cache)
- Cloudflare
- Generic HTTP caches

Author: Jason LaTorre
"""

import requests
import argparse
import sys
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from dataclasses import dataclass, field


@dataclass
class CacheHeaders:
    """Store cache-related headers from HTTP responses"""
    url: str
    status_code: int
    cache_control: Optional[str] = None
    surrogate_control: Optional[str] = None
    age: Optional[str] = None
    x_cache: Optional[str] = None
    x_cache_hits: Optional[str] = None
    x_cache_lookup: Optional[str] = None
    via: Optional[str] = None
    x_varnish: Optional[str] = None
    x_served_by: Optional[str] = None
    cf_cache_status: Optional[str] = None
    x_proxy_cache: Optional[str] = None
    x_nginx_cache: Optional[str] = None
    server: Optional[str] = None
    date: Optional[str] = None
    etag: Optional[str] = None
    detected_proxies: List[str] = field(default_factory=list)
    
    def __repr__(self):
        return f"CacheHeaders(url={self.url}, status={self.status_code}, proxies={self.detected_proxies})"


class ProxyCacheDetector:
    """Detects and manages various proxy cache servers"""

    def __init__(self, timeout: int = 10, proxy: Optional[str] = None):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ProxyCacheDetector/1.0'
        })

        # Configure proxy if provided
        if proxy:
            self.session.proxies = {
                'http': proxy,
                'https': proxy
            }
    
    def get_headers(self, url: str) -> CacheHeaders:
        """Fetch headers from a URL and extract cache information"""
        try:
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            headers = response.headers
            
            cache_headers = CacheHeaders(
                url=url,
                status_code=response.status_code,
                cache_control=headers.get('Cache-Control'),
                surrogate_control=headers.get('Surrogate-Control'),
                age=headers.get('Age'),
                x_cache=headers.get('X-Cache'),
                x_cache_hits=headers.get('X-Cache-Hits'),
                x_cache_lookup=headers.get('X-Cache-Lookup'),
                via=headers.get('Via'),
                x_varnish=headers.get('X-Varnish'),
                x_served_by=headers.get('X-Served-By'),
                cf_cache_status=headers.get('CF-Cache-Status'),
                x_proxy_cache=headers.get('X-Proxy-Cache'),
                x_nginx_cache=headers.get('X-Nginx-Cache'),
                server=headers.get('Server'),
                date=headers.get('Date'),
                etag=headers.get('ETag')
            )
            
            # Detect proxy types
            cache_headers.detected_proxies = self._detect_proxy_types(cache_headers)
            
            return cache_headers
            
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return CacheHeaders(url=url, status_code=0)
    
    def _detect_proxy_types(self, headers: CacheHeaders) -> List[str]:
        """Detect which proxy/cache servers are in use"""
        proxies = []
        
        # Varnish detection
        if headers.x_varnish or (headers.via and 'varnish' in headers.via.lower()):
            proxies.append('Varnish')
        
        # Nginx detection
        if headers.x_nginx_cache or (headers.server and 'nginx' in headers.server.lower()):
            if headers.x_cache or headers.age:
                proxies.append('Nginx (with caching)')
            else:
                proxies.append('Nginx')
        
        # Squid detection
        if headers.via and 'squid' in headers.via.lower():
            proxies.append('Squid')
        if headers.x_cache and 'squid' in headers.x_cache.lower():
            proxies.append('Squid')
        
        # Apache Traffic Server detection
        if headers.via and 'ATS' in headers.via:
            proxies.append('Apache Traffic Server')
        if headers.server and 'ATS' in headers.server:
            proxies.append('Apache Traffic Server')
        
        # Cloudflare detection
        if headers.cf_cache_status or (headers.server and 'cloudflare' in headers.server.lower()):
            proxies.append('Cloudflare')
        
        # Apache mod_cache detection
        if headers.x_cache and 'apache' in headers.x_cache.lower():
            proxies.append('Apache mod_cache')
        
        # HAProxy detection (doesn't cache but can be in the chain)
        if headers.via and 'haproxy' in headers.via.lower():
            proxies.append('HAProxy')
        
        # Generic cache detection
        if not proxies and (headers.x_cache or headers.age):
            proxies.append('Unknown Cache')
        
        return proxies
    
    def test_caching(self, url: str, delay_seconds: int = 3) -> Dict:
        """Test if content is being cached by making two requests"""
        print(f"\n>>> Testing {url}")
        
        # First request
        headers1 = self.get_headers(url)
        time.sleep(delay_seconds)
        
        # Second request
        headers2 = self.get_headers(url)
        
        # Calculate date delta if possible
        date_delta = None
        if headers1.date and headers2.date:
            try:
                from email.utils import parsedate_to_datetime
                d1 = parsedate_to_datetime(headers1.date)
                d2 = parsedate_to_datetime(headers2.date)
                date_delta = (d2 - d1).total_seconds()
            except:
                pass
        
        # Check if content is cached
        is_cached = False
        cache_evidence = []
        
        if headers1.age and headers2.age:
            try:
                age1 = int(headers1.age)
                age2 = int(headers2.age)
                if age2 > age1:
                    is_cached = True
                    cache_evidence.append(f"Age increased from {age1}s to {age2}s")
            except ValueError:
                pass
        
        if headers1.x_cache and 'HIT' in headers1.x_cache.upper():
            is_cached = True
            cache_evidence.append("X-Cache indicates HIT")
        
        if headers1.cf_cache_status and headers1.cf_cache_status.upper() == 'HIT':
            is_cached = True
            cache_evidence.append("Cloudflare cache HIT")
        
        if headers1.etag and headers2.etag and headers1.etag == headers2.etag:
            if date_delta and date_delta < 1:
                is_cached = True
                cache_evidence.append("Same ETag with minimal date change")
        
        return {
            'url': url,
            'status1': headers1.status_code,
            'status2': headers2.status_code,
            'cache_control': headers1.cache_control,
            'surrogate_control': headers1.surrogate_control,
            'age1': headers1.age,
            'age2': headers2.age,
            'x_cache1': headers1.x_cache,
            'x_cache2': headers2.x_cache,
            'via1': headers1.via,
            'via2': headers2.via,
            'date_delta_seconds': date_delta,
            'detected_proxies': headers1.detected_proxies,
            'is_cached': is_cached,
            'cache_evidence': cache_evidence
        }


class ProxyCachePurger:
    """Purge cache from various proxy servers"""

    def __init__(self, timeout: int = 10, proxy: Optional[str] = None):
        self.timeout = timeout
        self.proxies = None

        # Configure proxy if provided
        if proxy:
            self.proxies = {
                'http': proxy,
                'https': proxy
            }
    
    def purge_varnish(self, url: str, host: str = '127.0.0.1', 
                      port: int = 6081, cache_tags: Optional[str] = None) -> Dict:
        """
        Purge Varnish cache
        
        Args:
            url: URL to purge
            host: Varnish host
            port: Varnish port (default 6081)
            cache_tags: Optional cache tags (comma-separated)
        """
        parsed = urlparse(url)
        purge_url = f"http://{host}:{port}{parsed.path}"
        if parsed.query:
            purge_url += f"?{parsed.query}"
        
        headers = {
            'Host': parsed.netloc
        }
        
        if cache_tags:
            headers['X-Cache-Tags'] = cache_tags
        
        try:
            response = requests.request('PURGE', purge_url, headers=headers,
                                       timeout=self.timeout, proxies=self.proxies)
            return {
                'success': response.status_code in [200, 204],
                'status_code': response.status_code,
                'method': 'Varnish PURGE',
                'message': response.text if response.text else 'Purged successfully'
            }
        except requests.RequestException as e:
            return {
                'success': False,
                'method': 'Varnish PURGE',
                'message': f"Error: {e}"
            }
    
    def purge_nginx(self, url: str, purge_path: str = '/purge') -> Dict:
        """
        Purge Nginx cache (requires ngx_cache_purge module)
        
        Args:
            url: Base URL of the site
            purge_path: Purge endpoint path (default /purge)
        """
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        purge_url = f"{base_url}{purge_path}{parsed.path}"
        if parsed.query:
            purge_url += f"?{parsed.query}"
        
        try:
            response = requests.get(purge_url, timeout=self.timeout, proxies=self.proxies)
            return {
                'success': response.status_code in [200, 204],
                'status_code': response.status_code,
                'method': 'Nginx cache_purge',
                'message': response.text if response.text else 'Purged successfully'
            }
        except requests.RequestException as e:
            return {
                'success': False,
                'method': 'Nginx cache_purge',
                'message': f"Error: {e}"
            }
    
    def purge_squid(self, url: str, host: str = '127.0.0.1', port: int = 3128) -> Dict:
        """
        Purge Squid cache
        
        Args:
            url: URL to purge
            host: Squid host
            port: Squid port (default 3128)
        """
        parsed = urlparse(url)
        
        # Squid PURGE method
        headers = {
            'Host': parsed.netloc
        }
        
        try:
            response = requests.request('PURGE', url, headers=headers, 
                                       proxies={'http': f'http://{host}:{port}'},
                                       timeout=self.timeout)
            return {
                'success': response.status_code in [200, 204],
                'status_code': response.status_code,
                'method': 'Squid PURGE',
                'message': response.text if response.text else 'Purged successfully'
            }
        except requests.RequestException as e:
            return {
                'success': False,
                'method': 'Squid PURGE',
                'message': f"Error: {e}"
            }
    
    def purge_traffic_server(self, url: str, host: str = '127.0.0.1', 
                            port: int = 8080) -> Dict:
        """
        Purge Apache Traffic Server cache
        
        Args:
            url: URL to purge
            host: ATS host
            port: ATS port (default 8080)
        """
        parsed = urlparse(url)
        purge_url = f"http://{host}:{port}{parsed.path}"
        if parsed.query:
            purge_url += f"?{parsed.query}"
        
        headers = {
            'Host': parsed.netloc
        }
        
        try:
            response = requests.request('PURGE', purge_url, headers=headers,
                                       timeout=self.timeout, proxies=self.proxies)
            return {
                'success': response.status_code in [200, 204],
                'status_code': response.status_code,
                'method': 'Apache Traffic Server PURGE',
                'message': response.text if response.text else 'Purged successfully'
            }
        except requests.RequestException as e:
            return {
                'success': False,
                'method': 'Apache Traffic Server PURGE',
                'message': f"Error: {e}"
            }
    
    def purge_cloudflare(self, zone_id: str, api_token: str, 
                        urls: Optional[List[str]] = None,
                        purge_everything: bool = False) -> Dict:
        """
        Purge Cloudflare cache via API
        
        Args:
            zone_id: Cloudflare Zone ID
            api_token: Cloudflare API token
            urls: List of URLs to purge (max 30)
            purge_everything: Purge entire cache (use with caution)
        """
        api_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache"
        
        headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
        
        if purge_everything:
            data = {'purge_everything': True}
        elif urls:
            data = {'files': urls[:30]}  # Max 30 URLs per request
        else:
            return {
                'success': False,
                'method': 'Cloudflare API',
                'message': 'Must provide URLs or set purge_everything=True'
            }
        
        try:
            response = requests.post(api_url, headers=headers, json=data,
                                    timeout=self.timeout, proxies=self.proxies)
            result = response.json()
            return {
                'success': result.get('success', False),
                'method': 'Cloudflare API',
                'message': json.dumps(result, indent=2)
            }
        except requests.RequestException as e:
            return {
                'success': False,
                'method': 'Cloudflare API',
                'message': f"Error: {e}"
            }
    
    def purge_generic_http(self, url: str) -> Dict:
        """
        Try generic HTTP PURGE method
        Works with many cache servers that support the PURGE method
        """
        try:
            response = requests.request('PURGE', url, timeout=self.timeout,
                                       proxies=self.proxies)
            return {
                'success': response.status_code in [200, 204, 405],
                'status_code': response.status_code,
                'method': 'Generic HTTP PURGE',
                'message': response.text if response.text else
                          ('Purged successfully' if response.status_code in [200, 204]
                           else 'PURGE method not supported')
            }
        except requests.RequestException as e:
            return {
                'success': False,
                'method': 'Generic HTTP PURGE',
                'message': f"Error: {e}"
            }


def print_test_results(results: List[Dict]):
    """Pretty print cache test results"""
    print("\n" + "="*80)
    print("CACHE DETECTION RESULTS")
    print("="*80)
    
    for result in results:
        print(f"\nURL: {result['url']}")
        print(f"Status: {result['status1']} → {result['status2']}")
        
        if result['detected_proxies']:
            print(f"Detected Proxies: {', '.join(result['detected_proxies'])}")
        
        print(f"Is Cached: {'YES' if result['is_cached'] else 'MAYBE/NO'}")
        
        if result['cache_evidence']:
            print("Evidence:")
            for evidence in result['cache_evidence']:
                print(f"  - {evidence}")
        
        if result['cache_control']:
            print(f"Cache-Control: {result['cache_control']}")
        
        if result['age1'] or result['age2']:
            print(f"Age: {result['age1']} → {result['age2']}")
        
        if result['x_cache1'] or result['x_cache2']:
            print(f"X-Cache: {result['x_cache1']} → {result['x_cache2']}")
        
        if result['via1']:
            print(f"Via: {result['via1']}")
        
        if result['date_delta_seconds'] is not None:
            print(f"Date Delta: {result['date_delta_seconds']:.1f} seconds")
        
        print("-" * 80)


def main():
    parser = argparse.ArgumentParser(
        description='Detect and purge cache from various proxy servers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Detect cache
  %(prog)s detect https://example.com
  %(prog)s detect https://example.com https://example.com/api/data
  
  # Purge Varnish cache
  %(prog)s purge-varnish https://example.com
  %(prog)s purge-varnish https://example.com --port 6081 --cache-tags "tag1,tag2"
  
  # Purge Nginx cache
  %(prog)s purge-nginx https://example.com
  
  # Purge Squid cache
  %(prog)s purge-squid https://example.com --host 127.0.0.1 --port 3128
  
  # Purge Apache Traffic Server
  %(prog)s purge-ats https://example.com
  
  # Purge Cloudflare
  %(prog)s purge-cloudflare --zone-id ZONEID --token TOKEN --urls https://example.com/page1
  
  # Try generic PURGE
  %(prog)s purge-generic https://example.com
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Detect command
    detect_parser = subparsers.add_parser('detect', help='Detect cache configuration')
    detect_parser.add_argument('urls', nargs='+', help='URLs to test')
    detect_parser.add_argument('--delay', type=int, default=3,
                              help='Delay between requests (default: 3 seconds)')
    detect_parser.add_argument('--timeout', type=int, default=10,
                              help='Request timeout (default: 10 seconds)')
    detect_parser.add_argument('--proxy', type=str, default=None,
                              help='Proxy server URL (e.g., http://proxy.example.com:8080)')
    
    # Purge Varnish
    varnish_parser = subparsers.add_parser('purge-varnish',
                                           help='Purge Varnish cache')
    varnish_parser.add_argument('url', help='URL to purge')
    varnish_parser.add_argument('--host', default='127.0.0.1',
                               help='Varnish host (default: 127.0.0.1)')
    varnish_parser.add_argument('--port', type=int, default=6081,
                               help='Varnish port (default: 6081)')
    varnish_parser.add_argument('--cache-tags', help='Cache tags to purge')
    varnish_parser.add_argument('--proxy', type=str, default=None,
                               help='Proxy server URL (e.g., http://proxy.example.com:8080)')
    
    # Purge Nginx
    nginx_parser = subparsers.add_parser('purge-nginx',
                                        help='Purge Nginx cache')
    nginx_parser.add_argument('url', help='URL to purge')
    nginx_parser.add_argument('--purge-path', default='/purge',
                             help='Purge endpoint path (default: /purge)')
    nginx_parser.add_argument('--proxy', type=str, default=None,
                             help='Proxy server URL (e.g., http://proxy.example.com:8080)')

    # Purge Squid
    squid_parser = subparsers.add_parser('purge-squid',
                                        help='Purge Squid cache')
    squid_parser.add_argument('url', help='URL to purge')
    squid_parser.add_argument('--host', default='127.0.0.1',
                             help='Squid host (default: 127.0.0.1)')
    squid_parser.add_argument('--port', type=int, default=3128,
                             help='Squid port (default: 3128)')
    squid_parser.add_argument('--proxy', type=str, default=None,
                             help='Proxy server URL (e.g., http://proxy.example.com:8080)')

    # Purge Apache Traffic Server
    ats_parser = subparsers.add_parser('purge-ats',
                                      help='Purge Apache Traffic Server cache')
    ats_parser.add_argument('url', help='URL to purge')
    ats_parser.add_argument('--host', default='127.0.0.1',
                           help='ATS host (default: 127.0.0.1)')
    ats_parser.add_argument('--port', type=int, default=8080,
                           help='ATS port (default: 8080)')
    ats_parser.add_argument('--proxy', type=str, default=None,
                           help='Proxy server URL (e.g., http://proxy.example.com:8080)')

    # Purge Cloudflare
    cf_parser = subparsers.add_parser('purge-cloudflare',
                                     help='Purge Cloudflare cache via API')
    cf_parser.add_argument('--zone-id', required=True, help='Cloudflare Zone ID')
    cf_parser.add_argument('--token', required=True, help='Cloudflare API token')
    cf_parser.add_argument('--urls', nargs='+', help='URLs to purge (max 30)')
    cf_parser.add_argument('--purge-everything', action='store_true',
                          help='Purge entire cache (use with caution)')
    cf_parser.add_argument('--proxy', type=str, default=None,
                          help='Proxy server URL (e.g., http://proxy.example.com:8080)')

    # Generic purge
    generic_parser = subparsers.add_parser('purge-generic',
                                          help='Try generic HTTP PURGE method')
    generic_parser.add_argument('url', help='URL to purge')
    generic_parser.add_argument('--proxy', type=str, default=None,
                               help='Proxy server URL (e.g., http://proxy.example.com:8080)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    if args.command == 'detect':
        detector = ProxyCacheDetector(timeout=args.timeout, proxy=args.proxy)
        results = []
        for url in args.urls:
            result = detector.test_caching(url, args.delay)
            results.append(result)
        print_test_results(results)

    elif args.command == 'purge-varnish':
        purger = ProxyCachePurger(proxy=args.proxy)
        result = purger.purge_varnish(args.url, args.host, args.port,
                                     args.cache_tags)
        print(f"\n{result['method']}: {'SUCCESS' if result['success'] else 'FAILED'}")
        print(f"Message: {result['message']}")

    elif args.command == 'purge-nginx':
        purger = ProxyCachePurger(proxy=args.proxy)
        result = purger.purge_nginx(args.url, args.purge_path)
        print(f"\n{result['method']}: {'SUCCESS' if result['success'] else 'FAILED'}")
        print(f"Message: {result['message']}")

    elif args.command == 'purge-squid':
        purger = ProxyCachePurger(proxy=args.proxy)
        result = purger.purge_squid(args.url, args.host, args.port)
        print(f"\n{result['method']}: {'SUCCESS' if result['success'] else 'FAILED'}")
        print(f"Message: {result['message']}")

    elif args.command == 'purge-ats':
        purger = ProxyCachePurger(proxy=args.proxy)
        result = purger.purge_traffic_server(args.url, args.host, args.port)
        print(f"\n{result['method']}: {'SUCCESS' if result['success'] else 'FAILED'}")
        print(f"Message: {result['message']}")

    elif args.command == 'purge-cloudflare':
        purger = ProxyCachePurger(proxy=args.proxy)
        result = purger.purge_cloudflare(args.zone_id, args.token, args.urls,
                                        args.purge_everything)
        print(f"\n{result['method']}: {'SUCCESS' if result['success'] else 'FAILED'}")
        print(f"Message: {result['message']}")

    elif args.command == 'purge-generic':
        purger = ProxyCachePurger(proxy=args.proxy)
        result = purger.purge_generic_http(args.url)
        print(f"\n{result['method']}: {'SUCCESS' if result['success'] else 'FAILED'}")
        print(f"Status Code: {result.get('status_code', 'N/A')}")
        print(f"Message: {result['message']}")


if __name__ == '__main__':
    main()