import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

LABEL = "Mount Fuji"

LOG_DIR = Path.cwd() / "logs" / "winston"


class MyFormatter(logging.Formatter):
    """`Tue Sep 09 2025 18:5:3 [Mount Fuji] info: message`"""

    def format(self, record: logging.LogRecord) -> str:
        date = datetime.fromtimestamp(record.created)
        stamp = date.strftime("%a %b %d %Y")
        h, m, s = date.hour, date.minute, date.second
        level = record.levelname.lower()
        return f"{stamp} {h}:{m}:{s} [{LABEL}] {level}: {record.getMessage()}"


def _build(name: str, level: int, files: list[tuple[Path, bool]]) -> logging.Logger:
    log = logging.getLogger(name)
    log.setLevel(level)
    log.propagate = False

    if log.handlers:
        return log

    formatter = MyFormatter()

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    log.addHandler(console)

    for path, rotate in files:
        path.parent.mkdir(parents=True, exist_ok=True)
        handler: logging.Handler
        if rotate:
            # winston-daily-rotate-file equivalent: hourly rotation, 14 days kept
            handler = TimedRotatingFileHandler(
                path, when="H", interval=1, backupCount=14 * 24, encoding="utf-8"
            )
        else:
            handler = logging.FileHandler(path, encoding="utf-8")
        handler.setLevel(level)
        handler.setFormatter(formatter)
        log.addHandler(handler)

    return log


# Logger for general information
logger = _build(
    "app",
    logging.INFO,
    [
        (LOG_DIR / "successes" / "um-success.log", False),
        (LOG_DIR / "successes" / "um-rotate-success.log", True),
    ],
)

# Logger for errors
error_logger = _build(
    "app.error",
    logging.ERROR,
    [(LOG_DIR / "errors" / "um-error.log", True)],
)
