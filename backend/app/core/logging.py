"""
Centralised structlog configuration.

Call configure_logging() once at startup (in main.py lifespan).
Every module then does:

    import structlog
    logger = structlog.get_logger(__name__)
"""

import logging
import sys

import structlog
from structlog.contextvars import merge_contextvars

from app.core.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    dev = settings.DEBUG

    shared_processors: list = [
        merge_contextvars,                           # pulls request_id / user_id bound per-request
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
    ]

    if dev:
        # Pretty coloured output for local development
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        # Machine-readable JSON for production / log aggregators
        shared_processors.append(structlog.processors.format_exc_info)
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if dev else logging.INFO
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Silence noisy third-party loggers
    for name in ("uvicorn.access", "sqlalchemy.engine", "httpx"):
        logging.getLogger(name).setLevel(logging.WARNING)
