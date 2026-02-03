"""Base Coordinator Pattern - Abstract base for all pipeline coordinators.

This provides the common pattern that all 5 pipeline stages follow:
- Input/output management
- Configuration handling
- Error handling
- Progress reporting
- Validation
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .mixins import (
    ConfigurableMixin,
    ErrorHandlingMixin,
    ProgressReportingMixin,
    ValidationMixin,
)

PathLike = Union[str, Path]


@dataclass
class CoordinatorResult:
    """Standard result from any coordinator."""

    success: bool
    stage: str
    input_path: str
    output_path: str
    files_processed: int = 0
    files_failed: int = 0
    errors: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    duration: float = 0.0


class BaseCoordinator(
    ABC,
    ErrorHandlingMixin,
    ValidationMixin,
    ConfigurableMixin,
    ProgressReportingMixin,
):
    """Abstract base coordinator for all pipeline stages.

    This class encapsulates the common pattern found across all coordinators:
    1. Validate inputs
    2. Process files (abstract method for each stage)
    3. Handle errors consistently
    4. Report progress
    5. Return standard results
    """

    def __init__(
        self,
        input_path: PathLike,
        output_path: PathLike,
        config: Optional[Dict[str, Any]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize coordinator with common setup.

        Args:
            input_path: Input file or directory path
            output_path: Output directory path
            config: Stage-specific configuration
            logger: Logger instance
        """
        super().__init__(config=config)
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self._start_time = None
        self._result = None

    @property
    @abstractmethod
    def stage_name(self) -> str:
        """Return the name of this pipeline stage."""
        pass

    @abstractmethod
    def process_file(self, input_file: Path, output_dir: Path) -> bool:
        """Process a single file - must be implemented by each stage.

        Args:
            input_file: Path to input file
            output_dir: Directory for output

        Returns:
            True if successful, False otherwise
        """
        pass

    def validate_inputs(self) -> None:
        """Validate coordinator inputs before processing."""
        self.validate_path(self.input_path, must_exist=True)

        # Create output directory if needed
        self.output_path.mkdir(parents=True, exist_ok=True)

        self.logger.info(
            f"{self.stage_name} coordinator initialized: {self.input_path} -> {self.output_path}"
        )

    def discover_files(self) -> list[Path]:
        """Discover files to process based on input path.

        Returns:
            List of file paths to process
        """
        if self.input_path.is_file():
            return [self.input_path]
        elif self.input_path.is_dir():
            # Each stage should override with appropriate file patterns
            return list(self.input_path.rglob("*"))
        else:
            raise ValueError(f"Invalid input path: {self.input_path}")

    def process(self) -> CoordinatorResult:
        """Main processing pipeline - common pattern for all stages.

        Returns:
            Standardized result object
        """
        self._start_time = time.time()
        self._result = CoordinatorResult(
            success=False,
            stage=self.stage_name,
            input_path=str(self.input_path),
            output_path=str(self.output_path),
        )

        try:
            # Step 1: Validate inputs
            self.validate_inputs()

            # Step 2: Discover files to process
            files = self.discover_files()
            self.logger.info(f"Found {len(files)} files to process")

            # Step 3: Start progress tracking
            self.start_task("main", f"Processing {self.stage_name}", total=len(files))

            # Step 4: Process each file
            for file_path in files:
                try:
                    if self.process_file(file_path, self.output_path):
                        self._result.files_processed += 1
                    else:
                        self._result.files_failed += 1
                        self._result.errors.append(f"Failed: {file_path}")

                    self.update_task("main", advance=1)

                except Exception as e:
                    self._result.files_failed += 1
                    error_msg = f"Error processing {file_path}: {e}"
                    self._result.errors.append(error_msg)
                    self.handle_error(
                        e, str(file_path), recoverable=True, reraise=False
                    )

            # Step 5: Complete and calculate metrics
            self.complete_task("main")
            self._result.success = self._result.files_failed == 0
            self._result.duration = time.time() - self._start_time

            # Log summary
            self.logger.info(
                f"{self.stage_name} complete: {self._result.files_processed} processed, "
                f"{self._result.files_failed} failed in {self._result.duration:.2f}s"
            )

        except Exception as e:
            self._result.success = False
            self._result.errors.append(str(e))
            self.fail_task("main", str(e))
            self.handle_error(
                e, f"{self.stage_name} process", recoverable=False, reraise=True
            )

        return self._result

    def get_file_pattern(self) -> str:
        """Get the file pattern for this stage - override in subclasses.

        Returns:
            Glob pattern for files this stage processes
        """
        return "*"
