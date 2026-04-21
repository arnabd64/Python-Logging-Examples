import json
import logging
from typing import Dict


class DictFormatter(logging.Formatter):
    """
    Converts a `LogRecord` into a python
    dict object.
    """

    def _convert(self, record: logging.LogRecord) -> Dict:
        return {
            "asctime": self.formatTime(record, self.datefmt),
            "level": record.levelname,  # INFO, ERROR, WARNING
            "module": record.module,  # name of module or py-file
            "funcName": record.funcName,  # name of function
            "lineno": record.lineno,  # line number where logger is called
            "name": record.name,  # logger name
            "message": record.getMessage(),
        }

    def format(self, record: logging.LogRecord) -> Dict:
        return self._convert(record)


class JSONFormatter(DictFormatter):
    """
    Converts a `LogRecord` into a JSON string using
    the DictFormatter
    """

    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(self._convert(record))



if __name__ == '__main__':
    import logging

    json_logger = logging.getLogger("json_logger")
    json_logger.setLevel(logging.DEBUG)
    json_handler = logging.StreamHandler()
    json_handler.setFormatter(JSONFormatter())
    json_logger.addHandler(json_handler)

    json_logger.info("This is an info message")
    json_logger.warning("This is a warning message")
    json_logger.error("This is an error message")
