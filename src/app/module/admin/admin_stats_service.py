"""High-Performance Admin Statistics & Analytics Service.

Aggregates platform KPIs, growth charts, and categorical distributions across
Auth, Subscription, Chat, Feedback, Review, and Support collections.
Uses asyncio.gather for parallel sub-queries and Redis caching with TTL to guarantee
sub-millisecond dashboard response times.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

from src.app.module.auth.auth_model import Auth
from src.app.module.chat.chat_model import Chat
from src.app.module.chat.message_model import Message
from src.app.module.feedback.feedback_model import Feedback
from src.app.module.manage.manage_model import ContactUs
from src.app.module.notification.admin_notification_model import AdminNotification
from src.app.module.review.review_model import Review
from src.app.module.subscription.subscription_model import Subscription
from src.connection.connect_redis import RedisService

MONTH_NAMES = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


async def _aggregate(
    col: Any, pipeline: Any, length: int | None = None
) -> list[dict[str, Any]]:
    """Helper to run PyMongo aggregation and consume async cursor."""
    cursor = await col.aggregate(pipeline)
    res = await cursor.to_list(length=length)
    return list(res)


async def get_overview_statistics(refresh: bool = False) -> dict[str, Any]:
    """Returns top-level KPI overview for Admin Dashboard.

    Cached in Redis under `admin:stats:overview` for 60 seconds unless refresh=True.
    """
    cache_key = "admin:stats:overview"
    if not refresh:
        cached = await RedisService.get_json(cache_key)
        if cached:
            return cached

    now = datetime.now(UTC)
    start_of_today = datetime(now.year, now.month, now.day, tzinfo=UTC)
    start_of_month = datetime(now.year, now.month, 1, tzinfo=UTC)

    auth_col = Auth.get_pymongo_collection()
    sub_col = Subscription.get_pymongo_collection()
    chat_col = Chat.get_pymongo_collection()
    msg_col = Message.get_pymongo_collection()
    fb_col = Feedback.get_pymongo_collection()
    contact_col = ContactUs.get_pymongo_collection()
    review_col = Review.get_pymongo_collection()
    admin_notif_col = AdminNotification.get_pymongo_collection()

    results: list[Any] = await asyncio.gather(
        auth_col.count_documents({"isDeleted": {"$ne": True}}),
        auth_col.count_documents({"isActive": True, "isDeleted": {"$ne": True}}),
        auth_col.count_documents({"isVerified": True, "isDeleted": {"$ne": True}}),
        auth_col.count_documents({"isBlocked": True, "isDeleted": {"$ne": True}}),
        auth_col.count_documents(
            {"createdAt": {"$gte": start_of_today}, "isDeleted": {"$ne": True}}
        ),
        auth_col.count_documents(
            {"createdAt": {"$gte": start_of_month}, "isDeleted": {"$ne": True}}
        ),
        sub_col.count_documents({}),
        sub_col.count_documents({"status": "ACTIVE"}),
        sub_col.count_documents({"status": "CANCELED"}),
        sub_col.count_documents({"status": "EXPIRED"}),
        sub_col.count_documents({"status": "BILLING_ISSUE"}),
        chat_col.count_documents({}),
        msg_col.count_documents({}),
        msg_col.count_documents({"createdAt": {"$gte": start_of_today}}),
        fb_col.count_documents({"status": "PENDING"}),
        fb_col.count_documents({"status": "RESOLVED"}),
        fb_col.count_documents({}),
        contact_col.count_documents({"isReplied": False}),
        contact_col.count_documents({}),
        _aggregate(
            review_col,
            [
                {
                    "$group": {
                        "_id": None,
                        "avg": {"$avg": "$rating"},
                        "count": {"$sum": 1},
                    }
                }
            ],
            length=1,
        ),
        admin_notif_col.count_documents({"isRead": False}),
    )

    (
        total_users,
        active_users,
        verified_users,
        blocked_users,
        new_users_today,
        new_users_month,
        total_subs,
        active_subs,
        canceled_subs,
        expired_subs,
        billing_issues,
        total_chats,
        total_messages,
        messages_today,
        pending_feedbacks,
        resolved_feedbacks,
        total_feedbacks,
        unreplied_inquiries,
        total_inquiries,
        review_aggregates,
        unread_admin_notifs,
    ) = results

    avg_rating = 0.0
    total_reviews = 0
    if review_aggregates:
        avg_rating = round(float(review_aggregates[0].get("avg") or 0.0), 2)
        total_reviews = int(review_aggregates[0].get("count") or 0)

    churn_rate = 0.0
    if int(total_subs) > 0:
        churn_rate = round(
            (int(canceled_subs) + int(expired_subs)) / int(total_subs) * 100, 2
        )

    data: dict[str, Any] = {
        "users": {
            "total": total_users,
            "active": active_users,
            "verified": verified_users,
            "blocked": blocked_users,
            "newToday": new_users_today,
            "newThisMonth": new_users_month,
        },
        "subscriptions": {
            "total": total_subs,
            "active": active_subs,
            "canceled": canceled_subs,
            "expired": expired_subs,
            "billingIssues": billing_issues,
            "churnRatePercent": churn_rate,
        },
        "engagement": {
            "totalChats": total_chats,
            "totalMessages": total_messages,
            "messagesToday": messages_today,
        },
        "supportAndQuality": {
            "pendingFeedbacks": pending_feedbacks,
            "resolvedFeedbacks": resolved_feedbacks,
            "totalFeedbacks": total_feedbacks,
            "unrepliedInquiries": unreplied_inquiries,
            "totalInquiries": total_inquiries,
            "averageRating": avg_rating,
            "totalReviews": total_reviews,
        },
        "unreadAdminNotifications": unread_admin_notifs,
        "generatedAt": now.isoformat(),
    }

    await RedisService.set_json(cache_key, data, ttl_seconds=60)
    return data


async def get_charts_statistics(
    year: int | None = None, refresh: bool = False
) -> dict[str, Any]:
    """Returns monthly timeline metrics for registration and subscriptions.

    Used by frontend line/bar charts for growth analytics.
    """
    now = datetime.now(UTC)
    target_year = year or now.year
    cache_key = f"admin:stats:charts:{target_year}"

    if not refresh:
        cached = await RedisService.get_json(cache_key)
        if cached:
            return cached

    start_of_year = datetime(target_year, 1, 1, tzinfo=UTC)
    end_of_year = datetime(target_year, 12, 31, 23, 59, 59, tzinfo=UTC)
    seven_days_ago = now - timedelta(days=7)

    auth_col = Auth.get_pymongo_collection()
    sub_col = Subscription.get_pymongo_collection()
    msg_col = Message.get_pymongo_collection()

    user_pipeline = [
        {
            "$match": {
                "createdAt": {"$gte": start_of_year, "$lte": end_of_year},
                "isDeleted": {"$ne": True},
            }
        },
        {"$group": {"_id": {"$month": "$createdAt"}, "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]

    sub_pipeline = [
        {"$match": {"createdAt": {"$gte": start_of_year, "$lte": end_of_year}}},
        {"$group": {"_id": {"$month": "$createdAt"}, "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]

    msg_pipeline = [
        {"$match": {"createdAt": {"$gte": seven_days_ago}}},
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$createdAt"}},
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]

    chart_results: list[Any] = await asyncio.gather(
        _aggregate(auth_col, user_pipeline, length=12),
        _aggregate(sub_col, sub_pipeline, length=12),
        _aggregate(msg_col, msg_pipeline, length=7),
    )
    user_months_raw: list[dict[str, Any]] = chart_results[0]
    sub_months_raw: list[dict[str, Any]] = chart_results[1]
    msg_trend_raw: list[dict[str, Any]] = chart_results[2]

    user_map = {item["_id"]: item["count"] for item in user_months_raw}
    sub_map = {item["_id"]: item["count"] for item in sub_months_raw}

    monthly_growth: list[dict[str, Any]] = []
    for month_num in range(1, 13):
        monthly_growth.append(
            {
                "month": MONTH_NAMES[month_num - 1],
                "monthNumber": month_num,
                "users": user_map.get(month_num, 0),
                "subscriptions": sub_map.get(month_num, 0),
            }
        )

    recent_message_trend = [
        {"date": item["_id"], "count": item["count"]} for item in msg_trend_raw
    ]

    data: dict[str, Any] = {
        "year": target_year,
        "monthlyGrowth": monthly_growth,
        "recentMessageTrend": recent_message_trend,
        "generatedAt": now.isoformat(),
    }

    await RedisService.set_json(cache_key, data, ttl_seconds=60)
    return data


async def get_breakdowns_statistics(refresh: bool = False) -> dict[str, Any]:
    """Returns categorical distributions for pie/donut charts.

    Includes role distribution, OAuth providers, subscription stores,
    and star rating distribution.
    """
    cache_key = "admin:stats:breakdowns"
    if not refresh:
        cached = await RedisService.get_json(cache_key)
        if cached:
            return cached

    auth_col = Auth.get_pymongo_collection()
    sub_col = Subscription.get_pymongo_collection()
    review_col = Review.get_pymongo_collection()
    fb_col = Feedback.get_pymongo_collection()

    role_pipeline = [
        {"$match": {"isDeleted": {"$ne": True}}},
        {"$group": {"_id": "$role", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]

    store_pipeline = [
        {"$group": {"_id": "$store", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]

    rating_pipeline = [
        {"$group": {"_id": "$rating", "count": {"$sum": 1}}},
        {"$sort": {"_id": -1}},
    ]

    fb_status_pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]

    breakdown_results: list[Any] = await asyncio.gather(
        _aggregate(auth_col, role_pipeline, length=10),
        auth_col.count_documents(
            {"googleId": {"$ne": None}, "isDeleted": {"$ne": True}}
        ),
        auth_col.count_documents(
            {"appleId": {"$ne": None}, "isDeleted": {"$ne": True}}
        ),
        auth_col.count_documents(
            {"googleId": None, "appleId": None, "isDeleted": {"$ne": True}}
        ),
        _aggregate(sub_col, store_pipeline, length=10),
        _aggregate(review_col, rating_pipeline, length=5),
        _aggregate(fb_col, fb_status_pipeline, length=5),
    )

    roles_raw: list[dict[str, Any]] = breakdown_results[0]
    google_users: int = breakdown_results[1]
    apple_users: int = breakdown_results[2]
    password_users: int = breakdown_results[3]
    stores_raw: list[dict[str, Any]] = breakdown_results[4]
    ratings_raw: list[dict[str, Any]] = breakdown_results[5]
    fb_status_raw: list[dict[str, Any]] = breakdown_results[6]

    users_by_role = [
        {"role": item["_id"] or "UNKNOWN", "count": item["count"]} for item in roles_raw
    ]

    users_by_auth_provider = [
        {"provider": "EMAIL_PASSWORD", "count": password_users},
        {"provider": "GOOGLE", "count": google_users},
        {"provider": "APPLE", "count": apple_users},
    ]

    subs_by_store = [
        {"store": item["_id"] or "UNKNOWN", "count": item["count"]}
        for item in stores_raw
    ]

    rating_distribution = [
        {"stars": item["_id"], "count": item["count"]} for item in ratings_raw
    ]

    feedback_by_status = [
        {"status": item["_id"] or "UNKNOWN", "count": item["count"]}
        for item in fb_status_raw
    ]

    data: dict[str, Any] = {
        "usersByRole": users_by_role,
        "usersByAuthProvider": users_by_auth_provider,
        "subscriptionsByStore": subs_by_store,
        "ratingsDistribution": rating_distribution,
        "feedbacksByStatus": feedback_by_status,
        "generatedAt": datetime.now(UTC).isoformat(),
    }

    await RedisService.set_json(cache_key, data, ttl_seconds=60)
    return data
