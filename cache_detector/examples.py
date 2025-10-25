#!/usr/bin/env python3
"""
Example usage of the Proxy Cache Detector tool
Demonstrates common scenarios and use cases
"""

from proxy_cache_detector import ProxyCacheDetector, ProxyCachePurger


def example_detect_cache():
    """Example: Detect if a URL is being cached"""
    print("="*80)
    print("EXAMPLE 1: Detect Cache Configuration")
    print("="*80)
    
    detector = ProxyCacheDetector(timeout=10)
    
    # Test a single URL
    url = 'https://www.cloudpanel.io'
    result = detector.test_caching(url, delay_seconds=3)
    
    print(f"\nURL: {result['url']}")
    print(f"Detected Proxies: {', '.join(result['detected_proxies']) if result['detected_proxies'] else 'None'}")
    print(f"Is Cached: {'YES' if result['is_cached'] else 'NO/MAYBE'}")
    
    if result['cache_evidence']:
        print("\nCache Evidence:")
        for evidence in result['cache_evidence']:
            print(f"  - {evidence}")
    
    print("\nCache Headers:")
    print(f"  Cache-Control: {result['cache_control']}")
    print(f"  Age: {result['age1']} → {result['age2']}")
    print(f"  X-Cache: {result['x_cache1']} → {result['x_cache2']}")
    print(f"  Via: {result['via1']}")


def example_purge_varnish():
    """Example: Purge Varnish cache"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Purge Varnish Cache")
    print("="*80)
    
    purger = ProxyCachePurger()
    
    # Purge a specific URL
    url = 'https://example.com/page'
    result = purger.purge_varnish(
        url=url,
        host='127.0.0.1',
        port=6081,
        cache_tags=None  # or 'tag1,tag2' for tagged purging
    )
    
    print(f"\nPurge Method: {result['method']}")
    print(f"Success: {result['success']}")
    print(f"Message: {result['message']}")
    
    # Example with cache tags (CloudPanel style)
    print("\n--- With Cache Tags ---")
    result = purger.purge_varnish(
        url='https://example.com',
        host='127.0.0.1',
        port=6081,
        cache_tags='homepage,main'
    )
    print(f"Success: {result['success']}")


def example_purge_nginx():
    """Example: Purge Nginx cache"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Purge Nginx Cache")
    print("="*80)
    
    purger = ProxyCachePurger()
    
    # Purge via the cache_purge endpoint
    url = 'https://example.com/api/data'
    result = purger.purge_nginx(
        url=url,
        purge_path='/purge'
    )
    
    print(f"\nPurge Method: {result['method']}")
    print(f"Success: {result['success']}")
    print(f"Status Code: {result.get('status_code', 'N/A')}")
    print(f"Message: {result['message']}")


def example_batch_purge():
    """Example: Purge multiple URLs"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Batch Purge Multiple URLs")
    print("="*80)
    
    purger = ProxyCachePurger()
    
    urls = [
        'https://example.com/page1',
        'https://example.com/page2',
        'https://example.com/api/data'
    ]
    
    results = []
    for url in urls:
        result = purger.purge_varnish(url, host='127.0.0.1', port=6081)
        results.append({
            'url': url,
            'success': result['success'],
            'method': result['method']
        })
    
    print("\nBatch Purge Results:")
    for r in results:
        status = "✓ SUCCESS" if r['success'] else "✗ FAILED"
        print(f"  {status}: {r['url']}")


def example_detect_multiple():
    """Example: Detect cache for multiple URLs"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Detect Cache for Multiple URLs")
    print("="*80)
    
    detector = ProxyCacheDetector()
    
    urls = [
        'https://www.cloudpanel.io',
        'https://www.cloudpanel.io/docs/'
    ]
    
    for url in urls:
        print(f"\n--- Testing {url} ---")
        result = detector.test_caching(url, delay_seconds=2)
        
        print(f"Proxies: {', '.join(result['detected_proxies']) if result['detected_proxies'] else 'None'}")
        print(f"Cached: {'YES' if result['is_cached'] else 'NO/MAYBE'}")
        if result['x_cache1']:
            print(f"X-Cache: {result['x_cache1']}")


def example_cloudflare_purge():
    """Example: Purge Cloudflare cache (requires API credentials)"""
    print("\n" + "="*80)
    print("EXAMPLE 6: Purge Cloudflare Cache")
    print("="*80)
    print("\nNote: This example requires valid Cloudflare credentials")
    
    # Uncomment and fill in your credentials to test
    """
    purger = ProxyCachePurger()
    
    # Purge specific URLs
    result = purger.purge_cloudflare(
        zone_id='YOUR_ZONE_ID',
        api_token='YOUR_API_TOKEN',
        urls=['https://example.com/page1', 'https://example.com/page2']
    )
    
    print(f"\nPurge Method: {result['method']}")
    print(f"Success: {result['success']}")
    print(f"Response: {result['message']}")
    
    # Purge everything (use with caution!)
    result = purger.purge_cloudflare(
        zone_id='YOUR_ZONE_ID',
        api_token='YOUR_API_TOKEN',
        purge_everything=True
    )
    """
    
    print("\nSkipped (requires credentials)")


def example_comprehensive_check():
    """Example: Comprehensive cache check and report"""
    print("\n" + "="*80)
    print("EXAMPLE 7: Comprehensive Cache Analysis")
    print("="*80)
    
    detector = ProxyCacheDetector()
    
    url = 'https://www.cloudpanel.io'
    
    print(f"\nAnalyzing: {url}")
    print("-" * 40)
    
    # Get headers
    headers = detector.get_headers(url)
    
    print(f"\nServer: {headers.server or 'Unknown'}")
    print(f"Status: {headers.status_code}")
    
    if headers.detected_proxies:
        print(f"\nDetected Proxies:")
        for proxy in headers.detected_proxies:
            print(f"  ✓ {proxy}")
    else:
        print("\nNo proxies detected")
    
    print(f"\nCache Configuration:")
    print(f"  Cache-Control: {headers.cache_control or 'Not set'}")
    print(f"  Surrogate-Control: {headers.surrogate_control or 'Not set'}")
    print(f"  Age: {headers.age or 'Not set'}")
    
    print(f"\nProxy Chain:")
    print(f"  Via: {headers.via or 'Direct'}")
    
    if headers.x_cache:
        print(f"\nCache Status:")
        print(f"  X-Cache: {headers.x_cache}")
        if headers.x_cache_hits:
            print(f"  Cache Hits: {headers.x_cache_hits}")
    
    # Test caching behavior
    print("\n--- Testing Cache Behavior ---")
    result = detector.test_caching(url, delay_seconds=3)
    
    if result['is_cached']:
        print("✓ Content IS being cached")
        if result['cache_evidence']:
            print("\nEvidence:")
            for evidence in result['cache_evidence']:
                print(f"  - {evidence}")
    else:
        print("✗ Content does NOT appear to be cached")


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "Proxy Cache Detector Examples" + " "*29 + "║")
    print("╚" + "="*78 + "╝")
    
    try:
        # Run detection example
        example_detect_cache()
        
        # Note: The following purge examples will fail without proper
        # proxy server configuration. They're included for demonstration.
        
        print("\n\n" + "="*80)
        print("NOTE: Purge examples require proxy servers to be configured")
        print("="*80)
        
        # Uncomment to test purge operations
        # example_purge_varnish()
        # example_purge_nginx()
        # example_batch_purge()
        
        # Run additional detection examples
        example_detect_multiple()
        example_cloudflare_purge()
        example_comprehensive_check()
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n\n" + "="*80)
    print("Examples completed!")
    print("="*80)


if __name__ == '__main__':
    main()