from fastapi import APIRouter, Depends

from src.app.middleware.auth import auth
from src.app.middleware.file_uploader import upload_file
from src.app.module.user.user_controller import UserController
from src.config import config

router = APIRouter()

router.add_api_route(
    "/profile",
    UserController.get_profile,
    methods=["GET"],
    dependencies=[Depends(auth(config.auth_level.user))],
)
router.add_api_route(
    "/edit-profile",
    UserController.update_profile,
    methods=["PATCH"],
    dependencies=[
        Depends(auth(config.auth_level.user)),
        Depends(upload_file()),
    ],
)
router.add_api_route(
    "/delete-account",
    UserController.delete_my_account,
    methods=["DELETE"],
    dependencies=[Depends(auth(config.auth_level.user))],
)
