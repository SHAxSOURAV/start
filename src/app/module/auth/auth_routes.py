from fastapi import APIRouter, Depends

from src.app.middleware.auth import auth
from src.app.middleware.limiter import (
    change_password_limiter,
    delete_me_limiter,
    email_resend_cooldown_limiter,
    limiter,
    login_email_cooldown_limiter,
    login_limiter,
    otp_email_cooldown_limiter,
    otp_send_limiter,
    otp_verify_limiter,
    signup_limiter,
)
from src.app.middleware.validate_request import validate_request
from src.app.module.auth.auth_controller import AuthController
from src.app.module.auth.auth_validation import AuthValidation
from src.config import config

router = APIRouter()

# 1. Sign In (First)
router.add_api_route(
    "/sign-in",
    AuthController.sign_in,
    methods=["POST"],
    dependencies=[
        Depends(login_limiter),
        Depends(login_email_cooldown_limiter),
        Depends(validate_request(AuthValidation.sign_in)),
    ],
    summary="Sign in to user account",
)

# 1.1 Google Sign-In
router.add_api_route(
    "/google-sign-in",
    AuthController.google_sign_in,
    methods=["POST"],
    dependencies=[
        Depends(login_limiter),
        Depends(validate_request(AuthValidation.google_sign_in)),
    ],
    summary="Sign in or register with Google OAuth ID token",
)

# 1.2 Apple Sign-In
router.add_api_route(
    "/apple-sign-in",
    AuthController.apple_sign_in,
    methods=["POST"],
    dependencies=[
        Depends(login_limiter),
        Depends(validate_request(AuthValidation.apple_sign_in)),
    ],
    summary="Sign in or register with Apple identity token",
)

# 2. Sign Up (Second)
router.add_api_route(
    "/sign-up",
    AuthController.sign_up,
    methods=["POST"],
    dependencies=[
        Depends(signup_limiter),
        Depends(validate_request(AuthValidation.sign_up)),
    ],
    summary="Sign up a new user account",
)

# 3. Account Activation & OTP Management
router.add_api_route(
    "/activate-account",
    AuthController.activate_account,
    methods=["POST"],
    dependencies=[
        Depends(otp_email_cooldown_limiter),
        Depends(otp_verify_limiter),
        Depends(validate_request(AuthValidation.activate_account)),
    ],
    summary="Verify emailed OTP and activate account",
)
router.add_api_route(
    "/resend-otp",
    AuthController.resend_otp,
    methods=["POST"],
    dependencies=[
        Depends(email_resend_cooldown_limiter),
        Depends(otp_send_limiter),
        Depends(validate_request(AuthValidation.resend_otp)),
    ],
    summary="Resend activation OTP",
)

# 4. Token Refresh & Session Logout
router.add_api_route(
    "/refresh-token",
    AuthController.refresh_token,
    methods=["POST"],
    dependencies=[
        Depends(otp_verify_limiter),
        Depends(validate_request(AuthValidation.refresh_token)),
    ],
    summary="Exchange and rotate refresh token for new access and refresh tokens",
)
router.add_api_route(
    "/logout",
    AuthController.logout,
    methods=["POST"],
    summary="Log out from current device session and clear refresh token cookie",
)

# 5. Password Reset Flow
router.add_api_route(
    "/forgot-password",
    AuthController.forgot_pass,
    methods=["POST"],
    dependencies=[
        Depends(email_resend_cooldown_limiter),
        Depends(otp_send_limiter),
        Depends(validate_request(AuthValidation.forgot_password)),
    ],
    summary="Send password reset OTP",
)
router.add_api_route(
    "/verify-otp",
    AuthController.verify_otp,
    methods=["POST"],
    dependencies=[
        Depends(otp_email_cooldown_limiter),
        Depends(otp_verify_limiter),
        Depends(validate_request(AuthValidation.verify_otp)),
    ],
    summary="Verify password reset OTP",
)
router.add_api_route(
    "/reset-password",
    AuthController.reset_password,
    methods=["POST"],
    dependencies=[
        Depends(otp_verify_limiter),
        Depends(validate_request(AuthValidation.reset_password)),
    ],
    summary="Set new password after OTP verification",
)

# 6. Authenticated Password Change
router.add_api_route(
    "/change-password",
    AuthController.change_password,
    methods=["PATCH"],
    dependencies=[
        Depends(auth(config.auth_level.user)),
        Depends(change_password_limiter),
        Depends(validate_request(AuthValidation.change_password)),
    ],
    summary="Change password for authenticated user",
)

# 7. Authenticated User Profile & Account Management
router.add_api_route(
    "/me",
    AuthController.get_me,
    methods=["GET"],
    dependencies=[
        Depends(auth(config.auth_level.user)),
    ],
    summary="Get currently authenticated user profile",
)
router.add_api_route(
    "/me",
    AuthController.delete_me,
    methods=["DELETE"],
    dependencies=[
        Depends(auth(config.auth_level.user)),
        Depends(delete_me_limiter),
        Depends(validate_request(AuthValidation.delete_me)),
    ],
    summary="Soft delete user account (30-day retention with password confirmation)",
)

# 8. Device & Session Management
router.add_api_route(
    "/sessions",
    AuthController.list_sessions,
    methods=["GET"],
    dependencies=[
        Depends(auth(config.auth_level.user)),
    ],
    summary="List all active device sessions for authenticated user",
)
router.add_api_route(
    "/logout-other-devices",
    AuthController.logout_other_devices,
    methods=["POST"],
    dependencies=[
        Depends(auth(config.auth_level.user)),
    ],
    summary="Log out from all other active devices except current session",
)
router.add_api_route(
    "/sessions/{session_id}",
    AuthController.revoke_session,
    methods=["DELETE"],
    dependencies=[
        Depends(auth(config.auth_level.user)),
    ],
    summary="Remotely revoke a specific device session",
)

# --- Backward compatibility aliases (omitted from OpenAPI docs) ---
router.add_api_route(
    "/login",
    AuthController.sign_in,
    methods=["POST"],
    dependencies=[
        Depends(limiter),
        Depends(validate_request(AuthValidation.sign_in)),
    ],
    include_in_schema=False,
)
router.add_api_route(
    "/register",
    AuthController.sign_up,
    methods=["POST"],
    dependencies=[Depends(validate_request(AuthValidation.sign_up))],
    include_in_schema=False,
)
router.add_api_route(
    "/activation-code-resend",
    AuthController.resend_otp,
    methods=["POST"],
    dependencies=[
        Depends(otp_send_limiter),
        Depends(validate_request(AuthValidation.resend_otp)),
    ],
    include_in_schema=False,
)
router.add_api_route(
    "/forget-pass-otp-verify",
    AuthController.verify_otp,
    methods=["POST"],
    dependencies=[
        Depends(otp_verify_limiter),
        Depends(validate_request(AuthValidation.verify_otp)),
    ],
    include_in_schema=False,
)
