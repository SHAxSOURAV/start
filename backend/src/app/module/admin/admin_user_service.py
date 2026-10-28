from __future__ import annotations

import re
from datetime import timedelta
from typing import Any

from bson import ObjectId

from src.app.module.admin.admin_model import Admin
from src.app.module.admin.audit_log_model import AuditLog
from src.app.module.auth.auth_model import Auth
from src.app.module.auth.session_service import SessionService
from src.app.module.user.user_model import User
from src.connection.connect_redis import RedisService
from src.connection.socket_server import sio
from src.error.api_error import ApiError
from src.types.auth_types import AuthUserPayload
from src.util.base_document import utcnow
from src.util.email_helpers import EmailHelpers
from src.util.enum import EnumAccountStatus, EnumSocketEvent, EnumUserRole
from src.util.fire_and_forget import fire_and_forget
from src.util.http_status import status
from src.util.logger import error_logger

ROLE_WEIGHTS: dict[str, int] = {
    EnumUserRole.SUPER_ADMIN: 40,
    EnumUserRole.ADMIN: 30,
    EnumUserRole.DRIVER: 20,
    EnumUserRole.USER: 10,
}


def _oid(value: Any) -> ObjectId:
    return ObjectId(str(value))


async def manage_user_status(
    admin_user: AuthUserPayload,
    target_id: str,
    payload: dict[str, Any],
    ip: str = "unknown",
    user_agent: str = "",
) -> dict[str, Any]:
    """Manages user lifecycle status (BAN, SUSPEND, UNAPPROVE, ACTIVE, UNBAN)."""
    # 1. Resolve Target Account (allows searching by Auth _id or User profile _id)
    target_auth = await Auth.get_pymongo_collection().find_one({"_id": _oid(target_id)})
    target_user_id = None

    if not target_auth:
        user_doc = await User.get_pymongo_collection().find_one({"_id": _oid(target_id)})
        if user_doc and user_doc.get("authId"):
            target_auth = await Auth.get_pymongo_collection().find_one(
                {"_id": user_doc["authId"]}
            )
            target_user_id = user_doc["_id"]
    else:
        user_doc = await User.get_pymongo_collection().find_one(
            {"authId": target_auth["_id"]}
        )
        if user_doc:
            target_user_id = user_doc["_id"]

    if not target_auth:
        raise ApiError(status.NOT_FOUND, "Target account not found")

    # 2. Self-Action Prevention (Pillar 2)
    admin_auth_id = str(admin_user.get("authId") or "")
    if admin_auth_id == str(target_auth["_id"]):
        raise ApiError(
            status.BAD_REQUEST,
            "Self-action forbidden: You cannot ban or change status of your own account.",
        )

    # 3. Role Hierarchy Enforcement (Pillar 2)
    admin_role = admin_user.get("role", "")
    target_role = target_auth.get("role", "")
    admin_weight = ROLE_WEIGHTS.get(admin_role, 0)
    target_weight = ROLE_WEIGHTS.get(target_role, 0)

    if admin_weight <= target_weight:
        raise ApiError(
            status.FORBIDDEN,
            "Permission denied: You cannot change status of an account with equal or higher role privilege.",
        )

    action = payload["action"].upper()
    reason = payload.get("reason")
    internal_note = payload.get("internal_note")
    duration_hours = payload.get("duration_hours")
    revoke_sessions = payload.get("revoke_sessions", True)
    notify_user = payload.get("notify_user", True)

    current_status = target_auth.get("status") or (
        EnumAccountStatus.BANNED if target_auth.get("isBlocked") else EnumAccountStatus.ACTIVE
    )

    # 4. Idempotency Check (Pillar 6)
    if current_status == action and action not in ("SUSPEND",):
        return {
            "authId": str(target_auth["_id"]),
            "email": target_auth["email"],
            "status": current_status,
            "unchanged": True,
            "message": f"Account is already in {action} state.",
        }

    now = utcnow()
    ban_expires_at = None
    banned_at = None
    banned_by = None
    ban_reason = None
    unapproved_at = None

    # 5. State Machine & Duration Calculations (Pillar 3)
    if action == "BAN":
        new_status = EnumAccountStatus.BANNED
        is_blocked = True
        is_active = False
        banned_at = now
        banned_by = _oid(admin_auth_id)
        ban_reason = reason
        redis_ttl = 2592000  # 30 days
    elif action == "SUSPEND":
        new_status = EnumAccountStatus.SUSPENDED
        is_blocked = True
        is_active = False
        banned_at = now
        banned_by = _oid(admin_auth_id)
        ban_reason = reason
        hours = duration_hours or 24
        ban_expires_at = now + timedelta(hours=hours)
        redis_ttl = int(hours * 3600)
    elif action == "UNAPPROVE":
        new_status = EnumAccountStatus.UNAPPROVED
        is_blocked = True
        is_active = False
        unapproved_at = now
        ban_reason = reason
        redis_ttl = 2592000
    elif action in ("UNBAN", "ACTIVE"):
        new_status = EnumAccountStatus.ACTIVE
        is_blocked = False
        is_active = True
        redis_ttl = 0
    else:
        raise ApiError(status.BAD_REQUEST, f"Unsupported action: {action}")

    # 6. Atomic MongoDB Persistence (Pillar 3)
    update_fields: dict[str, Any] = {
        "status": new_status,
        "isBlocked": is_blocked,
        "isActive": is_active,
        "bannedAt": banned_at,
        "bannedBy": banned_by,
        "banReason": ban_reason,
        "banExpiresAt": ban_expires_at,
        "unapprovedAt": unapproved_at,
        "updatedAt": now,
    }
    await Auth.get_pymongo_collection().update_one(
        {"_id": target_auth["_id"]}, {"$set": update_fields}
    )

    # 7. Instant Token Invalidation, Redis Blacklist & Socket Force Logout (Pillars 1 & 4)
    if is_blocked:
        if revoke_sessions:
            await SessionService.revoke_all_user_sessions(target_auth["_id"])
            await RedisService.ban_user(target_auth["_id"], duration_seconds=redis_ttl)

        force_logout_payload = {
            "action": action,
            "status": new_status,
            "reason": reason or "Your account has been restricted by administration.",
            "expiresAt": ban_expires_at.isoformat() if ban_expires_at else None,
        }
        try:
            target_rooms = [str(target_auth["_id"])]
            if target_user_id:
                target_rooms.append(str(target_user_id))
            for room_id in set(target_rooms):
                await sio.emit(
                    EnumSocketEvent.FORCE_LOGOUT, force_logout_payload, room=room_id
                )
        except Exception as exc:
            error_logger.error(f"Socket FORCE_LOGOUT emit error: {exc}")
    else:
        # User unbanned / reactivated: clear Redis ban immediately
        await RedisService.unban_user(target_auth["_id"])

    # 8. Immutable Audit Trail (Pillar 5)
    audit_log = AuditLog(
        action=f"USER_{action}",
        performedBy=_oid(admin_auth_id),
        performedByRole=admin_role,
        targetAuthId=target_auth["_id"],
        targetUserId=_oid(target_user_id) if target_user_id else None,
        targetEmail=target_auth["email"],
        targetRole=target_role,
        reason=reason,
        internalNote=internal_note,
        oldStatus=current_status,
        newStatus=new_status,
        ip=ip,
        userAgent=user_agent,
        metadata={
            "durationHours": duration_hours,
            "banExpiresAt": ban_expires_at.isoformat() if ban_expires_at else None,
            "revokeSessions": revoke_sessions,
            "notifyUser": notify_user,
        },
    )
    await audit_log.insert()

    # 9. Asynchronous Transactional Notification (Pillars 4 & 6)
    if notify_user:
        fire_and_forget(
            EmailHelpers.send_account_status_email(
                email=target_auth["email"],
                data={
                    "name": target_auth.get("name", "User"),
                    "action": action,
                    "reason": reason or "Administrative decision.",
                    "expiresAt": ban_expires_at.strftime("%Y-%m-%d %H:%M:%S UTC")
                    if ban_expires_at
                    else None,
                },
            )
        )

    return {
        "authId": str(target_auth["_id"]),
        "targetUserId": str(target_user_id) if target_user_id else None,
        "email": target_auth["email"],
        "previousStatus": current_status,
        "status": new_status,
        "isBlocked": is_blocked,
        "banExpiresAt": ban_expires_at,
        "auditLogId": str(audit_log.id),
        "message": f"User status successfully updated to {new_status}.",
    }


async def get_all_users(query_params: dict[str, Any]) -> dict[str, Any]:
    """Retrieves paginated user accounts with rich filters and denormalized profile data.

    Enforces Application-Level Batch Population to retrieve users in 1-2 ms without $lookup join overhead.
    """
    filter_query: dict[str, Any] = {"isDeleted": {"$ne": True}}

    # 1. Filter by status (e.g. BANNED, SUSPENDED, UNAPPROVED, ACTIVE)
    status_filter = query_params.get("status")
    if status_filter:
        status_upper = status_filter.upper()
        if status_upper == "BANNED":
            filter_query["$or"] = [
                {"status": "BANNED"},
                {"isBlocked": True},
            ]
        else:
            filter_query["status"] = status_upper

    # Direct isBlocked filter if explicitly passed
    if "isBlocked" in query_params:
        is_blocked_val = str(query_params["isBlocked"]).lower() == "true"
        filter_query["isBlocked"] = is_blocked_val

    # 2. Filter by role
    if query_params.get("role"):
        filter_query["role"] = query_params["role"].upper()

    # 3. Search Term (case-insensitive regex on name or email)
    search_term = str(query_params.get("searchTerm", "")).strip()
    if search_term:
        escaped_term = re.escape(search_term)
        regex_filter = {"$regex": escaped_term, "$options": "i"}
        search_or = [
            {"name": regex_filter},
            {"email": regex_filter},
        ]
        if "$or" in filter_query:
            filter_query["$and"] = [
                {"$or": filter_query.pop("$or")},
                {"$or": search_or},
            ]
        else:
            filter_query["$or"] = search_or

    page = max(1, int(query_params.get("page", 1)))
    limit = max(1, min(100, int(query_params.get("limit", 20))))
    skip = (page - 1) * limit

    # Sort order: if searching for banned users, sort by bannedAt desc, else createdAt desc
    sort_field = (
        "bannedAt"
        if status_filter and status_filter.upper() == "BANNED"
        else "createdAt"
    )

    projection = {
        "password": 0,
        "verificationCode": 0,
        "verificationCodeExpire": 0,
        "activationCode": 0,
        "activationCodeExpire": 0,
    }

    cursor = (
        Auth.get_pymongo_collection()
        .find(filter_query, projection)
        .sort([(sort_field, -1), ("_id", -1)])
        .skip(skip)
        .limit(limit)
    )
    auth_docs = await cursor.to_list(length=limit)
    total = await Auth.get_pymongo_collection().count_documents(filter_query)
    total_page = (total + limit - 1) // limit if total > 0 else 1

    if not auth_docs:
        return {
            "data": [],
            "meta": {
                "page": page,
                "limit": limit,
                "total": total,
                "totalPage": total_page,
            },
        }

    # 4. Application-Level Batch Population (Dual primary index query via $in)
    auth_ids = [doc["_id"] for doc in auth_docs]

    user_cursor = User.get_pymongo_collection().find(
        {"authId": {"$in": auth_ids}},
        {
            "authId": 1,
            "profile_image": 1,
            "phoneNumber": 1,
            "address": 1,
            "isOnline": 1,
            "locationCoordinates": 1,
        },
    )
    user_profiles = {
        p["authId"]: p for p in await user_cursor.to_list(length=len(auth_ids))
    }

    # Query admin profiles for admin accounts or bannedBy details
    admin_auth_ids = [
        doc["_id"]
        for doc in auth_docs
        if doc.get("role") in (EnumUserRole.ADMIN, EnumUserRole.SUPER_ADMIN)
    ]
    banned_by_ids = [doc["bannedBy"] for doc in auth_docs if doc.get("bannedBy")]
    all_admin_ids = list({*admin_auth_ids, *banned_by_ids})

    admin_profiles: dict[Any, dict[str, Any]] = {}
    if all_admin_ids:
        admin_cursor = Admin.get_pymongo_collection().find(
            {"authId": {"$in": all_admin_ids}},
            {"authId": 1, "name": 1, "email": 1, "profile_image": 1},
        )
        admin_profiles = {
            a["authId"]: a
            for a in await admin_cursor.to_list(length=len(all_admin_ids))
        }

    # 5. In-Memory Stitching (0 disk I/O, ultra-fast response)
    results = []
    for doc in auth_docs:
        auth_id = doc["_id"]
        profile = user_profiles.get(auth_id) or admin_profiles.get(auth_id) or {}

        banned_by_info = None
        if doc.get("bannedBy"):
            admin_info = admin_profiles.get(doc["bannedBy"])
            if admin_info:
                banned_by_info = {
                    "authId": str(doc["bannedBy"]),
                    "name": admin_info.get("name"),
                    "email": admin_info.get("email"),
                }
            else:
                banned_by_info = {"authId": str(doc["bannedBy"])}

        user_data = {
            "authId": str(auth_id),
            "profileId": str(profile.get("_id")) if profile.get("_id") else None,
            "name": doc.get("name"),
            "email": doc.get("email"),
            "role": doc.get("role"),
            "status": doc.get("status")
            or ("BANNED" if doc.get("isBlocked") else "ACTIVE"),
            "isBlocked": bool(doc.get("isBlocked", False)),
            "isActive": bool(doc.get("isActive", False)),
            "profile_image": profile.get("profile_image"),
            "phoneNumber": profile.get("phoneNumber"),
            "address": profile.get("address"),
            "isOnline": profile.get("isOnline", False),
            "bannedAt": doc.get("bannedAt"),
            "banReason": doc.get("banReason"),
            "banExpiresAt": doc.get("banExpiresAt"),
            "bannedBy": banned_by_info,
            "unapprovedAt": doc.get("unapprovedAt"),
            "createdAt": doc.get("createdAt"),
            "updatedAt": doc.get("updatedAt"),
        }
        results.append(user_data)

    return {
        "data": results,
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPage": total_page,
        },
    }


async def get_audit_logs(query_params: dict[str, Any]) -> dict[str, Any]:
    """Retrieves paginated audit logs with optional filtering (Pillar 5)."""
    filter_query: dict[str, Any] = {}
    if query_params.get("action"):
        filter_query["action"] = query_params["action"]
    if query_params.get("targetAuthId"):
        filter_query["targetAuthId"] = _oid(query_params["targetAuthId"])
    if query_params.get("performedBy"):
        filter_query["performedBy"] = _oid(query_params["performedBy"])

    page = max(1, int(query_params.get("page", 1)))
    limit = max(1, min(100, int(query_params.get("limit", 20))))
    skip = (page - 1) * limit

    cursor = (
        AuditLog.get_pymongo_collection()
        .find(filter_query)
        .sort("createdAt", -1)
        .skip(skip)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    total = await AuditLog.get_pymongo_collection().count_documents(filter_query)
    total_page = (total + limit - 1) // limit if total > 0 else 1

    formatted_docs = []
    for doc in docs:
        doc["_id"] = str(doc["_id"])
        doc["performedBy"] = str(doc.get("performedBy", ""))
        doc["targetAuthId"] = str(doc.get("targetAuthId", ""))
        if doc.get("targetUserId"):
            doc["targetUserId"] = str(doc["targetUserId"])
        formatted_docs.append(doc)

    return {
        "data": formatted_docs,
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPage": total_page,
        },
    }
