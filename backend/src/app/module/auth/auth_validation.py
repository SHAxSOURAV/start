import re

from pydantic import BaseModel, field_validator

EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def check_email(value: str) -> str:
    cleaned = value.strip().lower()
    if not EMAIL_REGEX.match(cleaned):
        raise ValueError("Please provide a valid email address")
    return cleaned


def check_password(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters")
    return value


def check_non_empty(value: str, message: str) -> str:
    if not value:
        raise ValueError(message)
    return value


class RegisterBody(BaseModel):
    name: str
    email: str
    role: str
    password: str
    confirmPassword: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return check_email(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return check_password(v)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return check_non_empty(v, "Name is required")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        return check_non_empty(v, "Role is required")

    @field_validator("confirmPassword")
    @classmethod
    def validate_confirm(cls, v: str) -> str:
        return check_non_empty(v, "Confirm password is required")


class Register(BaseModel):
    body: RegisterBody


class LoginBody(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return check_email(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return check_non_empty(v, "Password is required")


class Login(BaseModel):
    body: LoginBody


class ActivateAccountBody(BaseModel):
    email: str
    activationCode: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return check_email(v)

    @field_validator("activationCode")
    @classmethod
    def validate_code(cls, v: str) -> str:
        return check_non_empty(v, "Code is required")


class ActivateAccount(BaseModel):
    body: ActivateAccountBody


class EmailOnlyBody(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return check_email(v)


class EmailOnly(BaseModel):
    body: EmailOnlyBody


class ForgetPassOtpVerifyBody(BaseModel):
    email: str
    code: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return check_email(v)

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        return check_non_empty(v, "Code is required")


class ForgetPassOtpVerify(BaseModel):
    body: ForgetPassOtpVerifyBody


class ResetPasswordBody(BaseModel):
    email: str
    newPassword: str
    confirmPassword: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return check_email(v)

    @field_validator("newPassword")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return check_password(v)

    @field_validator("confirmPassword")
    @classmethod
    def validate_confirm(cls, v: str) -> str:
        return check_non_empty(v, "Confirm password is required")


class ResetPassword(BaseModel):
    body: ResetPasswordBody


class ChangePasswordBody(BaseModel):
    oldPassword: str
    newPassword: str
    confirmPassword: str

    @field_validator("newPassword")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return check_password(v)

    @field_validator("oldPassword")
    @classmethod
    def validate_old(cls, v: str) -> str:
        return check_non_empty(v, "Old password is required")

    @field_validator("confirmPassword")
    @classmethod
    def validate_confirm(cls, v: str) -> str:
        return check_non_empty(v, "Confirm password is required")


class ChangePassword(BaseModel):
    body: ChangePasswordBody


class RefreshTokenBody(BaseModel):
    refreshToken: str | None = None  # may come from the cookie instead


class RefreshToken(BaseModel):
    body: RefreshTokenBody


class DeleteMeBody(BaseModel):
    password: str | None = None


class DeleteMe(BaseModel):
    body: DeleteMeBody


class GoogleSignInBody(BaseModel):
    idToken: str

    @field_validator("idToken")
    @classmethod
    def validate_id_token(cls, v: str) -> str:
        return check_non_empty(v, "idToken is required")


class GoogleSignIn(BaseModel):
    body: GoogleSignInBody


class AppleSignInBody(BaseModel):
    identityToken: str
    name: str | None = None

    @field_validator("identityToken")
    @classmethod
    def validate_identity_token(cls, v: str) -> str:
        return check_non_empty(v, "identityToken is required")


class AppleSignIn(BaseModel):
    body: AppleSignInBody


class AuthValidation:
    sign_in = Login
    sign_up = Register
    google_sign_in = GoogleSignIn
    apple_sign_in = AppleSignIn
    resend_otp = EmailOnly
    verify_otp = ForgetPassOtpVerify
    forgot_password = EmailOnly
    delete_me = DeleteMe

    register = Register
    login = Login
    activate_account = ActivateAccount
    email_only = EmailOnly
    forget_pass_otp_verify = ForgetPassOtpVerify
    reset_password = ResetPassword
    change_password = ChangePassword
    refresh_token = RefreshToken
