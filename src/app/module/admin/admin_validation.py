from typing import Literal

from pydantic import BaseModel, Field


class ManageUserStatusPayload(BaseModel):
    action: Literal["BAN", "UNBAN", "SUSPEND", "UNAPPROVE", "ACTIVE"] = Field(
        ...,
        description="Target administrative action to perform on user account",
    )
    reason: str | None = Field(
        default=None,
        description="User-facing reason explaining the account status update",
    )
    internal_note: str | None = Field(
        default=None,
        description="Internal administrative note for audit tracking",
    )
    duration_hours: int | None = Field(
        default=None,
        ge=1,
        le=8760,
        description="Suspension duration in hours (only applicable for SUSPEND action)",
    )
    revoke_sessions: bool = Field(
        default=True,
        description="Whether to immediately invalidate active JWTs and refresh tokens",
    )
    notify_user: bool = Field(
        default=True,
        description="Whether to dispatch a transactional status update email to the user",
    )


class AdminValidation:
    manage_user_status = ManageUserStatusPayload
