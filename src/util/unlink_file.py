from pathlib import Path

from src.error.api_error import ApiError
from src.util.http_status import status


def unlink_file(file_path: str) -> bool:
    try:
        if not file_path:
            raise ApiError(status.BAD_REQUEST, "File path is required")

        # Skip remote URLs (e.g. Cloudinary CDN assets)
        if file_path.startswith(("http://", "https://")):
            return True

        path = Path(file_path)
        if path.exists():
            path.unlink()

        return True
    except Exception as error:
        print("Error unlinking file:", error)
        raise
