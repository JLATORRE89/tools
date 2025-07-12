
import ssl, socket, datetime, json, csv, subprocess, os, requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import sys
from datetime import datetime, timezone

def get_ssl_info(domain):
    try:
        parsed = urlparse(domain)
        hostname = parsed.hostname or domain.replace("https://", "").replace("http://", "").strip("/")
        port = parsed.port or 443

        context = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                expires = datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y %Z")
                expires = expires.replace(tzinfo=timezone.utc)
                remaining = (expires - datetime.now(timezone.utc)).days
                status = "✅ Valid"
                if remaining <= 15:
                    status = "🔴 Expiring very soon"
                elif remaining <= 30:
                    status = "🟡 Renewal recommended"

                return {
                    "status": status,
                    "expires": expires.strftime("%Y-%m-%d %H:%M:%S"),
                    "remaining_days": remaining
                }
    except Exception as e:
        return {
            "status": "❌ error",
            "expires": "n/a",
            "remaining_days": None,
            "error": str(e)
        }
    
def check_safe_browsing(domain):
    return {
        "status": "⚠️ Potential issues found (manually review)",
        "url": f"https://transparencyreport.google.com/safe-browsing/search?url={domain.replace('https://', '').replace('http://', '')}&hl=en"
    }

def check_headers(domain):
    try:
        r = requests.get(domain, timeout=5)
        hsts = 'Strict-Transport-Security' in r.headers
        csp = 'Content-Security-Policy' in r.headers
        return {"HSTS": hsts, "CSP": csp}
    except:
        return {"HSTS": False, "CSP": False}

def check_mixed_content(domain):
    try:
        r = requests.get(domain, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        insecure = [tag.get('src') for tag in soup.find_all(['img', 'script', 'iframe', 'link'], src=True) if 'http://' in tag.get('src')]
        return {"count": len(insecure), "assets": insecure}
    except:
        return {"count": 0, "assets": []}

def check_forms(domain):
    try:
        r = requests.get(domain, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        forms = soup.find_all('form')
        insecure = [f.get('action') for f in forms if f.get('action') and f.get('action').startswith('http://')]
        return {"count": len(insecure), "forms": insecure}
    except:
        return {"count": 0, "forms": []}

def print_result(url, results):
    print(f"🔍 Summary for {url}")
    ssl = results['ssl']
    print(f"[SSL] {ssl['status']}, expires: {ssl['expires']}")
    print(f"[Safe Browsing] {results['safe']['status']}")
    print(f"[Headers] HSTS: {'✅' if results['headers']['HSTS'] else '❌'}, CSP: {'✅' if results['headers']['CSP'] else '❌'}")
    print(f"[Mixed Content] {results['mixed']['count']} insecure assets")
    print(f"[Insecure Forms] {results['forms']['count']} issues")

def main():
    if len(sys.argv) == 2:
        url = sys.argv[1]
        results = {
            "ssl": get_ssl_info(url),
            "safe": check_safe_browsing(url),
            "headers": check_headers(url),
            "mixed": check_mixed_content(url),
            "forms": check_forms(url)
        }
        print_result(url, results)
    elif len(sys.argv) == 4:
        input_file, json_out, csv_out = sys.argv[1], sys.argv[2], sys.argv[3]
        urls = open(input_file).read().splitlines()
        all_results = []
        for url in urls:
            result = {
                "url": url,
                "ssl": get_ssl_info(url),
                "safe": check_safe_browsing(url),
                "headers": check_headers(url),
                "mixed": check_mixed_content(url),
                "forms": check_forms(url)
            }
            all_results.append(result)
        with open(json_out, 'w') as f:
            json.dump(all_results, f, indent=2)
        with open(csv_out, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["URL", "SSL Status", "Expires", "Remaining Days", "Safe Browsing", "HSTS", "CSP", "Mixed Content", "Insecure Forms"])
            for r in all_results:
                writer.writerow([
                    r["url"], r["ssl"]["status"], r["ssl"]["expires"], r["ssl"]["remaining_days"],
                    r["safe"]["status"], r["headers"]["HSTS"], r["headers"]["CSP"],
                    r["mixed"]["count"], r["forms"]["count"]
                ])
        print("✅ Multi-site audit complete")
    else:
        print("Usage:")
        print("  python site_audit.py https://example.com")
        print("  python site_audit.py input.txt output.json output.csv")

if __name__ == "__main__":
    main()
