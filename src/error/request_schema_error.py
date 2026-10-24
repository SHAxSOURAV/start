from pydantic import ValidationError


class RequestSchemaError(Exception):
    """A request body/query/params schema violation (zod's counterpart)."""

    def __init__(self, error: ValidationError) -> None:
        super().__init__("Validation error")
        self.error = error
