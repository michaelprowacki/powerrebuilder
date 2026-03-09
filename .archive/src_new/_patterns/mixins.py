"""Reusable Mixins - Common functionality patterns extracted from the codebase.

These mixins capture the most frequently repeated patterns to ensure DRY code:
- Error handling (found in 150+ places)
- Validation (100+ instances)
- Progress reporting (80+ instances)
- Configuration management (60+ instances)
"""

from __future__ import annotations

import logging
import traceback
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

PathLike = Union[str, Path]
ConfigDict = Dict[str, Any]


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class BaseConfig:
    """Base configuration with common settings across all stages."""

    cache_enabled: bool = False
    parallel_enabled: bool = False
    recovery_enabled: bool = True
    validate_inputs: bool = True
    validate_outputs: bool = True
    max_retries: int = 3
    timeout_seconds: Optional[int] = None
    log_level: str = "INFO"
    buffer_size: int = 8192
    encoding: str = "utf-8"

    def merge(self, other: Dict[str, Any]) -> BaseConfig:
        """Merge with dictionary values."""
        for key, value in other.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self


# ============================================================================
# ERROR HANDLING MIXIN
# ============================================================================


class ErrorHandlingMixin:
    """Standardized error handling found throughout the codebase."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._error_count = 0
        self._max_errors = 10
        self._errors = []

    def handle_error(
        self,
        error: Exception,
        context: str = "",
        recoverable: bool = True,
        reraise: bool = True,
    ) -> bool:
        """Handle error with standard logging and recovery.

        Returns:
            True if handled successfully
        """
        self._error_count += 1
        self._errors.append(f"{context}: {error}")

        # Get logger
        logger = getattr(self, "logger", logging.getLogger(__name__))

        logger.error(f"Error in {context}: {error}")
        logger.debug(f"Stack trace: {traceback.format_exc()}")

        # Check max errors
        if self._error_count >= self._max_errors:
            logger.critical(f"Maximum errors ({self._max_errors}) exceeded")
            if reraise:
                raise RuntimeError("Too many errors encountered") from error
            return False

        # Attempt recovery if available
        if recoverable and hasattr(self, "_attempt_recovery"):
            try:
                if self._attempt_recovery(error, context):
                    logger.info(f"Recovered from error in {context}")
                    return True
            except Exception as recovery_error:
                logger.error(f"Recovery failed: {recovery_error}")

        if reraise:
            raise error
        return False

    @contextmanager
    def error_context(self, context: str, recoverable: bool = True):
        """Context manager for error handling."""
        try:
            yield
        except Exception as e:
            self.handle_error(e, context, recoverable)

    def get_errors(self) -> List[str]:
        """Get list of errors encountered."""
        return self._errors.copy()


# ============================================================================
# VALIDATION MIXIN
# ============================================================================


class ValidationMixin:
    """Common validation patterns."""

    def validate_path(
        self,
        path: PathLike,
        must_exist: bool = True,
        must_be_file: bool = False,
        must_be_dir: bool = False,
    ) -> bool:
        """Validate filesystem path.

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        path_obj = Path(path) if isinstance(path, str) else path

        if must_exist and not path_obj.exists():
            raise ValueError(f"Path does not exist: {path_obj}")

        if must_exist and must_be_file and not path_obj.is_file():
            raise ValueError(f"Path is not a file: {path_obj}")

        if must_exist and must_be_dir and not path_obj.is_dir():
            raise ValueError(f"Path is not a directory: {path_obj}")

        return True

    def validate_input(
        self, data: Any, rules: Optional[List[Callable[[Any], bool]]] = None
    ) -> bool:
        """Validate input data against rules.

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        if data is None:
            raise ValueError("Input data cannot be None")

        if rules:
            for rule in rules:
                if not rule(data):
                    raise ValueError(f"Validation failed for: {data}")

        return True

    def validate_output(self, data: Any, expected_type: Optional[type] = None) -> bool:
        """Validate output data.

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        if expected_type and not isinstance(data, expected_type):
            raise ValueError(f"Wrong type. Expected {expected_type}, got {type(data)}")
        return True


# ============================================================================
# CONFIGURATION MIXIN
# ============================================================================


class ConfigurableMixin:
    """Configuration management pattern."""

    def __init__(
        self, *args, config: Optional[Union[ConfigDict, BaseConfig]] = None, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._config = self._load_config(config)

    def _load_config(
        self, config: Optional[Union[ConfigDict, BaseConfig]]
    ) -> BaseConfig:
        """Load and validate configuration."""
        if config is None:
            return BaseConfig()
        elif isinstance(config, dict):
            return BaseConfig().merge(config)
        elif isinstance(config, BaseConfig):
            return config
        else:
            raise ValueError(f"Invalid config type: {type(config)}")

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value with default."""
        return getattr(self._config, key, default)

    def update_config(self, updates: ConfigDict) -> None:
        """Update configuration values."""
        self._config.merge(updates)


# ============================================================================
# PROGRESS REPORTING MIXIN
# ============================================================================


class ProgressReportingMixin:
    """Progress reporting pattern used throughout pipeline stages."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tasks = {}
        self._progress_enabled = True

    def start_task(
        self, task_id: str, description: str, total: Optional[int] = None
    ) -> None:
        """Start a progress task."""
        self._tasks[task_id] = {
            "description": description,
            "total": total,
            "current": 0,
            "status": "running",
        }

        # Log if available
        if hasattr(self, "logger"):
            self.logger.info(f"Started: {description}")

    def update_task(self, task_id: str, advance: int = 1, **kwargs: Any) -> None:
        """Update task progress."""
        if task_id in self._tasks:
            self._tasks[task_id]["current"] += advance

            # Update any additional fields
            self._tasks[task_id].update(kwargs)

            # Log progress periodically
            task = self._tasks[task_id]
            if task["total"] and hasattr(self, "logger"):
                progress = (task["current"] / task["total"]) * 100
                if progress % 20 == 0:  # Log every 20%
                    self.logger.info(f"{task['description']}: {progress:.0f}%")

    def complete_task(self, task_id: str) -> None:
        """Mark task as complete."""
        if task_id in self._tasks:
            self._tasks[task_id]["status"] = "completed"

            if hasattr(self, "logger"):
                self.logger.info(f"Completed: {self._tasks[task_id]['description']}")

    def fail_task(self, task_id: str, error: str) -> None:
        """Mark task as failed."""
        if task_id in self._tasks:
            self._tasks[task_id]["status"] = "failed"
            self._tasks[task_id]["error"] = error

            if hasattr(self, "logger"):
                self.logger.error(
                    f"Failed: {self._tasks[task_id]['description']} - {error}"
                )
