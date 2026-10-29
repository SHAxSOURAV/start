from fastapi import APIRouter, Depends

from src.app.middleware.auth import auth
from src.app.middleware.file_uploader import upload_file
from src.app.middleware.validate_request import validate_request
from src.app.module.admin.admin_controller import AdminController
from src.app.module.admin.admin_validation import AdminValidation
from src.config import config

router = APIRouter()

router.add_api_route(
    "/create-admin",
    AdminController.create_admin,
    methods=["POST"],
    dependencies=[Depends(auth(config.auth_level.super_admin))],
)
router.add_api_route(
    "/profile",
    AdminController.get_profile,
    methods=["GET"],
    dependencies=[Depends(auth(config.auth_level.admin))],
)
router.add_api_route(
    "/edit-profile",
    AdminController.update_profile,
    methods=["PATCH"],
    dependencies=[
        Depends(auth(config.auth_level.admin)),
        Depends(upload_file()),
    ],
)
router.add_api_route(
    "/delete-account",
    AdminController.delete_my_account,
    methods=["DELETE"],
    dependencies=[Depends(auth(config.auth_level.admin))],
)
router.add_api_route(
    "/statistics/overview",
    AdminController.get_overview_statistics,
    methods=["GET"],
    dependencies=[Depends(auth(config.auth_level.admin))],
)
router.add_api_route(
    "/statistics/charts",
    AdminController.get_charts_statistics,
    methods=["GET"],
    dependencies=[Depends(auth(config.auth_level.admin))],
)
router.add_api_route(
    "/statistics/breakdowns",
    AdminController.get_breakdowns_statistics,
    methods=["GET"],
    dependencies=[Depends(auth(config.auth_level.admin))],
)
router.add_api_route(
    "/users",
    AdminController.get_all_users,
    methods=["GET"],
    dependencies=[Depends(auth(config.auth_level.admin))],
    summary="Retrieve paginated user list with filters (status, role, search)",
)
router.add_api_route(
    "/users/banned",
    AdminController.get_banned_users,
    methods=["GET"],
    dependencies=[Depends(auth(config.auth_level.admin))],
    summary="Retrieve paginated list of all banned users",
)
router.add_api_route(
    "/users/{id}/status",
    AdminController.manage_user_status,
    methods=["PATCH"],
    dependencies=[
        Depends(auth(config.auth_level.admin)),
        Depends(validate_request(AdminValidation.manage_user_status)),
    ],
    summary="Instantly ban, suspend, unapprove, or restore a user account",
)
router.add_api_route(
    "/audit-logs",
    AdminController.get_audit_logs,
    methods=["GET"],
    dependencies=[Depends(auth(config.auth_level.admin))],
    summary="Retrieve paginated administrative audit logs",
)


