

import json
from app.core.config import settings
from pathlib import Path
import logging
import sys

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


class LoggingManager:
    def __init__(self, log_file: str = settings.LOG_FILE, log_directory: str | None = None):

        # Initialize logger
        self.logger = logging.getLogger("youtube_rag_chatbot")
        self.logger.setLevel(settings.LOG_LEVEL)
        self.logger.propagate = False

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        # Prepare log file path
        log_path = Path(log_file)

        if log_directory:
            log_path = Path(log_directory) / log_path.name

        # Create parent directories
        log_path.parent.mkdir(parents=True, exist_ok=True)


        # formatter = JSONFormatter()
        if settings.LOG_FORMAT.lower() == "json":
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(settings.LOG_LEVEL)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(settings.LOG_LEVEL)
        self.logger.addHandler(stream_handler)
        self.logger.addHandler(file_handler)

    def get_logger(self):
        return self.logger


logging_manager = LoggingManager(log_file=settings.LOG_FILE)
logger = logging_manager.get_logger()
