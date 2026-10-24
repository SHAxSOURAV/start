import pytest

from src.config import config
from src.util.media_storage import delete_media, upload_media
from src.util.s3 import (
    _extract_s3_key,
    generate_presigned_upload_url,
    is_s3_configured,
)


def test_is_s3_configured() -> None:
    """Verifies that S3 configuration validation works."""
    assert is_s3_configured() is True
    assert bool(config.s3.bucket_name)
    assert config.s3.region == "eu-north-1"
    assert config.storage_provider == "s3"


def test_extract_s3_key() -> None:
    """Tests S3 key extraction from full URLs and direct keys."""
    full_url = f"https://{config.s3.bucket_name}.s3.{config.s3.region}.amazonaws.com/profile_images/test.jpg"
    assert _extract_s3_key(full_url) == "profile_images/test.jpg"

    direct_key = "documents/kyc_doc.pdf"
    assert _extract_s3_key(direct_key) == "documents/kyc_doc.pdf"


@pytest.mark.asyncio
async def test_generate_presigned_upload_url() -> None:
    """Verifies presigned upload URL generation."""
    res = await generate_presigned_upload_url(
        folder="temp",
        filename="test_image.png",
        content_type="image/png",
        expires_in=1800,
        retention_category="temp",
    )
    assert res["configured"] is True
    assert "uploadUrl" in res
    assert "https://" in res["uploadUrl"]
    assert config.s3.bucket_name in res["uploadUrl"]
    assert res["key"].startswith("temp/")
    assert res["retentionCategory"] == "temp"


@pytest.mark.asyncio
async def test_media_storage_empty_input() -> None:
    """Ensures empty paths yield empty results gracefully."""
    res = await upload_media("", folder="temp")
    assert res == ""

    del_res = await delete_media("")
    assert del_res is False
