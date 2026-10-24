"""Upload errors -- the multer error translator's counterpart.

Codes mirror multer's so the client-facing messages are unchanged.
"""

from typing import Any

from src.util.create_error_message import create_error_message


class UploadError(Exception):
    def __init__(self, code: str, field: str | None = None, message: str = "") -> None:
        super().__init__(message or code)
        self.code = code
        self.field = field
        self.message = message


def handle_upload_error(err: UploadError) -> dict[str, Any]:
    code = err.code
    field = err.field
    for_field = f' for field "{field}"' if field else ""

    if code == "LIMIT_UNEXPECTED_FILE":
        message = (
            f"Unexpected file upload detected{for_field}. This field does not "
            "accept files or exceeded the allowed number of files."
        )
    elif code == "LIMIT_FILE_SIZE":
        message = (
            f"File size exceeds the allowed limit{for_field}. "
            "Please upload a smaller file."
        )
    elif code == "LIMIT_FILE_COUNT":
        message = (
            f"Too many files uploaded{for_field}. "
            "Please reduce the number of files and try again."
        )
    elif code == "LIMIT_FIELD_KEY":
        in_field = f' ("{field}")' if field else ""
        message = f"Field name is too long{in_field}. Please use shorter field names."
    elif code == "LIMIT_FIELD_VALUE":
        of_field = f' for "{field}"' if field else ""
        message = f"Field value is too long{of_field}. Please shorten the input value."
    elif code == "LIMIT_FIELD_COUNT":
        message = (
            "Too many form fields were submitted. "
            "Please reduce the number of fields and try again."
        )
    elif code == "LIMIT_PART_COUNT":
        message = (
            "Too many parts in the multipart request. This usually means too "
            "many files or fields were sent together."
        )
    elif code == "MISSING_FIELD_NAME":
        message = (
            "A field is missing its name. Ensure all form fields have valid "
            "names before submitting."
        )
    else:
        message = (
            err.message or "An unexpected file upload error occurred. Please try again."
        )

    return {
        "statusCode": 400,
        "message": message,
        "errorMessages": create_error_message(message, field or ""),
    }
