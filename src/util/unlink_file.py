from pathlib import Path

from src.error.api_error import ApiError
from src.util.http_status import status


def unlink_file(file_path: str) -> bool:
    try:
        if not file_path:
            raise ApiError(status.BAD_REQUEST, "File path is required")

        path = Path(file_path)
        path.stat()  # raises if the file is missing
        path.unlink()

        return True
    except Exception as error:
        print("Error unlinking file:", error)
        raise
