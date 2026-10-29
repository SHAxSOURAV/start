import hashlib


def hash_token(token: str) -> str:
    """Return SHA-256 hash of a JWT string to avoid plaintext token persistence."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def parse_user_agent(user_agent: str | None) -> str:
    """Extract human-readable device and browser representation from User-Agent string."""
    if not user_agent:
        return "Unknown Device"

    ua = user_agent.lower()

    # Operating System Detection
    if "windows" in ua:
        os_name = "Windows"
    elif "iphone" in ua:
        os_name = "iPhone"
    elif "ipad" in ua:
        os_name = "iPad"
    elif "macintosh" in ua or "mac os" in ua:
        os_name = "macOS"
    elif "android" in ua:
        os_name = "Android"
    elif "linux" in ua:
        os_name = "Linux"
    else:
        os_name = "Unknown OS"

    # Client / Browser Detection
    if "postman" in ua:
        client = "Postman"
    elif "edg/" in ua:
        client = "Edge"
    elif "opr/" in ua or "opera" in ua:
        client = "Opera"
    elif "chrome/" in ua or "crios/" in ua:
        client = "Chrome"
    elif "firefox/" in ua or "fxios/" in ua:
        client = "Firefox"
    elif "safari/" in ua:
        client = "Safari"
    else:
        client = "Browser"

    return f"{client} on {os_name}"
