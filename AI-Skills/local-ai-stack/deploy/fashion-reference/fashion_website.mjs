/** Node.js backend example. No npm dependencies. Never ship connection keys to browsers. */
import { createReadStream, createWriteStream } from 'node:fs';
import { mkdir, stat } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { Readable } from 'node:stream';
import { pipeline } from 'node:stream/promises';
import { setTimeout as sleep } from 'node:timers/promises';
import { parseArgs } from 'node:util';
import { pathToFileURL } from 'node:url';

function uuid(value) {
  if (typeof value !== 'string' || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value)) {
    throw new Error('Use a valid UUID for request, asset and job IDs.');
  }
  return value.toLowerCase();
}

export class LocalAI {
  constructor(base, key) {
    const url = new URL(base);
    if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash ||
        url.pathname.replace(/\/$/, '') !== '/api/v1/gpu-api' || !key) {
      throw new Error('Set a trusted HTTPS LOCAL_AI_API_BASE ending /api/v1/gpu-api and a connection key.');
    }
    this.base = url.href.replace(/\/$/, '');
    this.key = key;
  }

  async request(method, path, { json, body, headers = {} } = {}) {
    // Only this client constructs paths; never follow server-supplied asset URLs.
    if (!path.startsWith('/') || path.startsWith('//')) throw new Error('Invalid API path.');
    const response = await fetch(this.base + path, {
      method, redirect: 'error', signal: AbortSignal.timeout(90_000),
      headers: { ...headers, Authorization: `Bearer ${this.key}`,
        ...(json !== undefined ? { 'Content-Type': 'application/json' } : {}) },
      body: json !== undefined ? JSON.stringify(json) : body,
      ...(body ? { duplex: 'half' } : {}),
    });
    if (!response.ok) {
      await response.body?.cancel();
      throw new Error(`API returned HTTP ${response.status}. Check permissions, limits and job status before retrying.`);
    }
    return response;
  }

  async products(url) {
    return (await this.request('POST', '/products/preview', { json: { url } })).json();
  }

  async image(url, destination) {
    const response = await this.request('POST', '/products/image', { json: { url } });
    await pipeline(Readable.fromWeb(response.body), createWriteStream(destination, { flags: 'wx' }));
  }

  async workflows() {
    return (await (await this.request('GET', '/workflows')).json()).workflows;
  }

  async uploadBundle(filename) {
    const info = await stat(filename);
    if (!info.isFile() || info.size > 32 * 1024 ** 2) throw new Error('Use a reference ZIP no larger than 32 MiB.');
    const response = await this.request('POST', '/assets?filename=references.zip', {
      body: createReadStream(filename),
      headers: { 'Content-Type': 'application/octet-stream', 'Content-Length': String(info.size) },
    });
    return (await response.json()).asset.id;
  }

  async submit({ workflow, prompt, assetId, requestId }) {
    return (await this.request('POST', '/jobs', { json: {
      workflow, values: { prompt }, asset_id: uuid(assetId), request_id: uuid(requestId),
    } })).json();
  }

  async job(jobId) {
    return (await this.request('GET', `/jobs/${uuid(jobId)}`)).json();
  }

  async wait(job, timeoutMs = 30 * 60 * 1000) {
    const deadline = Date.now() + timeoutMs;
    while (!['complete', 'failed', 'cancelled'].includes(job.status)) {
      if (Date.now() >= deadline) throw new Error(`Job ${job.job_id} is still pending; resume polling rather than submitting a new job.`);
      await sleep(3000);
      job = await this.job(job.job_id);
      console.log('Status:', job.status);
    }
    if (job.status !== 'complete') throw new Error(`Job ${job.job_id}: ${job.status}`);
    return job;
  }

  async download(job, directory) {
    await mkdir(directory, { recursive: true });
    for (const asset of job.assets ?? []) {
      const id = uuid(asset.id);
      const response = await this.request('GET', `/assets/${id}/content`);
      // Preserve a simple extension, never trust server-provided paths or URLs.
      const extension = typeof asset.name === 'string' ? asset.name.match(/\.[a-z0-9]{1,8}$/i)?.[0] ?? '' : '';
      const destination = join(directory, id + extension);
      await pipeline(Readable.fromWeb(response.body), createWriteStream(destination, { flags: 'wx' }));
      console.log('Saved:', destination);
    }
  }
}

export async function main() {
  const { values: args } = parseArgs({ options: {
    product: { type: 'string' }, image: { type: 'string' }, bundle: { type: 'string' },
    'asset-id': { type: 'string' }, 'request-id': { type: 'string' }, 'job-id': { type: 'string' },
    prompt: { type: 'string', default: 'Put these clothes on a mannequin.' },
    output: { type: 'string', default: 'fashion-output' },
  } });
  const api = new LocalAI(process.env.LOCAL_AI_API_BASE, process.env.LOCAL_AI_CONNECTION_KEY);
  if (args.product) { console.log(JSON.stringify(await api.products(args.product), null, 2)); return; }
  if (args.image) { await api.image(args.image, args.output); console.log('Saved WebP:', args.output); return; }
  let job;
  if (args['job-id']) {
    job = await api.job(args['job-id']);
  } else {
    const requestId = uuid(args['request-id']); // Validate before creating an upload.
    const workflow = process.env.LOCAL_AI_FASHION_WORKFLOW;
    const workflows = await api.workflows();
    if (!workflow || !Object.hasOwn(workflows, workflow)) throw new Error('Configure an installed, verified fashion workflow.');
    if (!args['asset-id'] && !args.bundle) throw new Error('Provide --bundle references.zip or reuse --asset-id UUID.');
    const assetId = args['asset-id'] ? uuid(args['asset-id']) : await api.uploadBundle(args.bundle);
    console.log('Save for retries: --asset-id', assetId, '--request-id', requestId);
    job = await api.submit({ workflow, prompt: args.prompt, assetId, requestId });
    console.log('Job ID:', job.job_id);
  }
  await api.download(await api.wait(job), args.output);
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  main().catch(error => { console.error(error.message); process.exitCode = 1; });
}
