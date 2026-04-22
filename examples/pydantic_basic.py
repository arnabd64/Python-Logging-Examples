"""
Name: Pydantic In-Memory Logs

Description:

- All the `LogRecord` objects stored on the RAM as a Pydantic Object
"""

from datetime import datetime
from logging import Formatter, Handler, LogRecord
from pathlib import Path
from typing import List, Dict, Any

from pydantic import BaseModel


class PydanticLogRecord(BaseModel):
    """
    Data Model to store logs

    Attributes:
        timestamp (datetime) : when the log was created
        loglevel (str) : INFO, DEBUG, ERROR, WARNING ...
        name (str) : Name of the logger
        module (str) : module/script where the event was recorded
        funcName (str) : Name of parent function
        lineno (int) : Line Number where logger was called
        message (str) : Log Message
    """

    timestamp: datetime
    loglevel: str
    name: str
    module: str
    funcName: str
    lineno: int
    message: str
    extra: Dict[str, Any]


class PydanticFormatter(Formatter):
    """
    Converts a Log Event object (`LogRecord`) into a Pydantic
    object
    """
    _RESERVED = frozenset({
        "name", "msg", "args", "levelname", "levelno", "pathname",
        "filename", "module", "exc_info", "exc_text", "stack_info",
        "lineno", "funcName", "created", "msecs", "relativeCreated",
        "thread", "threadName", "processName", "process", "message",
        "taskName",
    })

    def format(self, record: LogRecord) -> PydanticLogRecord:
        extra = {
            k: v for k, v in record.__dict__.items()
            if k not in self._RESERVED and not k.startswith("_")
        }
        return PydanticLogRecord(
            timestamp=datetime.fromtimestamp(record.created),
            loglevel=record.levelname,
            name=record.name,
            module=record.module,
            funcName=record.funcName,
            lineno=record.lineno,
            message=record.getMessage(),
            extra=extra
        )


class PydanticInMemoryHandler(Handler):
    """
    Stores all `LogRecord` as Pydantic objects in the RAM

    WARNING: If you are using this code make sure to dump
    the records into a file or a database
    """

    def __init__(self, level=0):
        self._store: List[PydanticLogRecord] = []
        super().__init__(level)

    @property
    def store(self) -> List[PydanticLogRecord]:
        return self._store

    def emit(self, record: LogRecord):
        self._store.append(self.format(record))


class JSONLinesHandler(Handler):
    """
    Dumps all `LogRecord` into a jsonl formatted where
    each line is a JSON log event
    """

    def __init__(self, filename: str | Path, level=0):
        super().__init__(level)

        self.filename = Path(filename)

        if self.filename.is_dir():
            raise ValueError(f"{filename} is a directory")

        if not self.filename.exists():
            self.filename.parent.mkdir(parents=True, exist_ok=True)
            self.filename.touch()

    def emit(self, record: LogRecord):
        log = self.format(record)

        if not isinstance(log, PydanticLogRecord):
            raise ValueError("Formatted LogRecord is not a Pydantic Model")

        with self.filename.open("a", encoding="utf-8") as f:
            f.write(log.model_dump_json() + "\n")


if __name__ == "__main__":
    import logging

    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)

    handler = PydanticInMemoryHandler()
    handler.setFormatter(PydanticFormatter())
    logger.addHandler(handler)

    logger.info("Application started successfully", extra={"app.name": "Test Logger", "app.version": 1})
    logger.warning("Low memory detected: 85% usage")
    logger.error("Failed to connect to database: timeout after 30s", extra={"db.url": "sqlite:///app.log"})

    for log in handler.store:
        print(log.model_dump_json(indent=2))

    """
    {
        "timestamp": "2026-04-21T10:42:09.007298",
        "loglevel": "INFO",
        "name": "test_logger",
        "module": "pydantic_inmem",
        "funcName": "<module>",
        "lineno": 78,
        "message": "Application started successfully"
    }
    {
        "timestamp": "2026-04-21T10:42:09.007372",
        "loglevel": "WARNING",
        "name": "test_logger",
        "module": "pydantic_inmem",
        "funcName": "<module>",
        "lineno": 79,
        "message": "Low memory detected: 85% usage"
    }
    {
        "timestamp": "2026-04-21T10:42:09.007400",
        "loglevel": "ERROR",
        "name": "test_logger",
        "module": "pydantic_inmem",
        "funcName": "<module>",
        "lineno": 80,
        "message": "Failed to connect to database: timeout after 30s"
    }
    """

    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)

    handler = JSONLinesHandler("logs/app.jsonl")
    handler.setFormatter(PydanticFormatter())
    logger.addHandler(handler)

    logger.info("Application started successfully", extra={"app.name": "Test Logger", "app.version": 1})
    logger.warning("Low memory detected: 85% usage")
    logger.error("Failed to connect to database: timeout after 30s", extra={"db.url": "sqlite:///app.log"})
