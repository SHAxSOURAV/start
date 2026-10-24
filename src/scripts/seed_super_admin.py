import asyncio
import sys

from src.app.module.admin.admin_model import Admin
from src.app.module.auth.auth_model import Auth
from src.config import config
from src.connection.connect_db import connect_db, disconnect_db
from src.util.enum import EnumUserRole

# Idempotent: creates the SUPER_ADMIN account once; exits quietly if it exists.
# Usage: python -m src.scripts.seed_super_admin
# (requires SUPER_ADMIN_EMAIL and SUPER_ADMIN_PASSWORD in .env)


async def seed_super_admin() -> None:
    email = config.super_admin.email
    password = config.super_admin.password
    name = "Super Admin"

    if not email or not password:
        print(
            "Missing SUPER_ADMIN_EMAIL or SUPER_ADMIN_PASSWORD in the environment",
            file=sys.stderr,
        )
        sys.exit(1)

    await connect_db()

    existing = await Auth.find_one({"email": email})
    if existing:
        print(f"Super admin already exists: {email}")
    else:
        auth = Auth(
            name=name,
            email=email,
            password=password,
            role=EnumUserRole.SUPER_ADMIN,
            isActive=True,
        )
        await auth.insert()

        await Admin(authId=auth.id, name=name, email=email).insert()

        print(f"Super admin created: {email}")

    await disconnect_db()


if __name__ == "__main__":
    try:
        asyncio.run(seed_super_admin())
        sys.exit(0)
    except SystemExit:
        raise
    except Exception as error:
        print("Seeding failed:", error, file=sys.stderr)
        sys.exit(1)
