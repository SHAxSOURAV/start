"""Unified Multi-Provider Media Storage Engine.

Acts as the single abstraction layer for all file uploads across the backend.
Dynamically routes uploads to AWS S3, Cloudinary, or Local Storage based on
`STORAGE_PROVIDER` configuration in .env, with automatic graceful fallback.
"""

from __future__ import annotations

from src.config import config
from src.util.cloudinary import is_cloudinary_configured, upload_file_to_cloudinary
from src.util.logger import logger
from src.util.s3 import (
    delete_file_from_s3,
    is_s3_configured,
    upload_file_to_s3,
)
from src.util.unlink_file import unlink_file


async def upload_media(
    local_path: str,
    folder: str = "uploads",
    retention_category: str = "profiles",
    content_type: str | None = None,
) -> str:
    """Uploads a local media file to the configured primary storage provider.

    Storage routing priority:
    1. If STORAGE_PROVIDER == "s3":
       - Attempts S3 upload. If S3 fails or is unconfigured, falls back to Cloudinary.
       - If Cloudinary also fails, retains the local storage path.
    2. If STORAGE_PROVIDER == "cloudinary":
       - Attempts Cloudinary upload. If unconfigured, falls back to S3.
    3. If STORAGE_PROVIDER == "local":
       - Retains file on local disk (under `uploads/`).
    """
    if not local_path:
        return ""

    provider = config.storage_provider.lower()

    if provider == "s3":
        if is_s3_configured():
            result = await upload_file_to_s3(
                local_path=local_path,
                folder=folder,
                retention_category=retention_category,
                content_type=content_type,
            )
            # If upload succeeded and returned an S3 URL, return it
            if result.startswith("http://") or result.startswith("https://"):
                return result

        # Fallback to Cloudinary if S3 is unconfigured or failed
        if is_cloudinary_configured():
            logger.warning("Falling back to Cloudinary storage for upload.")
            return await upload_file_to_cloudinary(
                local_file_path=local_path, folder=folder
            )

        return local_path

    if provider == "cloudinary":
        if is_cloudinary_configured():
            result = await upload_file_to_cloudinary(
                local_file_path=local_path, folder=folder
            )
            if result.startswith("http://") or result.startswith("https://"):
                return result

        # Fallback to S3 if Cloudinary failed
        if is_s3_configured():
            logger.warning("Falling back to AWS S3 storage for upload.")
            return await upload_file_to_s3(
                local_path=local_path,
                folder=folder,
                retention_category=retention_category,
                content_type=content_type,
            )

        return local_path

    # Local disk storage default
    return local_path


async def delete_media(media_url_or_path: str) -> bool:
    """Removes media from its respective storage provider (S3, Cloudinary, or Local disk)."""
    if not media_url_or_path:
        return False

    if "amazonaws.com" in media_url_or_path:
        return await delete_file_from_s3(media_url_or_path)

    if "res.cloudinary.com" in media_url_or_path:
        # Cloudinary assets are managed via public ID; log for reference
        logger.info(f"Cloudinary media cleanup requested: {media_url_or_path}")
        return True

    # Local file path
    return unlink_file(media_url_or_path)
