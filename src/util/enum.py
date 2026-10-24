class EnumUserRole:
    USER = "USER"
    DRIVER = "DRIVER"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


class EnumPaymentStatus:
    SUCCEEDED = "succeeded"
    UNPAID = "unpaid"


class EnumSocketEvent:
    CONNECTION = "connection"
    DISCONNECT = "disconnect"

    SOCKET_ERROR = "socket_error"
    ONLINE_STATUS = "online_status"
    UPDATE_LOCATION = "update_location"

    START_CHAT = "start_chat"
    SEND_MESSAGE = "send_message"


class EnumLoginProvider:
    LOCAL = "local"
    GOOGLE = "google"
    APPLE = "apple"


class EnumUserAccountStatus:
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
