
from pydantic import BaseModel, Field


class RevenueCatEvent(BaseModel):
    id: str
    event_timestamp_ms: int | None = None
    app_user_id: str
    original_app_user_id: str | None = None
    aliases: list[str] = Field(default_factory=list)
    type: str  # e.g., INITIAL_PURCHASE, RENEWAL, CANCELLATION, EXPIRATION, BILLING_ISSUE
    product_id: str | None = None
    entitlement_ids: list[str] | None = None
    period_type: str | None = None
    purchased_at_ms: int | None = None
    expiration_at_ms: int | None = None
    store: str | None = None
    environment: str = "SANDBOX"
    cancel_reason: str | None = None
    auto_resume_at_ms: int | None = None


class RevenueCatWebhookPayload(BaseModel):
    api_version: str | None = None
    event: RevenueCatEvent


class CheckEntitlementQuery(BaseModel):
    entitlement: str = Field(default="pro", min_length=1)
