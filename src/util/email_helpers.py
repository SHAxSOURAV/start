from src.error.api_error import ApiError
from src.mail.new_device_login_email_temp import new_device_login_email_temp
from src.mail.otp_resend_temp import otp_resend_temp
from src.mail.reset_pass_email_temp import reset_pass_email_temp
from src.mail.sign_up_email_temp import sign_up_email_temp
from src.util.http_status import status
from src.util.send_email import send_email


async def send_activation_email(email: str, data: dict) -> None:
    try:
        await send_email(
            {
                "email": email,
                "subject": "Activate Your Account",
                "html": sign_up_email_temp(
                    {
                        "user": data["user"],
                        "activationCode": data["activationCode"],
                        "activationCodeExpire": str(data["activationCodeExpire"]),
                    }
                ),
            }
        )
    except Exception as error:
        print(error)
        raise ApiError(status.INTERNAL_SERVER_ERROR, "Email was not sent") from error


async def send_otp_resend_email(email: str, data: dict) -> None:
    try:
        await send_email(
            {
                "email": email,
                "subject": "New Activation Code",
                "html": otp_resend_temp(
                    {
                        "user": data["user"],
                        "code": int(data["activationCode"]),
                        "expiresIn": int(data["activationCodeExpire"]),
                        "activationCode": int(data["activationCode"]),
                        "activationCodeExpire": int(data["activationCodeExpire"]),
                    }
                ),
            }
        )
    except Exception as error:
        print(error)
        raise ApiError(status.INTERNAL_SERVER_ERROR, "Email was not sent") from error


async def send_reset_password_email(email: str, data: dict) -> None:
    try:
        await send_email(
            {
                "email": email,
                "subject": "Password Reset Code",
                "html": reset_pass_email_temp(
                    {
                        "name": data["user"],
                        "verificationCode": int(data["verificationCode"]),
                        "verificationCodeExpire": data["verificationCodeExpire"],
                    }
                ),
            }
        )
    except Exception as error:
        print(error)
        raise ApiError(status.INTERNAL_SERVER_ERROR, "Email was not sent") from error


async def send_new_device_login_email(email: str, data: dict) -> None:
    try:
        await send_email(
            {
                "email": email,
                "subject": "Security Alert: New Sign-in to Your Account",
                "html": new_device_login_email_temp(data),
            }
        )
    except Exception as error:
        print(f"Failed to send new device login email: {error}")


class EmailHelpers:
    send_activation_email = staticmethod(send_activation_email)
    send_otp_resend_email = staticmethod(send_otp_resend_email)
    send_reset_password_email = staticmethod(send_reset_password_email)
    send_new_device_login_email = staticmethod(send_new_device_login_email)
