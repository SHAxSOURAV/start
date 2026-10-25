import pytest
from pydantic import ValidationError

from src.app.module.admin.admin_user_service import ROLE_WEIGHTS
from src.app.module.admin.admin_validation import ManageUserStatusPayload
from src.util.enum import EnumAccountStatus, EnumUserRole


def test_validation_valid_payload() -> None:
    payload = ManageUserStatusPayload(
        action="BAN",
        reason="Terms of service violation",
        internal_note="Investigated by safety team",
        revoke_sessions=True,
        notify_user=True,
    )
    assert payload.action == "BAN"
    assert payload.revoke_sessions is True
    assert payload.notify_user is True


def test_validation_invalid_action() -> None:
    with pytest.raises(ValidationError):
        ManageUserStatusPayload(action="INVALID_ACTION")  # type: ignore[arg-type]


def test_validation_duration_hours_limits() -> None:
    # Valid duration
    payload = ManageUserStatusPayload(action="SUSPEND", duration_hours=48)
    assert payload.duration_hours == 48

    # Below minimum (ge=1)
    with pytest.raises(ValidationError):
        ManageUserStatusPayload(action="SUSPEND", duration_hours=0)

    # Above maximum (le=8760)
    with pytest.raises(ValidationError):
        ManageUserStatusPayload(action="SUSPEND", duration_hours=9000)


def test_role_hierarchy_weights() -> None:
    """Verifies privilege escalation prevention weights."""
    assert (
        ROLE_WEIGHTS[EnumUserRole.SUPER_ADMIN]
        > ROLE_WEIGHTS[EnumUserRole.ADMIN]
    )
    assert ROLE_WEIGHTS[EnumUserRole.ADMIN] > ROLE_WEIGHTS[EnumUserRole.DRIVER]
    assert ROLE_WEIGHTS[EnumUserRole.ADMIN] > ROLE_WEIGHTS[EnumUserRole.USER]
    assert ROLE_WEIGHTS[EnumUserRole.DRIVER] > ROLE_WEIGHTS[EnumUserRole.USER]


def test_enum_account_statuses() -> None:
    assert EnumAccountStatus.BANNED == "BANNED"
    assert EnumAccountStatus.SUSPENDED == "SUSPENDED"
    assert EnumAccountStatus.UNAPPROVED == "UNAPPROVED"
    assert EnumAccountStatus.ACTIVE == "ACTIVE"
