"""Asynchronous AWS S3 Media Retention Cleanup Job.

Enforces S3 media lifecycle policies by periodically purging expired objects
based on their category retention thresholds (e.g., Temp: 2 days, Chats: 180 days, Documents: 365 days).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.config import config
from src.util.logger import logger
from src.util.s3 import get_s3_session, is_s3_configured


async def s3_retention_cleanup_job() -> None:
    """Scans and purges expired objects from the S3 bucket based on retention rules."""
    if not is_s3_configured():
        return

    bucket = config.s3.bucket_name
    if not bucket:
        return

    now = datetime.now(UTC)

    # Calculate expiration thresholds for prefix-based categories
    retention_thresholds: dict[str, datetime] = {
        "temp/": now - timedelta(days=config.s3.retention.temp_days),
        "chats/": now - timedelta(days=config.s3.retention.chat_days),
        "documents/": now - timedelta(days=config.s3.retention.document_days),
        "exports/": now - timedelta(days=7),
    }

    session = get_s3_session()
    purged_count = 0

    try:
        async with session.client("s3") as s3:
            for prefix, threshold in retention_thresholds.items():
                paginator = s3.get_paginator("list_objects_v2")
                async for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                    objects = page.get("Contents", [])
                    keys_to_delete = []

                    for obj in objects:
                        last_modified = obj.get("LastModified")
                        if last_modified and last_modified <= threshold:
                            keys_to_delete.append({"Key": obj["Key"]})

                    if keys_to_delete:
                        # Batch delete up to 1000 objects per call (S3 limit)
                        for i in range(0, len(keys_to_delete), 1000):
                            batch = keys_to_delete[i : i + 1000]
                            await s3.delete_objects(
                                Bucket=bucket,
                                Delete={"Objects": batch, "Quiet": True},
                            )
                            purged_count += len(batch)

        if purged_count > 0:
            logger.info(
                f"[S3 Retention Cleanup] Purged {purged_count} expired media objects from S3."
            )

    except Exception as exc:
        logger.error(f"[S3 Retention Cleanup] Error during S3 retention purge: {exc}")
