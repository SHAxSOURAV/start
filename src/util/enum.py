class EnumUserRole:
    USER = "USER"
    DRIVER = "DRIVER"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


class EnumPaymentStatus:
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"
    UNPAID = "unpaid"


class EnumSubscriptionStatus:
    ACTIVE = "active"
    TRIAL = "trial"
    CANCELED = "canceled"
    EXPIRED = "expired"
    BILLING_ISSUE = "billing_issue"
    NONE = "none"


class EnumSubscriptionStore:
    APP_STORE = "APP_STORE"
    PLAY_STORE = "PLAY_STORE"
    STRIPE = "STRIPE"
    PROMOTIONAL = "PROMOTIONAL"
    AMAZON = "AMAZON"
    UNKNOWN = "UNKNOWN"


class EnumSocketEvent:
    CONNECTION = "connection"
    DISCONNECT = "disconnect"

    SOCKET_ERROR = "socket_error"
    ONLINE_STATUS = "online_status"
    UPDATE_LOCATION = "update_location"

    START_CHAT = "start_chat"
    SEND_MESSAGE = "send_message"
    NOTIFICATION = "notification"
    FORCE_LOGOUT = "force_logout"


class EnumNotificationType:
    SYSTEM = "system"
    CHAT = "chat"
    AUTH = "auth"
    SECURITY = "security"
    PAYMENT = "payment"
    PROMOTION = "promotion"


class EnumLoginProvider:
    LOCAL = "local"
    GOOGLE = "google"
    APPLE = "apple"


class EnumUserAccountStatus:
    VERIFIED = "verified"
    UNVERIFIED = "unverified"


class EnumAccountStatus:
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    UNAPPROVED = "UNAPPROVED"
    SUSPENDED = "SUSPENDED"
    BANNED = "BANNED"


class EnumAuditAction:
    USER_BAN = "USER_BAN"
    USER_UNBAN = "USER_UNBAN"
    USER_SUSPEND = "USER_SUSPEND"
    USER_UNAPPROVE = "USER_UNAPPROVE"
    USER_ACTIVATE = "USER_ACTIVATE"

