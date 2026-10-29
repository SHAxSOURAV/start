from typing import Any

from src.app.module.manage.manage_model import (
    FAQ,
    AboutUs,
    ContactUs,
    PrivacyPolicy,
    TermsConditions,
)
from src.error.api_error import ApiError
from src.util.base_document import utcnow
from src.util.http_status import status
from src.util.serialize import serialize


async def upsert_doc(model: Any, payload: dict[str, Any], updated_message: str) -> Any:
    exists = await model.get_pymongo_collection().find_one({})

    if exists:
        result = await model.get_pymongo_collection().find_one_and_update(
            {},
            {"$set": {**payload, "updatedAt": utcnow()}},
            return_document=True,
        )
        return {"message": updated_message, "result": result}

    doc = model(**payload)
    await doc.insert()
    return serialize(doc.model_dump(by_alias=True))


async def _get_one(model: Any) -> dict[str, Any] | None:
    return await model.get_pymongo_collection().find_one({})


async def _delete_one(model: Any, doc_id: str, not_found: str) -> dict[str, Any]:
    from bson import ObjectId

    result = await model.get_pymongo_collection().delete_one(
        {"_id": ObjectId(str(doc_id))}
    )
    if not result.deleted_count:
        raise ApiError(status.NOT_FOUND, not_found)
    return {"acknowledged": result.acknowledged, "deletedCount": result.deleted_count}


async def add_terms_conditions(payload: dict[str, Any]) -> Any:
    return await upsert_doc(TermsConditions, payload, "Terms & conditions updated")


async def get_terms_conditions() -> dict[str, Any] | None:
    return await _get_one(TermsConditions)


async def delete_terms_conditions(query: dict[str, Any]) -> dict[str, Any]:
    return await _delete_one(
        TermsConditions, query.get("id", ""), "TermsConditions not found"
    )


async def add_privacy_policy(payload: dict[str, Any]) -> Any:
    return await upsert_doc(PrivacyPolicy, payload, "Privacy policy updated")


async def get_privacy_policy() -> dict[str, Any] | None:
    return await _get_one(PrivacyPolicy)


async def delete_privacy_policy(query: dict[str, Any]) -> dict[str, Any]:
    return await _delete_one(
        PrivacyPolicy, query.get("id", ""), "Privacy Policy not found"
    )


async def add_about_us(payload: dict[str, Any]) -> Any:
    return await upsert_doc(AboutUs, payload, "About Us updated")


async def get_about_us() -> dict[str, Any] | None:
    return await _get_one(AboutUs)


async def delete_about_us(query: dict[str, Any]) -> dict[str, Any]:
    return await _delete_one(AboutUs, query.get("id", ""), "About Us not found")


async def add_faq(payload: dict[str, Any]) -> Any:
    return await upsert_doc(FAQ, payload, "FAQ updated")


async def get_faq() -> dict[str, Any] | None:
    return await _get_one(FAQ)


async def delete_faq(query: dict[str, Any]) -> dict[str, Any]:
    return await _delete_one(FAQ, query.get("id", ""), "FAQ not found")


async def add_contact_us(payload: dict[str, Any]) -> Any:
    return await upsert_doc(ContactUs, payload, "Contact Us updated")


async def get_contact_us() -> dict[str, Any] | None:
    return await _get_one(ContactUs)


async def delete_contact_us(query: dict[str, Any]) -> dict[str, Any]:
    return await _delete_one(ContactUs, query.get("id", ""), "Contact Us not found")


class ManageService:
    add_privacy_policy = staticmethod(add_privacy_policy)
    get_privacy_policy = staticmethod(get_privacy_policy)
    delete_privacy_policy = staticmethod(delete_privacy_policy)
    add_terms_conditions = staticmethod(add_terms_conditions)
    get_terms_conditions = staticmethod(get_terms_conditions)
    delete_terms_conditions = staticmethod(delete_terms_conditions)
    add_about_us = staticmethod(add_about_us)
    get_about_us = staticmethod(get_about_us)
    delete_about_us = staticmethod(delete_about_us)
    add_faq = staticmethod(add_faq)
    get_faq = staticmethod(get_faq)
    delete_faq = staticmethod(delete_faq)
    add_contact_us = staticmethod(add_contact_us)
    get_contact_us = staticmethod(get_contact_us)
    delete_contact_us = staticmethod(delete_contact_us)
