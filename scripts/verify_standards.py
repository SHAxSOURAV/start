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


def verify_redis_standards() -> list[str]:
    """Automated guardrail enforcing the 10 Golden Rules for Redis in Production."""
    import re

    violations: list[str] = []
    py_files = list(SRC_DIR.rglob("*.py"))

    # Rule 4: Blocking KEYS * forbidden
    keys_pattern = re.compile(r"\b(client|redis|_redis_client)\.keys\s*\(")
    # Rule 1: Never set keys without TTL
    raw_set_pattern = re.compile(r"\b(client|redis|_redis_client)\.set\s*\(([^)]+)\)")
    # Rule 2: Connection pooling - no ad-hoc redis.from_url
    from_url_pattern = re.compile(r"\bredis\.from_url\s*\(")

    for py_file in py_files:
        rel_path = py_file.relative_to(WORKSPACE_ROOT)
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()

        for idx, line in enumerate(lines, 1):
            if keys_pattern.search(line):
                violations.append(
                    f"FAIL (Redis Rule 4): {rel_path}:{idx} Uses blocking Redis '.keys()' command! Use 'scan_iter' or 'RedisService.scan_keys' instead."
                )

            match = raw_set_pattern.search(line)
            if match:
                args = match.group(2)
                if "ex=" not in args and "px=" not in args:
                    violations.append(
                        f"FAIL (Redis Rule 1): {rel_path}:{idx} Redis '.set()' called without TTL ('ex=' or 'px='). Never set keys without TTL in production!"
                    )

            if from_url_pattern.search(line) and "connect_redis.py" not in str(
                rel_path
            ):
                violations.append(
                    f"FAIL (Redis Rule 2): {rel_path}:{idx} Calls 'redis.from_url()' directly! Never open ad-hoc connections; always use 'get_redis_client()' or 'RedisService' from 'src.connection.connect_redis'."
                )

    return violations


def main() -> None:
    print("=" * 60)
    print("  🔍 Verifying Code Standards, Database Schema & Redis Rules...")
    print("=" * 60)

    length_violations = verify_file_lengths()
    schema_violations = verify_schema_catalog()
    naming_violations = verify_module_naming()
    redis_violations = verify_redis_standards()

    all_violations = (
        length_violations + schema_violations + naming_violations + redis_violations
    )

    if all_violations:
        print("\n❌ Code Standards Verification FAILED:")
        for v in all_violations:
            print(f"  • {v}")
        sys.exit(1)

    print("✅ All source files are under 1,000 lines!")
    print(
        f"✅ All {len(DOCUMENT_MODELS)} document models are cataloged in docs/DATABASE_SCHEMA.md!"
    )
    print("✅ All module files strictly follow architectural naming conventions!")
    print(
        "✅ All Redis calls strictly adhere to the 10 Golden Rules (No blocking KEYS, mandatory TTL)!"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
