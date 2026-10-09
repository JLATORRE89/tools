"""Typed MCP adapters for the existing local ComfyUI job API."""
import httpx
import os
from uuid import UUID

async def _api(path, payload=None):
    async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
        response = await client.request('GET' if payload is None else 'POST',
                                      os.environ.get('COMFYUI_JOB_API_URL', 'http://127.0.0.1:8770').rstrip('/') + path, json=payload)
        response.raise_for_status()
        return response.json()

def register(mcp):
    @mcp.tool(annotations={'readOnlyHint': True})
    async def list_comfyui_artifacts() -> dict:
        """List live local image checkpoints, LoRAs, samplers and limits. Call before generation."""
        return await _api('/artifacts')

    @mcp.tool(annotations={'readOnlyHint': True})
    async def list_comfyui_video_artifacts() -> dict:
        """Check local Wan video model readiness and supported dimensions/frame counts."""
        return await _api('/video/artifacts')

    @mcp.tool(annotations={'readOnlyHint': False, 'destructiveHint': False})
    async def generate_comfyui_image(positive_prompt: str,
            checkpoint: str = 'DreamShaper_8_pruned.safetensors',
            negative_prompt: str = '', width: int = 512, height: int = 512,
            steps: int = 24, seed: int | None = None) -> dict:
        """Generate an image on local Intel GPU. Returns job_id; poll get_comfyui_job for image URLs. Existing inventory and resource limits apply."""
        return await _api('/generate', dict(positive_prompt=positive_prompt,
            checkpoint=checkpoint, negative_prompt=negative_prompt, width=width,
            height=height, steps=steps, seed=seed, seed_mode='fixed' if seed is not None else 'random'))

    @mcp.tool(annotations={'readOnlyHint': False, 'destructiveHint': False})
    async def generate_comfyui_video(positive_prompt: str, negative_prompt: str = '',
            width: int = 512, height: int = 512, frames: int = 17,
            fps: float = 8, steps: int = 20, seed: int | None = None) -> dict:
        """Generate a short local Wan2.1 video. Frames must be 4n+1. Returns job_id; poll get_comfyui_job for video URLs. This can take minutes."""
        return await _api('/video/generate', dict(positive_prompt=positive_prompt,
            negative_prompt=negative_prompt, width=width, height=height, frames=frames,
            fps=fps, steps=steps, seed=seed, seed_mode='fixed' if seed is not None else 'random'))

    @mcp.tool(annotations={'readOnlyHint': True})
    async def get_comfyui_job(job_id: str) -> dict:
        """Poll a submitted ComfyUI job; returns completion/errors and HTTPS image/video URLs. Never claim completion until this reports it."""
        UUID(job_id)
        return await _api('/jobs/' + job_id)
