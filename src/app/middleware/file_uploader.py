import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path

from fastapi import Request
from starlette.datastructures import UploadFile

from src.error.handle_upload_error import UploadError

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_FILE_COUNT = 4

# Extension is derived from the validated MIME type -- never from the
# user-controlled original filename
mime_type_extensions: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
allowed_mime_types: list[str] = list(mime_type_extensions.keys())
allowed_field_names: list[str] = ["profile_image"]

# Field name -> how many files it accepts
field_max_count: dict[str, int] = {"profile_image": 1}


def is_valid_file_type(mimetype: str) -> bool:
    return mimetype in allowed_mime_types


def create_dir_if_not_exists(upload_path: Path) -> None:
    upload_path.mkdir(parents=True, exist_ok=True)


def upload_file() -> Callable[[Request], Awaitable[None]]:
    """Multer equivalent: validates, stores to disk, records paths for rollback."""

    async def dependency(request: Request) -> None:
        content_type = request.headers.get("content-type", "")
        if "multipart/form-data" not in content_type:
            return

        form = await request.form()

        body: dict[str, str] = {}
        files: dict[str, list[dict[str, str]]] = {}
        uploaded_files: list[str] = getattr(request.state, "uploaded_files", None) or []
        request.state.uploaded_files = uploaded_files

        file_count = 0

        for field_name, value in form.multi_items():
            if not isinstance(value, UploadFile):
                body[field_name] = str(value)
                continue

            if not field_name:
                continue

            if field_name not in allowed_field_names:
                raise UploadError("LIMIT_UNEXPECTED_FILE", field_name)

            mimetype = value.content_type or ""
            if not is_valid_file_type(mimetype):
                raise UploadError(
                    "LIMIT_UNEXPECTED_FILE", field_name, "Invalid file type"
                )

            file_count += 1
            if file_count > MAX_FILE_COUNT:
                raise UploadError("LIMIT_FILE_COUNT", field_name)
            if len(files.get(field_name, [])) >= field_max_count.get(field_name, 1):
                raise UploadError("LIMIT_UNEXPECTED_FILE", field_name)

            content = await value.read()
            if len(content) > MAX_FILE_SIZE:
                raise UploadError("LIMIT_FILE_SIZE", field_name)

            upload_path = Path("uploads") / field_name
            create_dir_if_not_exists(upload_path)

            ext = mime_type_extensions.get(mimetype, "")
            name = f"{uuid.uuid4()}{ext}"
            file_path = f"uploads/{field_name}/{name}"

            (upload_path / name).write_bytes(content)

            # Recorded so a failed request can roll the uploads back
            uploaded_files.append(file_path)
            files.setdefault(field_name, []).append(
                {"path": file_path, "filename": name, "mimetype": mimetype}
            )

        request.state.body = body
        request.state.files = files

    return dependency
