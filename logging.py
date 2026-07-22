"""
Structured logging configuration. Call `setup_logging()` once at app startup.
Every module should do `logger = logging.getLogger(__name__)` and log through that.
"""
import logging
import sys

from app.core.config import settings


class RequestIdFilter(logging.Filter):
    """Placeholder filter so request_id can be injected by middleware later."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


def setup_logging() -> None:
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | req=%(request_id)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Quiet down noisy third-party loggers in production
    if settings.is_production:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
