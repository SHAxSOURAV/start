"""Enterprise Cloudinary Helper Utility.

Provides direct client-to-cloud signed upload signatures,
dynamic real-time transformation URL builders, and signed private media delivery.
Eliminates heavy image/video processing (Pillow, FFmpeg) on the backend server.
"""

import hashlib
import time
from pathlib import Path
from typing import Any

import httpx

from src.config import config
from src.util.logger import logger


def is_cloudinary_configured() -> bool:
    """Checks if Cloudinary credentials are fully configured."""
    return bool(
        config.cloudinary.cloud_name
        and config.cloudinary.api_key
        and config.cloudinary.api_secret
    )


def generate_upload_signature(
    folder: str = "uploads",
    public_id: str | None = None,
    tags: list[str] | None = None,
    eager: str | None = None,
) -> dict[str, Any]:
    """Generates a cryptographic signature for client-side direct uploads.

    The frontend (React/Flutter/Web) uploads directly to Cloudinary's Edge CDN
    using this signature, bypassing the backend server completely (Zero Server Memory Load).
    """
    if not is_cloudinary_configured():
        logger.warning("Cloudinary credentials are not configured in .env")
        return {
            "configured": False,
            "message": "Cloudinary is not configured. Falling back to local storage.",
        }

    timestamp = int(time.time())
    params: dict[str, Any] = {
        "folder": folder,
        "timestamp": timestamp,
    }

    if public_id:
        params["public_id"] = public_id
    if tags:
        params["tags"] = ",".join(tags)
    if eager:
        params["eager"] = eager

    # Sort parameters alphabetically by key as required by Cloudinary
    sorted_pairs = sorted([f"{k}={v}" for k, v in params.items() if v is not None])
    to_sign = "&".join(sorted_pairs) + str(config.cloudinary.api_secret)

    signature = hashlib.sha1(to_sign.encode("utf-8")).hexdigest()

    return {
        "configured": True,
        "signature": signature,
        "timestamp": timestamp,
        "apiKey": config.cloudinary.api_key,
        "cloudName": config.cloudinary.cloud_name,
        "folder": folder,
        "uploadUrl": f"https://api.cloudinary.com/v1_1/{config.cloudinary.cloud_name}/auto/upload",
    }


def get_transformed_url(
    public_id: str,
    preset: str = "avatar",
    custom_transform: str | None = None,
) -> str:
    """Builds optimized Cloudinary CDN transformation URLs on-the-fly.

    Presets:
    - avatar: Face-centered smart crop, circular radius, WebP/AVIF auto-format
    - thumbnail: AI smart crop (400x300), auto-quality
    - banner: 16:9 responsive landscape banner (1200x630)
    - blur: Blurred placeholder (for paywalled or loading states)
    """
    cloud_name = config.cloudinary.cloud_name or "demo"
    base = f"https://res.cloudinary.com/{cloud_name}/image/upload"

    presets: dict[str, str] = {
        "avatar": "c_thumb,g_face,w_300,h_300,r_max/f_auto,q_auto",
        "thumbnail": "c_fill,g_auto,w_400,h_300/f_auto,q_auto",
        "banner": "c_fill,g_auto,w_1200,h_630/f_auto,q_auto",
        "blur": "e_blur:2000,f_auto,q_auto",
    }

    transform = custom_transform or presets.get(preset, "f_auto,q_auto")
    return f"{base}/{transform}/{public_id}"


def get_video_hls_url(public_id: str) -> str:
    """Returns adaptive bitrate streaming URL (.m3u8) for video playback."""
    cloud_name = config.cloudinary.cloud_name or "demo"
    return f"https://res.cloudinary.com/{cloud_name}/video/upload/sp_auto/f_m3u8/{public_id}.m3u8"


async def upload_file_to_cloudinary(
    local_file_path: str,
    folder: str = "uploads",
    resource_type: str = "auto",
) -> str:
    """Uploads a local file to Cloudinary asynchronously via REST API.

    Fallback Architecture:
    - If Cloudinary is unconfigured -> immediately returns local_file_path (Disk Storage fallback).
    - If upload fails due to network/API error -> logs warning and returns local_file_path.
    - If upload succeeds -> unlinks local temporary file and returns HTTPS CDN URL.
    """
    if not is_cloudinary_configured():
        return local_file_path

    path_obj = Path(local_file_path)
    if not path_obj.exists():
        return local_file_path

    timestamp = int(time.time())
    to_sign = f"folder={folder}&timestamp={timestamp}{config.cloudinary.api_secret}"
    signature = hashlib.sha1(to_sign.encode("utf-8")).hexdigest()

    upload_url = f"https://api.cloudinary.com/v1_1/{config.cloudinary.cloud_name}/{resource_type}/upload"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            with open(path_obj, "rb") as file_data:
                files = {"file": file_data}
                data = {
                    "api_key": config.cloudinary.api_key,
                    "timestamp": str(timestamp),
                    "signature": signature,
                    "folder": folder,
                }
                response = await client.post(upload_url, data=data, files=files)

        if response.status_code == 200:
            result = response.json()
            secure_url = result.get("secure_url")
            if secure_url:
                try:
                    path_obj.unlink(missing_ok=True)
                except Exception:
                    pass
                return str(secure_url)

        logger.warning(
            f"Cloudinary upload failed with status {response.status_code}: {response.text}. Falling back to local storage."
        )
        return local_file_path
    except Exception as exc:
        logger.error(f"Cloudinary upload exception: {exc}. Falling back to local storage.")
        return local_file_path

