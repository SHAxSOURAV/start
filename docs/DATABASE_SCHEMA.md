# Database Schema Catalog (`docs/DATABASE_SCHEMA.md`)

This document is the **official, authoritative reference** for all MongoDB database collections, document models, fields, data types, indexes, and relationships in the application.

> [!IMPORTANT]
> **Mandatory Agent Rule**: Whenever adding, modifying, or removing any collection, field, data type, or index in the backend codebase, the agent or engineer **MUST** immediately update this document to keep the schema catalog 100% in sync with the source code.

---

## 1. Global Document Conventions

All models (except embedded sub-documents) inherit from `TimestampedDocument` ([src/util/base_document.py](file:///c:/Users/Sourav/Documents/Start/src/util/base_document.py)), which automatically manages MongoDB `_id` and UTC timestamps:

| Field | BSON Type | Python Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `_id` | `ObjectId` | `PydanticObjectId` | Auto (`ObjectId()`) | Primary Key unique identifier |
| `createdAt` | `Date` | `datetime` | `utcnow()` | UTC document creation timestamp |
| `updatedAt` | `Date` | `datetime` | `utcnow()` | UTC timestamp updated on every save/mutation |

---

## 2. Collections & Document Models

```mermaid
erDiagram
    AUTHS ||--o| USERS : "authId (1:1)"
    AUTHS ||--o| ADMINS : "authId (1:1)"
    AUTHS ||--o{ SESSIONS : "authId (1:N)"
    CHATS ||--|{ MESSAGES : "chatId (1:N)"
    USERS ||--o{ REVIEWS : "user (1:N)"
    USERS ||--o{ FEEDBACKS : "user (1:N)"
    USERS ||--o{ NOTIFICATIONS : "toId (1:N)"
```

---

### 2.1 `auths` (Auth Model)
- **Source**: [src/app/module/auth/auth_model.py](file:///c:/Users/Sourav/Documents/Start/src/app/module/auth/auth_model.py)
- **Purpose**: Stores core authentication credentials, role assignments, account statuses, activation/recovery OTPs, and OAuth identifiers.
- **Security Projection**: `password` is strictly omitted from all public responses (`AUTH_PUBLIC_PROJECTION = {"password": 0}`).

#### Fields
| Field | BSON Type | Python Type | Required | Default | Validation / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `name` | `string` | `str` | Yes | - | Full name of the account holder |
| `email` | `string` | `str` | Yes | - | Validated email regex, lowercase |
| `password` | `string` | `str` | Yes | - | Bcrypt hashed password (empty for pure OAuth accounts) |
| `role` | `string` | `str` | Yes | - | `USER`, `ADMIN`, `SUPER_ADMIN`, `DRIVER` |
| `isVerified` | `bool` | `bool \| None` | No | `None` | Email verification flag |
| `isBlocked` | `bool` | `bool \| None` | No | `False` | Administrative account ban flag |
| `isActive` | `bool` | `bool \| None` | No | `False` | Account active state |
| `isDeleted` | `bool` | `bool \| None` | No | `False` | Soft-delete flag (30-day retention) |
| `deletedAt` | `Date` | `datetime \| None`| No | `None` | Soft-deletion initiation timestamp |
| `googleId` | `string` | `str \| None` | No | `None` | Google OAuth subject identifier (`sub`) |
| `appleId` | `string` | `str \| None` | No | `None` | Apple Sign-In subject identifier (`sub`) |
| `verificationCode` | `string` | `str \| None` | No | `None` | Password reset OTP hash |
| `verificationCodeExpire` | `Date` | `datetime \| None` | No | `None` | Reset OTP expiration |
| `verificationAttempts` | `int` | `int \| None` | No | `0` | Rate limiter count for reset OTP |
| `activationCode` | `string` | `str \| None` | No | `None` | Registration activation OTP |
| `activationCodeExpire` | `Date` | `datetime \| None` | No | `None` | Activation OTP expiration |
| `activationAttempts` | `int` | `int \| None` | No | `0` | Rate limiter count for activation OTP |
| `passwordChangedAt` | `Date` | `datetime \| None` | No | `None` | Timestamp of last password change/reset (invalidates old JWT sessions) |
| `failedLoginAttempts` | `int` | `int \| None` | No | `0` | Consecutive failed password attempts counter (locks account at 5) |
| `lockUntil` | `Date` | `datetime \| None` | No | `None` | Expiration timestamp for temporary brute force account lockout |

#### Indexes
| Index Keys | Type | Options | Purpose |
| :--- | :--- | :--- | :--- |
| `[("email", 1)]` | Single field | `unique=True` | Unique login and registration lookups |
| `[("isDeleted", 1), ("deletedAt", 1)]` | Compound | Default | Superfast IXSCAN for soft-delete queries & retention cleanup |
| `[("googleId", 1)]` | Single field | `sparse=True` | OAuth Google Sign-In lookup |
| `[("appleId", 1)]` | Single field | `sparse=True` | OAuth Apple Sign-In lookup |

---

### 2.2 `sessions` (Session Model)
- **Source**: [src/app/module/auth/session_model.py](file:///c:/Users/mdsad/Documents/start/src/app/module/auth/session_model.py)
- **Purpose**: Tracks active user sessions, device identifiers, client IP, Refresh Token Rotation (RTR) hashes, and 15-second grace periods for token reuse detection.

#### Fields
| Field | BSON Type | Python Type | Required | Default | Validation / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `authId` | `ObjectId` | `PydanticObjectId` | Yes | - | Foreign Key -> `auths._id` |
| `userId` | `ObjectId` | `PydanticObjectId` | Yes | - | Foreign Key -> `users._id` (or `admins._id`) |
| `refreshTokenHash` | `string` | `str` | Yes | - | SHA-256 hash of active refresh token |
| `previousTokenHash` | `string` | `str \| None` | No | `None` | SHA-256 hash of rotated token (grace period) |
| `rotatedAt` | `Date` | `datetime \| None` | No | `None` | Timestamp when rotation occurred |
| `device` | `string` | `str` | No | `"Unknown Device"` | Human-readable client platform/browser |
| `ip` | `string` | `str` | No | `"unknown"` | Client IP address at session creation/refresh |
| `userAgent` | `string` | `str` | No | `""` | Raw HTTP User-Agent string |
| `isValid` | `bool` | `bool` | No | `True` | Session validity status (False when revoked) |
| `expiresAt` | `Date` | `datetime` | Yes | - | Refresh token TTL expiration |
| `lastActiveAt` | `Date` | `datetime` | Yes | - | Timestamp of last access or rotation |

#### Indexes
| Index Keys | Type | Options | Purpose |
| :--- | :--- | :--- | :--- |
| `[("authId", 1)]` | Single field | Default | Fast lookup of all user sessions |
| `[("refreshTokenHash", 1)]` | Single field | `unique=True` | Unique lookup for active refresh token validation |
| `[("expiresAt", 1)]` | Single field | `expireAfterSeconds=0` | MongoDB TTL index for automatic expired session cleanup |
| `[("authId", 1), ("isValid", 1)]` | Compound | Default | Fast lookup of active valid sessions during mass revocation |

---

### 2.3 `users` (User Model)
- **Source**: [src/app/module/user/user_model.py](file:///c:/Users/Sourav/Documents/Start/src/app/module/user/user_model.py)
- **Purpose**: User profile information, contact numbers, address, and live geospatial coordinates.

#### Fields
| Field | BSON Type | Python Type | Required | Default | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `authId` | `ObjectId` | `PydanticObjectId` | Yes | - | Foreign Key -> `auths._id` |
| `name` | `string` | `str` | Yes | - | User display name |
| `email` | `string` | `str` | Yes | - | User email |
| `profile_image` | `string` | `str \| None` | No | `None` | Uploaded image path or OAuth avatar URL |
| `phoneNumber` | `string` | `str \| None` | No | `None` | Contact phone number |
| `dateOfBirth` | `string` | `str \| None` | No | `None` | User date of birth string |
| `address` | `string` | `str \| None` | No | `None` | Physical residential address |
| `isOnline` | `bool` | `bool \| None` | No | `False` | Real-time Socket.IO presence status |
| `isDeleted` | `bool` | `bool \| None` | No | `False` | Synced soft-delete flag |
| `deletedAt` | `Date` | `datetime \| None`| No | `None` | Synced soft-delete timestamp |
| `locationCoordinates`| `object` | `LocationCoordinates` | No | `None` | GeoJSON `{ type: "Point", coordinates: [lng, lat] }` |

#### Indexes
| Index Keys | Type | Purpose |
| :--- | :--- | :--- |
| `[("authId", 1)]` | Single field | 1-to-1 lookup from `Auth` session |
| `[("email", 1)]` | Single field | Fast lookup and search |
| `[("isDeleted", 1), ("deletedAt", 1)]` | Compound | Cleanup job filtering |
| `[("locationCoordinates", "2dsphere")]` | Geospatial | `$nearSphere` / geospatial distance queries |

---

### 2.4 `admins` (Admin Model)
- **Source**: [src/app/module/admin/admin_model.py](file:///c:/Users/Sourav/Documents/Start/src/app/module/admin/admin_model.py)
- **Purpose**: Admin and Super Admin profile metadata.

#### Fields
| Field | BSON Type | Python Type | Required | Default | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `authId` | `ObjectId` | `PydanticObjectId` | Yes | - | Foreign Key -> `auths._id` |
| `name` | `string` | `str` | Yes | - | Admin name |
| `email` | `string` | `str` | Yes | - | Admin email |
| `profile_image` | `string` | `str \| None` | No | `None` | Admin avatar path |
| `phoneNumber` | `string` | `str \| None` | No | `None` | Phone number |
| `address` | `string` | `str \| None` | No | `None` | Address |
| `isDeleted` | `bool` | `bool \| None` | No | `False` | Soft delete flag |
| `deletedAt` | `Date` | `datetime \| None`| No | `None` | Soft delete timestamp |

#### Indexes
| Index Keys | Type | Purpose |
| :--- | :--- | :--- |
| `[("authId", 1)]` | Single field | Fast 1-to-1 relation lookup |
| `[("email", 1)]` | Single field | Email search |
| `[("isDeleted", 1), ("deletedAt", 1)]` | Compound | Soft-delete IXSCAN |

---

### 2.5 `chats` (Chat Model)
- **Source**: [src/app/module/chat/chat_model.py](file:///c:/Users/Sourav/Documents/Start/src/app/module/chat/chat_model.py)
- **Purpose**: Chat room metadata between two or more participants.

#### Fields
| Field | BSON Type | Python Type | Required | Default | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `participants` | `Array[ObjectId]` | `list[PydanticObjectId]` | Yes | `[]` | List of `users._id` in this conversation |

#### Indexes
| Index Keys | Type | Purpose |
| :--- | :--- | :--- |
| `[("participants", 1)]` | Multikey | Finding chats involving a specific user |

---

### 2.6 `messages` (Message Model)
- **Source**: [src/app/module/chat/message_model.py](file:///c:/Users/Sourav/Documents/Start/src/app/module/chat/message_model.py)
- **Purpose**: Individual chat messages. Separated from `chats` to prevent the 16MB document cap limit.

#### Fields
| Field | BSON Type | Python Type | Required | Default | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `chatId` | `ObjectId` | `PydanticObjectId` | Yes | - | Foreign Key -> `chats._id` |
| `sender` | `ObjectId` | `PydanticObjectId` | Yes | - | Foreign Key -> `users._id` |
| `receiver` | `ObjectId` | `PydanticObjectId` | Yes | - | Foreign Key -> `users._id` |
| `message` | `string` | `str` | Yes | - | Message text content |
| `isRead` | `bool` | `bool` | Yes | `False` | Message read status |

#### Indexes
| Index Keys | Type | Purpose |
| :--- | :--- | :--- |
| `[("chatId", 1), ("createdAt", -1)]` | Compound | Fast paginated chat history (newest first) |
| `[("receiver", 1), ("isRead", 1)]` | Compound | Fast count of unread messages per user |

---

### 2.7 `notifications` (Notification Model)
- **Source**: [src/app/module/notification/notification_model.py](file:///c:/Users/Sourav/Documents/Start/src/app/module/notification/notification_model.py)
- **Purpose**: In-app notifications for end users.

#### Fields
| Field | BSON Type | Python Type | Required | Default | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `toId` | `ObjectId` | `PydanticObjectId` | Yes | - | Foreign Key -> `users._id` |
| `title` | `string` | `str` | Yes | - | Notification title |
| `message` | `string` | `str` | Yes | - | Notification body |
| `isRead` | `bool` | `bool` | Yes | `False` | Read status |

#### Indexes
| Index Keys | Type | Purpose |
| :--- | :--- | :--- |
| `[("toId", 1), ("isRead", 1)]` | Compound | Fast unread notifications filter |

---

### 2.8 `adminnotifications` (AdminNotification Model)
- **Source**: [src/app/module/notification/admin_notification_model.py](file:///c:/Users/Sourav/Documents/Start/src/app/module/notification/admin_notification_model.py)
- **Purpose**: Global system alerts and administrator notifications.

#### Fields
| Field | BSON Type | Python Type | Required | Default | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `title` | `string` | `str` | Yes | - | Alert title |
| `message` | `string` | `str` | Yes | - | Alert message |
| `isRead` | `bool` | `bool` | Yes | `False` | Read status |

---

### 2.9 `feedbacks` (Feedback Model)
- **Source**: [src/app/module/feedback/feedback_model.py](file:///c:/Users/Sourav/Documents/Start/src/app/module/feedback/feedback_model.py)
- **Purpose**: User customer feedback submissions and admin responses.

#### Fields
| Field | BSON Type | Python Type | Required | Default | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `user` | `ObjectId` | `PydanticObjectId \| None` | No | `None` | Optional FK -> `users._id` |
| `name` | `string` | `str` | Yes | - | Submitter name |
| `email` | `string` | `str` | Yes | - | Submitter email |
| `feedback`| `string` | `str` | Yes | - | Feedback message |
| `reply` | `string` | `str \| None` | No | `None` | Admin response text |

---

### 2.10 `reviews` (Review Model)
- **Source**: [src/app/module/review/review_model.py](file:///c:/Users/Sourav/Documents/Start/src/app/module/review/review_model.py)
- **Purpose**: User reviews and ratings (1 to 5).

#### Fields
| Field | BSON Type | Python Type | Required | Default | Constraints |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `user` | `ObjectId` | `PydanticObjectId` | Yes | - | FK -> `users._id` |
| `rating` | `int` | `int` | Yes | - | Constrained between 1 and 5 (`ge=1, le=5`) |
| `review` | `string` | `str` | Yes | - | Written review |

---

### 2.11 Static Content Management Collections (`manage_model.py`)
- **Source**: [src/app/module/manage/manage_model.py](file:///c:/Users/Sourav/Documents/Start/src/app/module/manage/manage_model.py)
- All inherit from `_Description(TimestampedDocument)` containing a single `description: str` field.

| Collection Name | Document Model | Description |
| :--- | :--- | :--- |
| `termsconditions` | `TermsConditions` | Platform terms & conditions |
| `privacypolicies` | `PrivacyPolicy` | Platform privacy policies |
| `faqs` | `FAQ` | Frequently asked questions |
| `aboutus` | `AboutUs` | About Us information |
| `contactus` | `ContactUs` | Support contact details |

---

### 2.12 `notifications` (Notification Model)
- **Source**: [src/app/module/notification/notification_model.py](file:///c:/Users/Sourav/Documents/Start/src/app/module/notification/notification_model.py)
- **Purpose**: User-specific in-app notification feed with automatic 30-day TTL lifecycle, deep-link payloads, and read/unread status.
- **Auto-Retention**: MongoDB TTL index on `createdAt` automatically removes records after **30 days** (`expireAfterSeconds = 2592000`).

#### Fields
| Field | BSON Type | Python Type | Required | Default | Description / Constraints |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `toId` | `ObjectId` | `PydanticObjectId` | Yes | - | FK -> `users._id` (Target Recipient) |
| `senderId` | `ObjectId` | `PydanticObjectId \| None` | No | `None` | Optional FK -> Sender User/Admin |
| `title` | `string` | `str` | Yes | - | Notification title headline |
| `message` | `string` | `str` | Yes | - | Notification body content |
| `type` | `string` | `str` | Yes | `system` | Category: `system`, `chat`, `auth`, `security`, `payment`, `promotion` |
| `data` | `object` | `dict[str, Any]` | No | `{}` | Flexible deep-link navigation metadata |
| `link` | `string` | `str \| None` | No | `None` | Web URL or mobile deep-link URI |
| `image` | `string` | `str \| None` | No | `None` | Optional banner or avatar image URL |
| `isRead` | `bool` | `bool` | Yes | `False` | Read status flag |
| `readAt` | `Date` | `datetime \| None` | No | `None` | Timestamp when user opened/read notification |
| `createdAt` | `Date` | `datetime` | Yes | `utcnow()` | Creation timestamp (Bound to 30-day TTL) |
| `updatedAt` | `Date` | `datetime` | Yes | `utcnow()` | Last mutation timestamp |

#### Indexes
- `notification_created_at_ttl_idx`: `[("createdAt", ASC)]`, `expireAfterSeconds = 2592000` (Automatic 30-Day Expiration)
- `user_unread_feed_idx`: `[("toId", ASC), ("isRead", ASC), ("createdAt", DESC)]` (Hot path: unread feed)
- `user_all_feed_idx`: `[("toId", ASC), ("createdAt", DESC)]` (User feed pagination)
- `user_type_feed_idx`: `[("toId", ASC), ("type", ASC), ("createdAt", DESC)]` (Category filtering)

---

### 2.13 `adminnotifications` (AdminNotification Model)
- **Source**: [src/app/module/notification/admin_notification_model.py](file:///c:/Users/Sourav/Documents/Start/src/app/module/notification/admin_notification_model.py)
- **Purpose**: System-wide administrative broadcast notifications with automatic 30-day TTL lifecycle.
- **Auto-Retention**: MongoDB TTL index on `createdAt` automatically removes records after **30 days** (`expireAfterSeconds = 2592000`).

#### Fields
| Field | BSON Type | Python Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `title` | `string` | `str` | Yes | - | Admin alert title |
| `message` | `string` | `str` | Yes | - | Admin alert message |
| `type` | `string` | `str` | Yes | `system` | Alert category |
| `data` | `object` | `dict[str, Any]` | No | `{}` | Metadata payload |
| `link` | `string` | `str \| None` | No | `None` | Admin dashboard target link |
| `image` | `string` | `str \| None` | No | `None` | Image URL |
| `isRead` | `bool` | `bool` | Yes | `False` | Admin read flag |
| `readAt` | `Date` | `datetime \| None` | No | `None` | Timestamp read |
| `createdAt` | `Date` | `datetime` | Yes | `utcnow()` | Creation timestamp (Bound to 30-day TTL) |
| `updatedAt` | `Date` | `datetime` | Yes | `utcnow()` | Last mutation timestamp |

#### Indexes
- `admin_notification_ttl_idx`: `[("createdAt", ASC)]`, `expireAfterSeconds = 2592000` (Automatic 30-Day Expiration)
- `admin_unread_feed_idx`: `[("isRead", ASC), ("createdAt", DESC)]`
- `admin_all_feed_idx`: `[("createdAt", DESC)]`

---

### 2.14 `subscriptions` (Subscription Model)
- **Source**: [src/app/module/subscription/subscription_model.py](file:///c:/Users/Sourav/Documents/Start/src/app/module/subscription/subscription_model.py)
- **Purpose**: Stores user in-app purchase and recurring subscription entitlements synced via RevenueCat webhooks.
- **Provider**: RevenueCat (REST API v2 and Inbound Webhook integration). Controlled via `REVENUECAT_ENABLED` feature flag.

#### Fields
| Field | BSON Type | Python Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `userId` | `ObjectId` | `PydanticObjectId` | Yes | - | FK -> `users._id` (Unique 1:1 mapping) |
| `appUserId` | `string` | `str` | Yes | - | RevenueCat App User ID (MongoDB user `_id`) |
| `originalAppUserId` | `string` | `str \| None` | No | `None` | Pre-identification anonymous ID |
| `aliases` | `array` | `list[str]` | No | `[]` | RevenueCat user aliases |
| `status` | `string` | `str` | Yes | `none` | `active`, `canceled`, `expired`, `billing_issue`, `trial`, `none` |
| `productId` | `string` | `str \| None` | No | `None` | RevenueCat package / Store product identifier |
| `entitlements` | `array` | `list[str]` | No | `[]` | List of active entitlement IDs (e.g. `["pro", "premium"]`) |
| `store` | `string` | `str` | Yes | `UNKNOWN` | `APP_STORE`, `PLAY_STORE`, `STRIPE`, `PROMOTIONAL`, `AMAZON` |
| `environment` | `string` | `str` | Yes | `SANDBOX` | `SANDBOX` or `PRODUCTION` |
| `purchasedAt` | `Date` | `datetime \| None` | No | `None` | Timestamp of subscription activation |
| `expiresAt` | `Date` | `datetime \| None` | No | `None` | Subscription expiration timestamp |
| `unsubscribeDetectedAt` | `Date` | `datetime \| None` | No | `None` | Auto-renew cancellation timestamp |
| `isAutoRenewing` | `bool` | `bool` | Yes | `True` | Auto-renewal state |
| `cancelReason` | `string` | `str \| None` | No | `None` | Cancellation reason |
| `rawEvent` | `object` | `dict[str, Any]` | No | `{}` | Last processed RevenueCat webhook event payload |
| `createdAt` | `Date` | `datetime` | Yes | `utcnow()` | Document creation timestamp |
| `updatedAt` | `Date` | `datetime` | Yes | `utcnow()` | Last mutation timestamp |

#### Indexes
- `subscription_user_id_unique_idx`: `[("userId", ASC)]`, `unique=True`
- `subscription_app_user_id_idx`: `[("appUserId", ASC)]`
- `subscription_entitlement_status_idx`: `[("status", ASC), ("entitlements", ASC), ("expiresAt", DESC)]`

---

### 2.17 `payments` (Payment Model)
- **Source**: [src/app/module/payment/payment_model.py](file:///c:/Users/Sourav/Documents/Start/src/app/module/payment/payment_model.py)
- **Purpose**: Records Stripe one-time payments, checkout sessions, custom payment intents, refunds, and user transaction history.

#### Fields
| Field | BSON Type | Python Type | Required | Default | Validation / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `userId` | `ObjectId` | `PydanticObjectId` | Yes | - | Foreign Key -> `users._id` |
| `userEmail` | `string` | `str \| None` | No | `None` | Customer receipt email |
| `amount` | `double` | `float` | Yes | - | Payment amount in standard currency units (e.g. 29.99) |
| `currency` | `string` | `str` | Yes | `"usd"` | 3-letter ISO lowercase currency code |
| `status` | `string` | `str` | Yes | `"pending"` | `pending`, `succeeded`, `failed`, `canceled`, `refunded` |
| `stripePaymentIntentId` | `string` | `str \| None` | No | `None` | Stripe PaymentIntent ID (`pi_...`) |
| `stripeSessionId` | `string` | `str \| None` | No | `None` | Stripe Checkout Session ID (`cs_...`) |
| `stripeCustomerId` | `string` | `str \| None` | No | `None` | Stripe Customer ID (`cus_...`) |
| `paymentMethod` | `string` | `str \| None` | No | `"card"` | Payment method type |
| `description` | `string` | `str \| None` | No | `None` | Description or item title |
| `metadata` | `object` | `dict[str, Any]` | No | `{}` | Custom payload key-value pairs |
| `receiptUrl` | `string` | `str \| None` | No | `None` | Hosted Stripe receipt URL |
| `failureReason` | `string` | `str \| None` | No | `None` | Stripe error message upon failure |
| `createdAt` | `Date` | `datetime` | Yes | `utcnow()` | Document creation timestamp |
| `updatedAt` | `Date` | `datetime` | Yes | `utcnow()` | Document mutation timestamp |

#### Indexes
- `[("userId", 1)]`: Fast lookup for user payment history
- `[("stripePaymentIntentId", 1)]`: Sparse index for webhook event matching
- `[("stripeSessionId", 1)]`: Sparse index for checkout session webhook matching
- `[("status", 1)]`: Fast filtering for successful/pending payments
- `[("createdAt", -1)]`: Fast chronological sort for payment history
- `[("userId", 1), ("status", 1)]`: Compound index for user filtered payments

---

## 3. In-Memory Redis Key Catalog & Namespace Contracts

The application utilizes **Redis (asyncio)** as a sub-millisecond in-memory cache, distributed rate limiter, and JWT token revocation layer. 

### 3.1 Namespace Specifications & TTL Contracts

| Key Pattern / Namespace | Data Type | Default TTL | Eviction Policy | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `auth:blacklist:jti:{jti}` | `string` | Remaining token lifespan (`exp - now`) | `volatile-ttl` | Instant revocation of logged-out JWT tokens. |
| `auth:ban:user:{auth_id}` | `string` | 900s (15 min) | `volatile-ttl` | Instant ban/block of all active access tokens upon admin block, password change, or token theft. |
| `ratelimit:{name}:{identifier}` | `integer` | Window duration (e.g. 900s) | `volatile-ttl` | Distributed atomic rate limiting across all Uvicorn workers and containers. |
| `lock:{lock_name}` | `string` | 10s | `volatile-ttl` | Distributed mutex lock (SETNX) preventing Cache Stampedes / Thundering Herd. |
| `cache:{cache_key}` | `string (JSON)` | Jittered Base TTL (±10%) | `volatile-ttl` | High-performance cached query payloads with Cache Avalanche and Penetration protection. |

### 3.2 Production Redis Server Configuration
- **Memory Limit**: `maxmemory 256mb`
- **Eviction Strategy**: `volatile-ttl` (Safeguards persistent data by only evicting keys with an explicit TTL that are closest to expiration)
- **Data Persistence**: Hybrid RDB (snapshots every 300s/10 changes) + AOF (`appendfsync everysec`)
- **Non-blocking Operations**: Background memory reclamation (`lazyfree-lazy-eviction`, `lazyfree-lazy-expire`, `lazyfree-lazy-server-del`) and non-blocking `UNLINK` / `SCAN`.

