"""Fetch one owned MCP asset for Telegram delivery; never print the credential."""
import argparse
import json
import os
from pathlib import Path
import re
import ssl
import urllib.request
from urllib.parse import urlsplit, urljoin


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('asset_url')
    args=parser.parse_args()
    home=Path.home()
    config=json.loads((home/'.openclaw/openclaw.json').read_text())
    provider=config.get('models',{}).get('providers',{}).get('localnet',{})
    base=os.getenv('LOCAL_AI_STACK_BASE_URL') or provider.get('baseUrl','')
    origin=urlsplit(base)
    if origin.scheme!='https' or not origin.hostname or origin.username or origin.password:
        raise SystemExit('Configure a trusted HTTPS account provider first')
    url=urlsplit(urljoin(base,args.asset_url))
    if (url.scheme,url.netloc)!=(origin.scheme,origin.netloc) or url.query or url.fragment:
        raise SystemExit('Asset URL must use the configured account origin')
    match=re.fullmatch(r'/api/v1/gpu-openclaw/assets/([0-9a-f-]{36})/content',url.path)
    if not match:raise SystemExit('Expected an owned account asset download URL')
    import uuid
    asset_id=str(uuid.UUID(match[1]))
    key=os.getenv('LOCAL_AI_STACK_ACCOUNT_KEY') or os.getenv('LOCAL_AI_STACK_API_KEY')
    if not key:raise SystemExit('Account credential is unavailable in the gateway environment')
    context=ssl.create_default_context()
    ca=os.getenv('NODE_EXTRA_CA_CERTS')
    if ca:context.load_verify_locations(cafile=ca)
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):return None
    opener=urllib.request.build_opener(NoRedirect(),urllib.request.HTTPSHandler(context=context))
    request=urllib.request.Request(url.geturl(),headers={'Authorization':'Bearer '+key})
    directory=home/'.cache/openclaw-account-media'
    if directory.is_symlink():raise SystemExit('Unsafe media directory')
    directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    directory.chmod(0o700)
    with opener.open(request,timeout=60) as response:
        head=response.read(64)
        suffix=('.png' if head.startswith(b'\x89PNG\r\n\x1a\n') else
                '.webp' if head[:4]==b'RIFF' and head[8:12]==b'WEBP' else
                '.webm' if head.startswith(b'\x1aE\xdf\xa3') and b'\x42\x82\x84webm' in head else
                '.mp4' if head[4:8]==b'ftyp' else None)
        if suffix is None:raise SystemExit('Unsupported media format')
        # Unique files avoid overwriting an earlier attachment or following links.
        path=directory/(asset_id+'-'+uuid.uuid4().hex+suffix)
        size=0
        try:
            with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as target:
                chunk=head
                while chunk:
                    size+=len(chunk)
                    if size>256*1024**2:raise ValueError('Media exceeds download limit')
                    target.write(chunk);chunk=response.read(1024*1024)
        except BaseException:
            path.unlink(missing_ok=True)
            raise
    print(json.dumps({'path':str(path),'bytes':size,
                      'delivery_kind':'document' if suffix in {'.webm','.webp'} else 'media'}))


if __name__=='__main__':main()
