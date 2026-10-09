"""Backend client: pip install requests Pillow. Secrets stay in environment."""
import argparse
import io
import os
from pathlib import Path
import time
import uuid
import zipfile

import requests
from PIL import Image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--product', help='Discover images from a product page, then exit')
    parser.add_argument('--image', action='append', default=[], help='Selected image URL; repeat in reference order')
    parser.add_argument('--asset-id', help='Reuse an uploaded reference bundle for retries')
    parser.add_argument('--request-id', help='Persist this UUID before submission; reuse on retry')
    parser.add_argument('--prompt', default='Put these clothes on a mannequin.')
    parser.add_argument('--output', default='fashion-output')
    args = parser.parse_args()
    base = os.environ['LOCAL_AI_API_BASE'].rstrip('/')
    if not base.startswith('https://'):
        parser.error('Use a trusted HTTPS API origin')
    session = requests.Session()
    session.headers['Authorization'] = 'Bearer ' + os.environ['LOCAL_AI_CONNECTION_KEY']
    def call(method, path, **kwargs):
        response = session.request(method, base + path, timeout=(10,90), allow_redirects=False, **kwargs)
        if not 200 <= response.status_code < 300:
            raise RuntimeError(f'API returned {response.status_code}: {response.text[:500]}')
        return response
    if args.product:
        print(call('POST', '/products/preview', json={'url':args.product}).json())
        return
    if not args.request_id:
        parser.error('Choose and persist --request-id UUID before submitting')
    request_id = str(uuid.UUID(args.request_id))
    workflow = os.environ['LOCAL_AI_FASHION_WORKFLOW']
    workflows = call('GET', '/workflows').json()['workflows']
    if workflow not in workflows:
        parser.error('The requested local workflow is not available')
    asset = args.asset_id
    if not asset:
        if not 1 <= len(args.image) <= 8 or workflows[workflow].get('reference_count') != len(args.image):
            parser.error('Provide the exact number of --image references advertised by this workflow')
        bundle = io.BytesIO()
        with zipfile.ZipFile(bundle, 'w', compression=zipfile.ZIP_STORED) as archive:
            for index, url in enumerate(args.image):
                data = call('POST', '/products/image', json={'url':url}).content
                with Image.open(io.BytesIO(data)) as source:
                    image = source.convert('RGB'); image.thumbnail((1024,1024))
                    png = io.BytesIO(); image.save(png, format='PNG')
                    if png.tell() > 4*1024**2:
                        raise ValueError('Reference exceeds bundle image limit')
                    archive.writestr(f'{index}.png', png.getvalue())
        asset = call('POST', '/assets', params={'filename':'references.zip'},
                     data=bundle.getvalue(), headers={'Content-Type':'application/octet-stream'}).json()['asset']['id']
        print('Save for retry: --asset-id', asset, flush=True)
    job = call('POST', '/jobs', json={'workflow':workflow, 'values':{'prompt':args.prompt},
                                     'asset_id':asset, 'request_id':request_id}).json()
    print('Job:', job['job_id'], flush=True)
    deadline = time.monotonic()+1800
    while job['status'] not in {'complete','failed','cancelled'}:
        if time.monotonic()>deadline:
            raise TimeoutError('Job still pending. Poll its ID later; do not resubmit with a new ID.')
        time.sleep(3)
        job = call('GET', '/jobs/'+job['job_id']).json()
        print(job['status'], flush=True)
    if job['status'] != 'complete':
        raise RuntimeError('Render did not succeed: '+job['status'])
    output = Path(args.output); output.mkdir(parents=True, exist_ok=True)
    for asset in job['assets']:
        asset_id = str(uuid.UUID(asset['id']))
        # Construct an API path; never forward credentials to arbitrary result URLs.
        response = call('GET', '/assets/'+asset_id+'/content', stream=True)
        with response, (output / asset_id).open('xb') as destination:
            for chunk in response.iter_content(1024*1024):
                destination.write(chunk)
        print('Saved', output / asset_id)


if __name__ == '__main__':
    main()
