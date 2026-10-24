from fastapi import APIRouter, Depends

from src.app.middleware.auth import auth
from src.app.module.feedback.feedback_controller import FeedbackController
from src.config import config

router = APIRouter()

router.add_api_route(
    "/post-feedback",
    FeedbackController.post_feedback,
    methods=["POST"],
    dependencies=[Depends(auth(config.auth_level.user, False))],
)
router.add_api_route(
    "/get-feedback",
    FeedbackController.get_feedback,
    methods=["GET"],
    dependencies=[Depends(auth(config.auth_level.user))],
)
router.add_api_route(
    "/get-all-feedbacks",
    FeedbackController.get_all_feedbacks,
    methods=["GET"],
    dependencies=[Depends(auth(config.auth_level.user))],
)
router.add_api_route(
    "/update-feedback-with-reply",
    FeedbackController.update_feedback_with_reply,
    methods=["PATCH"],
    dependencies=[Depends(auth(config.auth_level.admin))],
)
router.add_api_route(
    "/delete-feedback",
    FeedbackController.delete_feedback,
    methods=["DELETE"],
    dependencies=[Depends(auth(config.auth_level.user))],
)
