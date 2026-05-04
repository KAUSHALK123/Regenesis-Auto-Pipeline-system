"""
Logging module for the Regenesis Auto Pipeline System.

Provides a configured logger for consistent logging throughout the application
with support for console and file output.
"""

import logging
import sys
from pathlib import Path


class LoggerSetup:
    """Setup and configure logging for the application."""

    _logger = None

    @classmethod
    def get_logger(cls, name: str = __name__) -> logging.Logger:
        """
        Get or create a configured logger instance.

        Args:
            name: The name of the logger (typically __name__).

        Returns:
            logging.Logger: Configured logger instance.
        """
        if cls._logger is None:
            cls._logger = cls._configure_logger(name)
        return cls._logger

    @staticmethod
    def _configure_logger(name: str) -> logging.Logger:
        """
        Configure and return a logger instance.

        Args:
            name: The name of the logger.

        Returns:
            logging.Logger: Configured logger instance.
        """
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)

        # Avoid duplicate handlers if logger is already configured
        if logger.handlers:
            return logger

        # Create logs directory if it doesn't exist
        logs_dir = Path(__file__).parent.parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # File handler
        file_handler = logging.FileHandler(logs_dir / "app.log")
        file_handler.setLevel(logging.DEBUG)

        # Formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # Add handlers to logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        return logger


# Export a default logger instance
logger = LoggerSetup.get_logger(__name__)


if __name__ == "__main__":
    # Quick test to verify logging works
    logger.info("[OK] Logger initialized successfully")
    logger.error("This is a test error message")
