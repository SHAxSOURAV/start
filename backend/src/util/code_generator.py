import random
import time


def code_generator(minutes: int) -> tuple[str, float]:
    """Returns a 6-digit code and its expiry as an epoch timestamp in ms."""
    code = str(random.randint(100000, 999999))
    expired_at = time.time() * 1000 + minutes * 60 * 1000
    return code, expired_at
