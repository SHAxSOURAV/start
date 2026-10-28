from fastapi import APIRouter, Depends

from src.app.middleware.auth import auth
from src.app.module.review.review_controller import ReviewController
from src.config import config

router = APIRouter()

user_only = [Depends(auth(config.auth_level.user))]

router.add_api_route(
    "/post-review",
    ReviewController.post_review,
    methods=["POST"],
    dependencies=user_only,
)
router.add_api_route(
    "/get-all-reviews",
    ReviewController.get_all_reviews,
    methods=["GET"],
    dependencies=user_only,
)
router.add_api_route(
    "/get-review",
    ReviewController.get_review,
    methods=["GET"],
    dependencies=user_only,
)
router.add_api_route(
    "/update-review",
    ReviewController.update_review,
    methods=["PATCH"],
    dependencies=user_only,
)
router.add_api_route(
    "/delete-review",
    ReviewController.delete_review,
    methods=["DELETE"],
    dependencies=user_only,
)
