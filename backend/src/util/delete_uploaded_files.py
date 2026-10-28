from pathlib import Path

GREEN_BG = "\033[42m"
RED_BG = "\033[41m"
YELLOW_BG = "\033[43m"
RESET = "\033[0m"


def delete_uploaded_files(uploaded_files: list[str] | None) -> None:
    if not uploaded_files:
        return

    for file_path in uploaded_files:
        path = Path(file_path)
        if path.exists():
            try:
                path.unlink()
                print(f"{GREEN_BG}\u2705 Deleted file: {file_path}{RESET}")
            except OSError as err:
                print(f"{RED_BG}\u274c Failed to delete file: {file_path}{RESET}", err)
        else:
            print(f"{YELLOW_BG}\u26a0\ufe0f File does not exist: {file_path}{RESET}")
