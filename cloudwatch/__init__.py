import enum
import json
import logging

import boto3


class AllowedExtras(enum.Enum):
    USER_ID = "user_id"
    SESSION_ID = "session_id"
    ENVIRONMENT = "environment"


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "level": record.levelname.upper(),
            "module": record.module,
            "function": record.funcName,
            "message": record.getMessage(),
        }

        for key in AllowedExtras:
            if key.value in record.__dict__:
                log_data[key.value] = str(record.__dict__[key.value])

        return json.dumps(log_data)


class CloudWatchHandler(logging.Handler):
    def __init__(
        self,
        log_group: str,
        log_stream: str,
        region_name: str,
        labels: dict[str, str] = {},
        level=0,
    ) -> None:
        super().__init__(level)

        # AWS Client
        self.client = boto3.client("logs", region_name=region_name)

        # CloudWatch settings
        self.log_group = log_group
        self.log_stream = log_stream

        # add labels
        self.labels = labels

        self._initialize_cloudwatch()

    def _initialize_cloudwatch(self) -> None:
        """Creates the log group and stream if they do not exist."""
        try:
            self.client.create_log_group(logGroupName=self.log_group)
        except self.client.exceptions.ResourceAlreadyExistsException:
            pass

        try:
            self.client.create_log_stream(
                logGroupName=self.log_group, logStreamName=self.log_stream
            )
        except self.client.exceptions.ResourceAlreadyExistsException:
            pass

    def emit(self, record: logging.LogRecord):
        # build JSON
        log_event = {
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            **self.labels,
        }

        # Add
        try:
            log_event = self.format(record)

            self.client.put_log_events(
                logGroupName=self.log_group,
                logStreamName=self.log_stream,
                logEvents=[
                    {"timestamp": int(record.created * 1000), "message": log_event}
                ],
            )

        except Exception:
            self.handleError(record)
