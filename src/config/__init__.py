"""Single source of truth for environment variables.

Keep .env.example in sync with this schema -- the app refuses to boot on a
mismatch.
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import AliasChoices, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(dotenv_path=Path.cwd() / ".env")


class EnvSchema(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", case_sensitive=True)

    NODE_ENV: Literal["development", "production", "test"] = "development"
    BASE_URL: str = "0.0.0.0"
    PORT: int = 8001

    MONGO_URL: str = Field(min_length=1)
    DB_NAME: str | None = None

    BCRYPT_SALT_ROUNDS: int = 10
    JWT_SECRET: str = Field(min_length=32)
    JWT_EXPIRES_IN: str = "15m"
    JWT_REFRESH_SECRET: str = Field(min_length=32)
    JWT_REFRESH_EXPIRES_IN: str = "30d"

    SMTP_HOST: str | None = None
    SMTP_PORT: int | None = None
    SMTP_SERVICE: str | None = None
    SMTP_MAIL: str | None = Field(
        default=None, validation_alias=AliasChoices("SMTP_MAIL", "SMTP_EMAIL")
    )
    SMTP_PASSWORD: str | None = None
    SERVICE_NAME: str = "Server Template"

    SUPER_ADMIN_EMAIL: str | None = None
    SUPER_ADMIN_PASSWORD: str | None = None

    STRIPE_SECRET_KEY: str | None = None

    CLOUD_NAME: str | None = None
    API_KEY: str | None = None
    API_SECRET: str | None = None
    CLOUDINARY_URL: str | None = None

    EMAIL_TEMP_IMAGE: str | None = None
    EMAIL_TEMP_TEXT_SECONDARY_COLOR: str | None = None

    ONESIGNAL_APP_ID: str | None = None
    ONESIGNAL_REST_API_KEY: str | None = None

    GOOGLE_CLIENT_ID: str | None = None
    APPLE_CLIENT_ID: str | None = None


try:
    env = EnvSchema()  # type: ignore[call-arg]
except ValidationError as exc:
    print("\u274c Invalid environment configuration:", file=sys.stderr)
    for issue in exc.errors():
        path = ".".join(str(p) for p in issue["loc"])
        print(f"  - {path}: {issue['msg']}", file=sys.stderr)
    sys.exit(1)


@dataclass(frozen=True)
class AuthLevel:
    user: list[str] = field(default_factory=lambda: ["USER", "ADMIN", "SUPER_ADMIN"])
    admin: list[str] = field(default_factory=lambda: ["ADMIN", "SUPER_ADMIN"])
    super_admin: list[str] = field(default_factory=lambda: ["SUPER_ADMIN"])


@dataclass(frozen=True)
class JwtConfig:
    secret: str
    refresh_secret: str
    expires_in: str
    refresh_expires_in: str


@dataclass(frozen=True)
class SmtpConfig:
    smtp_host: str | None
    smtp_port: int | None
    smtp_service: str | None
    smtp_mail: str | None
    smtp_password: str | None
    NAME: str


@dataclass(frozen=True)
class CloudinaryConfig:
    cloud_name: str | None
    api_key: str | None
    api_secret: str | None
    cloudinary_url: str | None


@dataclass(frozen=True)
class StripeConfig:
    stripe_secret_key: str | None


@dataclass(frozen=True)
class SuperAdminConfig:
    email: str | None
    password: str | None


@dataclass(frozen=True)
class Variables:
    email_temp_image: str | None
    email_temp_text_secondary_color: str | None


@dataclass(frozen=True)
class OneSignalConfig:
    app_id: str | None
    rest_api_key: str | None


@dataclass(frozen=True)
class OAuthConfig:
    google_client_id: str | None
    apple_client_id: str | None


@dataclass(frozen=True)
class Config:
    env: str
    port: int
    base_url: str
    database_url: str
    database_name: str | None
    bcrypt_salt_rounds: int
    auth_level: AuthLevel
    jwt: JwtConfig
    smtp: SmtpConfig
    cloudinary: CloudinaryConfig
    stripe: StripeConfig
    super_admin: SuperAdminConfig
    variables: Variables
    onesignal: OneSignalConfig
    oauth: OAuthConfig


# Shape kept identical to the TypeScript config so consumers are unaffected
config = Config(
    env=env.NODE_ENV,
    port=env.PORT,
    base_url=env.BASE_URL,
    database_url=env.MONGO_URL,
    database_name=env.DB_NAME,
    bcrypt_salt_rounds=env.BCRYPT_SALT_ROUNDS,
    auth_level=AuthLevel(),
    jwt=JwtConfig(
        secret=env.JWT_SECRET,
        refresh_secret=env.JWT_REFRESH_SECRET,
        expires_in=env.JWT_EXPIRES_IN,
        refresh_expires_in=env.JWT_REFRESH_EXPIRES_IN,
    ),
    smtp=SmtpConfig(
        smtp_host=env.SMTP_HOST,
        smtp_port=env.SMTP_PORT,
        smtp_service=env.SMTP_SERVICE,
        smtp_mail=env.SMTP_MAIL,
        smtp_password=env.SMTP_PASSWORD,
        NAME=env.SERVICE_NAME,
    ),
    cloudinary=CloudinaryConfig(
        cloud_name=env.CLOUD_NAME,
        api_key=env.API_KEY,
        api_secret=env.API_SECRET,
        cloudinary_url=env.CLOUDINARY_URL,
    ),
    stripe=StripeConfig(stripe_secret_key=env.STRIPE_SECRET_KEY),
    super_admin=SuperAdminConfig(
        email=env.SUPER_ADMIN_EMAIL, password=env.SUPER_ADMIN_PASSWORD
    ),
    variables=Variables(
        email_temp_image=env.EMAIL_TEMP_IMAGE,
        email_temp_text_secondary_color=env.EMAIL_TEMP_TEXT_SECONDARY_COLOR,
    ),
    onesignal=OneSignalConfig(
        app_id=env.ONESIGNAL_APP_ID,
        rest_api_key=env.ONESIGNAL_REST_API_KEY,
    ),
    oauth=OAuthConfig(
        google_client_id=env.GOOGLE_CLIENT_ID,
        apple_client_id=env.APPLE_CLIENT_ID,
    ),
)
