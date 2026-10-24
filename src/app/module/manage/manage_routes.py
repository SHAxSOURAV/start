from fastapi import APIRouter, Depends

from src.app.middleware.auth import auth
from src.app.module.manage.manage_controller import ManageController
from src.config import config

router = APIRouter()

admin_only = [Depends(auth(config.auth_level.admin))]

router.add_api_route(
    "/add-terms-conditions",
    ManageController.add_terms_conditions,
    methods=["POST"],
    dependencies=admin_only,
)
router.add_api_route(
    "/get-terms-conditions", ManageController.get_terms_conditions, methods=["GET"]
)
router.add_api_route(
    "/delete-terms-conditions",
    ManageController.delete_terms_conditions,
    methods=["DELETE"],
    dependencies=admin_only,
)

router.add_api_route(
    "/add-privacy-policy",
    ManageController.add_privacy_policy,
    methods=["POST"],
    dependencies=admin_only,
)
router.add_api_route(
    "/get-privacy-policy", ManageController.get_privacy_policy, methods=["GET"]
)
router.add_api_route(
    "/delete-privacy-policy",
    ManageController.delete_privacy_policy,
    methods=["DELETE"],
    dependencies=admin_only,
)

router.add_api_route(
    "/add-about-us",
    ManageController.add_about_us,
    methods=["POST"],
    dependencies=admin_only,
)
router.add_api_route("/get-about-us", ManageController.get_about_us, methods=["GET"])
router.add_api_route(
    "/delete-about-us",
    ManageController.delete_about_us,
    methods=["DELETE"],
    dependencies=admin_only,
)

router.add_api_route(
    "/add-faq", ManageController.add_faq, methods=["POST"], dependencies=admin_only
)
router.add_api_route("/get-faq", ManageController.get_faq, methods=["GET"])
router.add_api_route(
    "/delete-faq",
    ManageController.delete_faq,
    methods=["DELETE"],
    dependencies=admin_only,
)

router.add_api_route(
    "/add-contact-us",
    ManageController.add_contact_us,
    methods=["POST"],
    dependencies=admin_only,
)
router.add_api_route(
    "/get-contact-us", ManageController.get_contact_us, methods=["GET"]
)
router.add_api_route(
    "/delete-contact-us",
    ManageController.delete_contact_us,
    methods=["DELETE"],
    dependencies=admin_only,
)
