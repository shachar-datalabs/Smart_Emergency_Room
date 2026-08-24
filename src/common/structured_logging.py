from __future__ import annotations

import json
import logging
from datetime import UTC, datetime


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format="%(message)s")


def log_event(logger: logging.Logger, component: str, event: str, **fields: object) -> None:
    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "component": component,
        "level": "INFO",
        "event": event,
        **fields,
    }
    logger.info(json.dumps(payload, sort_keys=True))
