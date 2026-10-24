from typing import Any

from pydantic import BaseModel, Field


class CreateCheckoutSessionSchema(BaseModel):
    amount: float = Field(..., gt=0, description="Amount in currency units (e.g. 29.99)")
    currency: str = Field(default="usd", min_length=3, max_length=3)
    productName: str = Field(..., min_length=1, description="Item or subscription display title")
    description: str | None = None
    successUrl: str | None = None
    cancelUrl: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CreatePaymentIntentSchema(BaseModel):
    amount: float = Field(..., gt=0, description="Amount in currency units (e.g. 29.99)")
    currency: str = Field(default="usd", min_length=3, max_length=3)
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
