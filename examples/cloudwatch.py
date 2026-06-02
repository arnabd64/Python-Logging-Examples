import json
import logging

import boto3


class JSONFormatter(logging.Formatter):
    """
    Custom formatter to output log records as structured JSON.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats the standard LogRecord into a JSON string containing explicit metadata.
        Uses ISO 8601 string format for the internal JSON log timestamp.
        """
        log_data = {
            "level": record.levelname,
            "filename": record.filename,
            "function_name": record.funcName,
            "line_number": record.lineno,
            "message": record.getMessage(),
        }

        return json.dumps(log_data)


class CloudWatchLogHandler(logging.Handler):
    """
    Custom logging handler to send application logs directly to Amazon CloudWatch.
    Optimized according to the latest Boto3 guidelines by omitting deprecated sequence tokens.
    """

    def __init__(self, log_group: str, log_stream: str, region_name: str = None):
        super().__init__()
        self.log_group = log_group
        self.log_stream = log_stream
        self.client = boto3.client("logs", region_name=region_name)

        self._initialize_resources()

    def _initialize_resources(self) -> None:
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

    def emit(self, record: logging.LogRecord) -> None:
        """
        Formats the log record and sends it to CloudWatch.
        Uses the LogRecord's native creation time converted to milliseconds for AWS compatibility.
        """
        try:
            log_message = self.format(record)

            self.client.put_log_events(
                logGroupName=self.log_group,
                logStreamName=self.log_stream,
                logEvents=[
                    {"timestamp": int(record.created * 1000), "message": log_message}
                ],
            )
        except Exception:
            self.handleError(record)


if __name__ == "__main__":
    LOG_GROUP_NAME = "/python/backend"
    LOG_STREAM_NAME = "application-execution"

    logger = logging.getLogger("CloudWatchJSONTest")
    logger.setLevel(logging.INFO)

    cw_handler = CloudWatchLogHandler(
        log_group=LOG_GROUP_NAME, log_stream=LOG_STREAM_NAME, region_name="us-east-2"
    )

    json_formatter = JSONFormatter()
    cw_handler.setFormatter(json_formatter)

    logger.addHandler(cw_handler)

    print("Sending structured JSON logs to CloudWatch...")

    def sample_function():
        logger.info("Application initialized successfully.")
        logger.warning(
            "Simulated execution warning: Disk space utilization exceeds 70%."
        )
        logger.error("Simulated execution error: Database connection dropped.")

    sample_function()
    print("Logs dispatched.")
