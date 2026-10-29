import re

from src.error.api_error import ApiError
from src.util.http_status import status

DATE_REGEX = re.compile(r"^\d{4}-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01])$")
TIME_REGEX = re.compile(r"((1[0-2]|0?[1-9]):([0-5][0-9]) ?([AaPp][Mm]))")


def date_time_validator(
    input_date: list[str] | None = None, input_time: list[str] | None = None
) -> bool:
    for date in input_date or []:
        if date and not DATE_REGEX.match(date):
            raise ApiError(status.BAD_REQUEST, "Invalid date format. Use MM/DD/YYYY.")

    for time_value in input_time or []:
        if time_value and not TIME_REGEX.search(time_value):
            raise ApiError(status.BAD_REQUEST, "Invalid time format. Use HH:MM AM/PM.")

    return True
