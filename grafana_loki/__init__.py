import enum
import logging
import queue
from logging.handlers import QueueHandler, QueueListener

import urllib3


class AllowedKeywords(enum.Enum):
    REQUEST_ID = "request_id"
    ENVIRONMENT = "environment"
    USER_ID = "user_id"
    SESSION_ID = "session_id"


class LokiHandler(logging.Handler):
    def __init__(self, base_url: str, labels: dict | None = None) -> None:
        super().__init__(level=0)
        self._url = f"{base_url}/loki/api/v1/push"
        self.client = urllib3.PoolManager()
        self.labels = labels or {}

    def emit(self, record: logging.LogRecord) -> None:
        # metadata
        labels = {
            **self.labels,
            "module": record.module,
            "function": record.funcName,
            "level": record.levelname.lower(),
        }

        # Add only allowed keys supplied through extra=
        for key in AllowedKeywords:
            if key.value in record.__dict__:
                labels[key.value] = str(record.__dict__[key.value])

        # payload
        payload = {
            "streams": [
                {
                    "stream": labels,
                    "values": [[str(int(record.created * 1e9)), record.getMessage()]],
                }
            ]
        }

        # forward log to loki server
        try:
            response = self.client.request(
                "POST", self._url, json=payload, timeout=urllib3.Timeout()
            )

            if response.status >= 300:
                self.handleError(record)

        except:
            self.handleError(record)

    def close(self) -> None:
        try:
            self.client.clear()

        finally:
            return super().close()


def get_logger(labels: dict = {}):
    # initiate logger
    logger = logging.getLogger("loki-logger")

    # add handler
    handler = LokiHandler(base_url="http://localhost:3100", labels=labels)
    handler.setLevel(logging.INFO)

    # add handler to logger
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger


def get_async_compatible_logger(labels: dict[str, str] = {}):
    # initiate logger
    logger = logging.getLogger("loki-logger")

    # add loki handler
    handler = LokiHandler(base_url="http://localhost:3100", labels=labels)
    handler.setLevel(logging.INFO)

    # add Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter(r"%(asctime)s %(levelname)8s - %(message)s")
    )
    logger.addHandler(console_handler)

    # add handler to logger
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # define queue
    log_queue = queue.Queue()
    listener = QueueListener(log_queue, handler)
    queue_handler = QueueHandler(log_queue)

    # add queue handler to logger
    logger.addHandler(queue_handler)

    return logger, listener


# Standard Logging
# if __name__ == "__main__":
#     logger = get_logger({"service_name": "test-app"})
#     _extras = {"user_id": "arnabd64", "session_id": "sync"}

#     logger.info("This is a Info message", extra=_extras)
#     logger.warning("This is a Warning Message", extra=_extras)
#     logger.error("This is an error message", extra=_extras)

# Async compatibnle logging
if __name__ == "__main__":
    logger, listener = get_async_compatible_logger(
        labels={"service_name": "test-app"},
    )

    listener.start()

    try:
        extras = {
            "user_id": "arnabd64",
            "session_id": "async",
        }

        logger.info("This is an info message", extra=extras)
        logger.warning("This is a warning message", extra=extras)
        logger.error("This is an error message", extra=extras)

    finally:
        listener.stop()
        logging.getLogger("loki-logger").handlers.clear()
