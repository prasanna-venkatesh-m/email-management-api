
import logging
import json
import sys


class JSONFormatter(logging.Formatter):

    def format(self, record):
        payload = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        event_data = getattr(record, "event_data", None)

        if event_data:
            payload.update(event_data)

        if record.exc_info:
            payload["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(payload, default=str)


def setup_logging():

    logger = logging.getLogger("email_management.llm")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    logger.addHandler(handler)
