"""Single source of truth for environment variables.

Keep .env.example in sync with this schema -- the app refuses to boot on a
mismatch.
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

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
    REDIS_URL: str = "redis://localhost:6379/0"

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
    STRIPE_PUBLISHABLE_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None
    STRIPE_CURRENCY: str = "usd"
    STRIPE_SUCCESS_URL: str | None = None
    STRIPE_CANCEL_URL: str | None = None

    CLOUD_NAME: str | None = Field(
        default=None,
        validation_alias=AliasChoices("CLOUDINARY_CLOUD_NAME", "CLOUD_NAME"),
    )
    API_KEY: str | None = Field(
        default=None,
        validation_alias=AliasChoices("CLOUDINARY_API_KEY", "API_KEY"),
    )
    API_SECRET: str | None = Field(
        default=None,
        validation_alias=AliasChoices("CLOUDINARY_API_SECRET", "API_SECRET"),
    )
    CLOUDINARY_URL: str | None = None

    EMAIL_TEMP_IMAGE: str | None = None
    EMAIL_TEMP_TEXT_SECONDARY_COLOR: str | None = None

    ONESIGNAL_APP_ID: str | None = None
    ONESIGNAL_REST_API_KEY: str | None = None
    NOTIFICATION_RETENTION_DAYS: int = 30

    GOOGLE_CLIENT_ID: str | None = None
    APPLE_CLIENT_ID: str | None = None

    REVENUECAT_ENABLED: bool = False
    REVENUECAT_API_KEY: str | None = None
    REVENUECAT_PROJECT_ID: str | None = None
    REVENUECAT_WEBHOOK_SECRET: str | None = None

    SENTRY_DSN: str | None = None

    STORAGE_PROVIDER: Literal["s3", "cloudinary", "local"] = "s3"

    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str = "eu-north-1"
    AWS_S3_BUCKET_NAME: str | None = None

    S3_RETENTION_TEMP_DAYS: int = 2
    S3_RETENTION_CHAT_DAYS: int = 180
    S3_RETENTION_DOCUMENT_DAYS: int = 365



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
    publishable_key: str | None
    webhook_secret: str | None
    currency: str
    success_url: str | None
    cancel_url: str | None


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
class RedisConfig:
    url: str


@dataclass(frozen=True)
class NotificationConfig:
    retention_days: int
    retention_seconds: int


@dataclass(frozen=True)
class RevenueCatConfig:
    enabled: bool
    api_key: str | None
    project_id: str | None
    webhook_secret: str | None


@dataclass(frozen=True)
class S3RetentionConfig:
    temp_days: int
    chat_days: int
    document_days: int


@dataclass(frozen=True)
class AwsS3Config:
    access_key_id: str | None
    secret_access_key: str | None
    region: str
    bucket_name: str | None
    retention: S3RetentionConfig


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
    redis: RedisConfig
    smtp: SmtpConfig
    cloudinary: CloudinaryConfig
    stripe: StripeConfig
    super_admin: SuperAdminConfig
    variables: Variables
    onesignal: OneSignalConfig
    notification: NotificationConfig
    revenuecat: RevenueCatConfig
    oauth: OAuthConfig
    storage_provider: Literal["s3", "cloudinary", "local"]
    s3: AwsS3Config
    sentry_dsn: str | None = None


# Parse CLOUDINARY_URL if individual credentials are not provided
_c_name: str | None = env.CLOUD_NAME
_c_key: str | None = env.API_KEY
_c_secret: str | None = env.API_SECRET
if env.CLOUDINARY_URL and env.CLOUDINARY_URL.startswith("cloudinary://"):
    try:
        _parsed = urlsplit(env.CLOUDINARY_URL)
        _c_key = _c_key or _parsed.username
        _c_secret = _c_secret or _parsed.password
        _c_name = _c_name or _parsed.hostname
    except Exception:
        pass

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
    redis=RedisConfig(url=env.REDIS_URL),
    smtp=SmtpConfig(
        smtp_host=env.SMTP_HOST,
        smtp_port=env.SMTP_PORT,
        smtp_service=env.SMTP_SERVICE,
        smtp_mail=env.SMTP_MAIL,
        smtp_password=env.SMTP_PASSWORD,
        NAME=env.SERVICE_NAME,
    ),
    cloudinary=CloudinaryConfig(
        cloud_name=_c_name,
        api_key=_c_key,
        api_secret=_c_secret,
        cloudinary_url=env.CLOUDINARY_URL,
    ),
    stripe=StripeConfig(
        stripe_secret_key=env.STRIPE_SECRET_KEY,
        publishable_key=env.STRIPE_PUBLISHABLE_KEY,
        webhook_secret=env.STRIPE_WEBHOOK_SECRET,
        currency=env.STRIPE_CURRENCY.lower(),
        success_url=env.STRIPE_SUCCESS_URL,
        cancel_url=env.STRIPE_CANCEL_URL,
    ),
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
    notification=NotificationConfig(
        retention_days=env.NOTIFICATION_RETENTION_DAYS,
        retention_seconds=env.NOTIFICATION_RETENTION_DAYS * 24 * 60 * 60,
    ),
    revenuecat=RevenueCatConfig(
        enabled=env.REVENUECAT_ENABLED,
        api_key=env.REVENUECAT_API_KEY,
        project_id=env.REVENUECAT_PROJECT_ID,
        webhook_secret=env.REVENUECAT_WEBHOOK_SECRET,
    ),
    oauth=OAuthConfig(
        google_client_id=env.GOOGLE_CLIENT_ID,
        apple_client_id=env.APPLE_CLIENT_ID,
    ),
    storage_provider=env.STORAGE_PROVIDER,
    s3=AwsS3Config(
        access_key_id=env.AWS_ACCESS_KEY_ID,
        secret_access_key=env.AWS_SECRET_ACCESS_KEY,
        region=env.AWS_REGION,
        bucket_name=env.AWS_S3_BUCKET_NAME,
        retention=S3RetentionConfig(
            temp_days=env.S3_RETENTION_TEMP_DAYS,
            chat_days=env.S3_RETENTION_CHAT_DAYS,
            document_days=env.S3_RETENTION_DOCUMENT_DAYS,
        ),
    ),
    sentry_dsn=env.SENTRY_DSN,
)
