"""Logger implementations for dependency injection.

This module provides concrete implementations of the ILogger interface.
"""

from typing import Any

from .interfaces import ILogger


class StandardLogger(ILogger):
    """Standard logger implementation wrapping Python's logging module."""

    def __init__(self, name: str) -> None:
        """Initialize standard logger.

        Args:
            name: Logger name
        """
        import logging

        self._logger = logging.getLogger(name)
        self._context: dict[str, Any] = {}

    def _log_with_context(
        self, level: int, msg: str, *args: Any, **kwargs: Any
    ) -> None:
        """Log message with context."""
        extra = kwargs.get("extra", {})
        extra.update(self._context)
        kwargs["extra"] = extra
        self._logger.log(level, msg, *args, **kwargs)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        import logging

        self._log_with_context(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        import logging

        self._log_with_context(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        import logging

        self._log_with_context(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        import logging

        self._log_with_context(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        import logging

        self._log_with_context(logging.CRITICAL, msg, *args, **kwargs)

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log an exception with traceback."""
        kwargs["exc_info"] = kwargs.get("exc_info", True)
        self.error(msg, *args, **kwargs)

    def set_context(self, **kwargs: Any) -> None:
        """Set persistent context fields for all subsequent logs."""
        self._context.update(kwargs)

    def clear_context(self) -> None:
        """Clear all context fields."""
        self._context.clear()


class DetailedLoggerAdapter(ILogger):
    """Adapter to make DetailedLogger conform to ILogger interface."""

    def __init__(self, detailed_logger: Any) -> None:
        """Initialize adapter.

        Args:
            detailed_logger: Instance of DetailedLogger from logging module
        """
        self._logger = detailed_logger

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        self._logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        self._logger.critical(msg, *args, **kwargs)

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log an exception with traceback."""
        self._logger.exception(msg, *args, **kwargs)

    def set_context(self, **kwargs: Any) -> None:
        """Set persistent context fields for all subsequent logs."""
        self._logger.set_context(**kwargs)

    def clear_context(self) -> None:
        """Clear all context fields."""
        self._logger.clear_context()
