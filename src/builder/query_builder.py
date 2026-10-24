import math
import re
from typing import Any

from pymongo.collation import Collation

# Query parameters coming from the URL
# (e.g. ?searchTerm=john&sort=name&page=2&limit=10&fields=name,email)
QueryParams = dict[str, Any]

# What count_total() returns
PaginationMeta = dict[str, int]

REGEX_META = re.compile(r"([.*+?^${}()|\[\]\\])")


def _parse_projection(spec: str) -> dict[str, int]:
    projection: dict[str, int] = {}
    for token in spec.split():
        if not token:
            continue
        if token.startswith("-"):
            projection[token[1:]] = 0
        else:
            projection[token] = 1
    return projection


def _parse_sort(spec: str) -> list[tuple[str, int]]:
    order: list[tuple[str, int]] = []
    for token in spec.split():
        if not token:
            continue
        if token.startswith("-"):
            order.append((token[1:], -1))
        else:
            order.append((token, 1))
    return order


class QueryBuilder:
    """Mongoose QueryBuilder equivalent, chained the same way.

    Documents come back as plain dicts, matching the `.lean()` calls the
    TypeScript version used at every call site.
    """

    def __init__(
        self,
        document_cls: Any,
        base_filter: dict[str, Any] | None,
        query: QueryParams | None,
    ) -> None:
        self.document_cls = document_cls
        self.collection = document_cls.get_pymongo_collection()
        self._filter: dict[str, Any] = dict(base_filter or {})
        self.query: QueryParams = query or {}

        self._sort: list[tuple[str, int]] = []
        self._skip = 0
        self._limit = 0
        self._projection: dict[str, int] | None = None
        self._collation: Collation | None = None

    def search(self, searchable_fields: list[str]) -> QueryBuilder:
        search_term = self.query.get("searchTerm")

        if search_term and isinstance(search_term, str):
            # Escape regex metacharacters so user input can't inject regex
            # patterns (ReDoS) into the $regex query
            escaped_term = REGEX_META.sub(r"\\\1", search_term)

            self._filter["$or"] = [
                {field: {"$regex": escaped_term, "$options": "i"}}
                for field in searchable_fields
            ]
            self._collation = Collation(locale="en", strength=2)

        return self

    def filter(self) -> QueryBuilder:
        query_obj = dict(self.query)

        # Remove fields that are not actual database filters
        for key in ("searchTerm", "sort", "limit", "page", "fields"):
            query_obj.pop(key, None)

        # Only allow plain string values on safe keys. Operator keys and dotted
        # paths are dropped entirely -- ?age[$ne]=0 is a NoSQL operator injection.
        for key, value in query_obj.items():
            if key.startswith("$") or "." in key:
                continue
            if isinstance(value, str):
                self._filter[key] = value

        return self

    def sort(self) -> QueryBuilder:
        # Comma-separated sort string, newest first when absent
        spec = " ".join((self.query.get("sort") or "").split(",")) or "-createdAt"
        self._sort = _parse_sort(spec)
        return self

    def paginate(self) -> QueryBuilder:
        page = _to_int(self.query.get("page"), 1)
        limit = _to_int(self.query.get("limit"), 10)

        self._skip = (page - 1) * limit
        self._limit = limit
        return self

    def fields(self) -> QueryBuilder:
        # Comma-separated field list, excluding __v when absent
        spec = " ".join((self.query.get("fields") or "").split(",")) or "-__v"
        self._projection = _parse_projection(spec)
        return self

    async def execute(self) -> list[dict[str, Any]]:
        cursor = self.collection.find(self._filter, self._projection)

        if self._collation is not None:
            cursor = cursor.collation(self._collation)
        if self._sort:
            cursor = cursor.sort(self._sort)
        if self._skip:
            cursor = cursor.skip(self._skip)
        if self._limit:
            cursor = cursor.limit(self._limit)

        return await cursor.to_list(length=self._limit or None)

    async def count_total(self) -> PaginationMeta:
        total = await self.collection.count_documents(self._filter)

        page = _to_int(self.query.get("page"), 1)
        limit = _to_int(self.query.get("limit"), 10)
        total_page = math.ceil(total / limit) if limit else 0

        return {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPage": total_page,
        }


def _to_int(value: Any, fallback: int) -> int:
    try:
        parsed = int(value)
    except TypeError, ValueError:
        return fallback
    return parsed or fallback
