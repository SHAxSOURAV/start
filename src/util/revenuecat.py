"""RevenueCat REST API v2 Helper Client.

Provides non-blocking outbound HTTP requests to RevenueCat API v2
for verifying subscriber entitlements and customer profiles.
Gracefully disabled when REVENUECAT_ENABLED is False.
"""

from typing import Any

import httpx

from src.config import config
from src.util.logger import logger

REVENUECAT_BASE_URL = "https://api.revenuecat.com/v2"


def is_revenuecat_enabled() -> bool:
    """Returns True if RevenueCat is enabled and configured."""
    return bool(config.revenuecat.enabled and config.revenuecat.api_key)


async def get_customer_active_entitlements(
    customer_id: str,
) -> list[str]:
    """Fetch a customer's active entitlements from RevenueCat API v2.

    Returns an empty list if RevenueCat is disabled or customer has no entitlements.
    """
    if not is_revenuecat_enabled():
        return []

    project_id = config.revenuecat.project_id
    api_key = config.revenuecat.api_key

    if not project_id or not api_key:
        logger.warning(
            "RevenueCat active: REVENUECAT_PROJECT_ID or REVENUECAT_API_KEY is missing."
        )
        return []

    url = (
        f"{REVENUECAT_BASE_URL}/projects/{project_id}/customers/{customer_id}/active_entitlements"
    )
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                return [
                    item.get("entitlement_id")
                    for item in items
                    if item.get("entitlement_id")
                ]
            else:
                logger.warning(
                    f"RevenueCat active_entitlements returned {response.status_code}: {response.text}"
                )
                return []
    except Exception as exc:
        logger.error(f"Error calling RevenueCat API: {exc}")
        return []


async def get_customer_profile(customer_id: str) -> dict[str, Any] | None:
    """Fetch complete customer profile from RevenueCat API v2."""
    if not is_revenuecat_enabled():
        return None

    project_id = config.revenuecat.project_id
    api_key = config.revenuecat.api_key

    if not project_id or not api_key:
        return None

    url = f"{REVENUECAT_BASE_URL}/projects/{project_id}/customers/{customer_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            return None
    except Exception as exc:
        logger.error(f"Error fetching RevenueCat customer profile: {exc}")
        return None
