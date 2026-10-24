from typing import Any

from src.util.unlink_file import unlink_file


def process_file_updates(
    files: dict[str, list[dict[str, Any]]] | None,
    file_fields: list[dict[str, Any]],
) -> dict[str, str | list[str]]:
    files = files or {}
    update_data: dict[str, str | list[str]] = {}

    for entry in file_fields:
        key = entry["key"]
        old_path = entry["oldPath"]

        # Ensure the uploaded file list exists and we have an old path to replace
        if not files.get(key) or not old_path:
            continue

        if isinstance(old_path, list):
            # For lists: map new paths and unlink old files
            update_data[key] = [file["path"] for file in files[key]]
            for path in old_path:
                if path:
                    unlink_file(path)
        else:
            # For single files: use the first file and unlink the old one
            first_file = files[key][0] if files[key] else None
            if first_file:
                update_data[key] = first_file["path"]
                unlink_file(old_path)

    return update_data
