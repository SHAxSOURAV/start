import sys
from pathlib import Path

from src.connection.connect_db import DOCUMENT_MODELS

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = WORKSPACE_ROOT / "src"
SCHEMA_MD = WORKSPACE_ROOT / "docs" / "DATABASE_SCHEMA.md"

MAX_FILE_LINES = 1000
WARNING_FILE_LINES = 800


def verify_file_lengths() -> list[str]:
    violations: list[str] = []
    py_files = list(SRC_DIR.rglob("*.py"))

    for py_file in py_files:
        lines = len(py_file.read_text(encoding="utf-8", errors="ignore").splitlines())
        rel_path = py_file.relative_to(WORKSPACE_ROOT)

        if lines > MAX_FILE_LINES:
            violations.append(
                f"FAIL: {rel_path} has {lines} lines (exceeds max limit of {MAX_FILE_LINES})"
            )
        elif lines >= WARNING_FILE_LINES:
            print(f"WARN: {rel_path} has {lines} lines (approaching {MAX_FILE_LINES})")

    return violations


def verify_schema_catalog() -> list[str]:
    violations: list[str] = []
    if not SCHEMA_MD.exists():
        return [f"FAIL: {SCHEMA_MD} does not exist!"]

    schema_content = SCHEMA_MD.read_text(encoding="utf-8")

    for model in DOCUMENT_MODELS:
        model_name = model.__name__
        collection_name = (
            getattr(model.Settings, "name", "") if hasattr(model, "Settings") else ""
        )

        # Verify model name is documented
        if model_name not in schema_content:
            violations.append(
                f"FAIL: Document model '{model_name}' is registered in connect_db.py but missing from docs/DATABASE_SCHEMA.md"
            )
        # Verify collection name is documented
        if collection_name and collection_name not in schema_content:
            violations.append(
                f"FAIL: Collection '{collection_name}' ({model_name}) is missing from docs/DATABASE_SCHEMA.md"
            )

    return violations


def verify_module_naming() -> list[str]:
    violations: list[str] = []
    module_dir = SRC_DIR / "app" / "module"

    allowed_suffixes = {
        "_model.py",
        "_controller.py",
        "_service.py",
        "_routes.py",
        "_validation.py",
        "_constants.py",
        "_utils.py",
        "__init__.py",
    }

    for f in module_dir.rglob("*.py"):
        if f.name.startswith("__pycache__"):
            continue
        # allow nested files or module-level files matching standard suffixes
        if not any(f.name.endswith(suffix) for suffix in allowed_suffixes):
            violations.append(
                f"FAIL: Module file '{f.relative_to(WORKSPACE_ROOT)}' does not follow standard naming conventions ({allowed_suffixes})"
            )

    return violations


def main() -> None:
    print("=" * 60)
    print("  \U0001f50d Verifying Code Standards & Database Schema Sync...")
    print("=" * 60)

    length_violations = verify_file_lengths()
    schema_violations = verify_schema_catalog()
    naming_violations = verify_module_naming()

    all_violations = length_violations + schema_violations + naming_violations

    if all_violations:
        print("\n\u274c Code Standards Verification FAILED:")
        for v in all_violations:
            print(f"  • {v}")
        sys.exit(1)

    print("\u2705 All source files are under 1,000 lines!")
    print(
        f"\u2705 All {len(DOCUMENT_MODELS)} document models are cataloged in docs/DATABASE_SCHEMA.md!"
    )
    print("\u2705 All module files strictly follow architectural naming conventions!")
    print("=" * 60)


if __name__ == "__main__":
    main()
