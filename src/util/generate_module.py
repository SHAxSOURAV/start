import sys
from pathlib import Path

from src.util.file_templates import (
    controller_template,
    model_template,
    routes_template,
    service_template,
)

# Scaffolds a new domain module under src/app/module/<name>.
# Usage: python -m src.util.generate_module <ModuleName>


def generate_module(raw_name: str) -> None:
    module_name = raw_name[:1].upper() + raw_name[1:]
    module_folder = raw_name.lower()
    dir_path = Path.cwd() / "src" / "app" / "module" / module_folder

    if dir_path.exists():
        print(f"\U0001f6ab {module_name} module already exists.")
        return

    dir_path.mkdir(parents=True)
    (dir_path / "__init__.py").write_text("", encoding="utf-8")

    (dir_path / f"{module_folder}_model.py").write_text(
        model_template(module_name), encoding="utf-8"
    )
    (dir_path / f"{module_folder}_controller.py").write_text(
        controller_template(module_name), encoding="utf-8"
    )
    (dir_path / f"{module_folder}_routes.py").write_text(
        routes_template(module_name), encoding="utf-8"
    )
    (dir_path / f"{module_folder}_service.py").write_text(
        service_template(module_name), encoding="utf-8"
    )

    print(f"\u2705 {module_name} module files created successfully!")
    print("\U0001f449 Remember to mount the new router in src/app/routes/__init__.py")
    print(
        "\U0001f449 And register the new document model in src/connection/connect_db.py"
    )
    print(
        "\U0001f449 And catalog the collection, fields & indexes in docs/DATABASE_SCHEMA.md"
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python -m src.util.generate_module <ModuleName>",
            file=sys.stderr,
        )
        sys.exit(1)

    generate_module(sys.argv[1])
