from fastapi import APIRouter, Depends

from src.app.middleware.auth import auth
from src.app.middleware.file_uploader import upload_file
from src.app.module.admin.admin_controller import AdminController
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
