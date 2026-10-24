from datetime import UTC, datetime
from typing import Literal

from src.app.module.auth.auth_model import Auth
from src.util.logger import logger

# Belt-and-braces cleanup: expiry is enforced inside the auth services,
# this job just removes stale code fields from the collection.


async def cleanup_expired_otp_fields(
    check: Literal["activation", "verification"],
) -> None:
    now = datetime.now(UTC)
    result = None

    if check == "activation":
        result = await Auth.get_pymongo_collection().update_many(
            {"activationCodeExpire": {"$lte": now}},
            {
                "$unset": {
                    "activationCode": "",
                    "activationCodeExpire": "",
                    "activationAttempts": "",
                }
            },
        )

    if check == "verification":
        result = await Auth.get_pymongo_collection().update_many(
            {"verificationCodeExpire": {"$lte": now}},
            {
                "$unset": {
                    "isVerified": "",
                    "verificationCode": "",
                    "verificationCodeExpire": "",
                    "verificationAttempts": "",
                }
            },
        )

    if result and result.modified_count > 0:
        logger.info(f"Removed {result.modified_count} expired {check} code")
