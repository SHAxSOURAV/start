"""Enterprise AWS S3 Storage Adapter.

Provides native AsyncIO S3 file uploads, cryptographic presigned upload/download URLs,
and media retention lifecycle management. Eliminates local disk storage bottlenecks
and handles high-concurrency media pipelines.
"""

from __future__ import annotations

import mimetypes
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import aioboto3
import aiofiles

from src.config import config
from src.util.logger import logger
from src.util.unlink_file import unlink_file

# Recognized retention categories and default retention days
RETENTION_POLICIES: dict[str, int | None] = {
    "temp": config.s3.retention.temp_days,  # Short-lived draft/temp uploads
    "chats": config.s3.retention.chat_days,  # Chat attachments & media
    "documents": config.s3.retention.document_days,  # KYC & verification documents
    "exports": 7,  # Generated reports & invoices
    "profiles": None,  # Permanent: user avatars & branding
}


def is_s3_configured() -> bool:
    """Checks if AWS S3 credentials and bucket name are fully configured."""
    return bool(
        config.s3.access_key_id
        and config.s3.secret_access_key
        and config.s3.bucket_name
    )


def get_s3_session() -> aioboto3.Session:
    """Creates a configured aioboto3 Session."""
    return aioboto3.Session(
        aws_access_key_id=config.s3.access_key_id,
        aws_secret_access_key=config.s3.secret_access_key,
        region_name=config.s3.region,
    )


def _extract_s3_key(s3_url_or_key: str) -> str:
    """Extracts S3 object key from full HTTPS S3 URL or returns the key directly."""
    if s3_url_or_key.startswith("http://") or s3_url_or_key.startswith("https://"):
        parsed = urlparse(s3_url_or_key)
        # /path/to/key -> path/to/key
        return parsed.path.lstrip("/")
    return s3_url_or_key


async def upload_file_to_s3(
    local_path: str,
    folder: str = "uploads",
    custom_filename: str | None = None,
    content_type: str | None = None,
    retention_category: str = "profiles",
) -> str:
    """Uploads a local file to AWS S3 asynchronously.

    - Tags object with RetentionCategory for automated lifecycle pruning.
    - If upload succeeds -> unlinks local temporary file and returns public HTTPS S3 URL.
    - If S3 is unconfigured or upload fails -> logs warning and falls back to local_path.
    """
    if not is_s3_configured():
        logger.warning("AWS S3 is not configured in .env. Falling back to local storage.")
        return local_path

    file_obj = Path(local_path)
    if not file_obj.exists():
        logger.error(f"Local file does not exist: {local_path}")
        return local_path

    # Generate unique sanitized key
    ext = file_obj.suffix.lower()
    unique_name = custom_filename or f"{uuid.uuid4().hex}{ext}"
    s3_key = f"{folder.strip('/')}/{unique_name}"

    # Determine Content-Type
    if not content_type:
        guessed_type, _ = mimetypes.guess_type(local_path)
        content_type = guessed_type or "application/octet-stream"

    # Retention Tagging
    tagging_str = (
        f"RetentionCategory={retention_category}&"
        f"UploadedAt={datetime.now(UTC).strftime('%Y%m%d')}"
    )

    bucket = config.s3.bucket_name
    assert bucket is not None

    session = get_s3_session()
    try:
        async with session.client("s3") as s3:
            async with aiofiles.open(local_path, "rb") as f:
                file_bytes = await f.read()

            await s3.put_object(
                Bucket=bucket,
                Key=s3_key,
                Body=file_bytes,
                ContentType=content_type,
                Tagging=tagging_str,
            )

        # Successfully uploaded: unlink local temporary file
        unlink_file(local_path)

        s3_url = f"https://{bucket}.s3.{config.s3.region}.amazonaws.com/{s3_key}"
        logger.info(f"File uploaded to AWS S3: {s3_url} (Category: {retention_category})")
        return s3_url

    except Exception as exc:
        logger.error(
            f"AWS S3 upload failed for {local_path}: {exc}. Falling back to local storage."
        )
        return local_path


async def delete_file_from_s3(s3_url_or_key: str) -> bool:
    """Deletes an object from AWS S3."""
    if not is_s3_configured() or not s3_url_or_key:
        return False

    s3_key = _extract_s3_key(s3_url_or_key)
    bucket = config.s3.bucket_name
    assert bucket is not None

    session = get_s3_session()
    try:
        async with session.client("s3") as s3:
            await s3.delete_object(Bucket=bucket, Key=s3_key)
        logger.info(f"Deleted AWS S3 object: {s3_key}")
        return True
    except Exception as exc:
        logger.error(f"Failed to delete AWS S3 object {s3_key}: {exc}")
        return False


async def generate_presigned_upload_url(
    folder: str = "uploads",
    filename: str | None = None,
    content_type: str = "image/jpeg",
    expires_in: int = 3600,
    retention_category: str = "profiles",
) -> dict[str, Any]:
    """Generates a cryptographic presigned PUT URL for direct client-to-S3 uploads.

    Allows mobile and web clients to upload files directly to S3 without passing
    through the backend server (Zero Server RAM/CPU Load).
    """
    if not is_s3_configured():
        return {
            "configured": False,
            "message": "AWS S3 is not configured on the server.",
        }

    ext = os.path.splitext(filename or "")[1].lower() or ".jpg"
    unique_key = f"{folder.strip('/')}/{uuid.uuid4().hex}{ext}"
    bucket = config.s3.bucket_name
    assert bucket is not None

    session = get_s3_session()
    async with session.client("s3") as s3:
        params: dict[str, Any] = {
            "Bucket": bucket,
            "Key": unique_key,
            "ContentType": content_type,
            "Tagging": (
                f"RetentionCategory={retention_category}&"
                f"UploadedAt={datetime.now(UTC).strftime('%Y%m%d')}"
            ),
        }
        presigned_url = await s3.generate_presigned_url(
            ClientMethod="put_object",
            Params=params,
            ExpiresIn=expires_in,
        )

    public_url = f"https://{bucket}.s3.{config.s3.region}.amazonaws.com/{unique_key}"

    return {
        "configured": True,
        "uploadUrl": presigned_url,
        "key": unique_key,
        "publicUrl": public_url,
        "expiresIn": expires_in,
        "retentionCategory": retention_category,
    }


async def generate_presigned_download_url(
    s3_url_or_key: str, expires_in: int = 3600
) -> str:
    """Generates a presigned GET URL to securely access private S3 media."""
    if not is_s3_configured():
        return s3_url_or_key

    s3_key = _extract_s3_key(s3_url_or_key)
    bucket = config.s3.bucket_name
    assert bucket is not None

    session = get_s3_session()
    async with session.client("s3") as s3:
        return await s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": s3_key},
            ExpiresIn=expires_in,
        )
