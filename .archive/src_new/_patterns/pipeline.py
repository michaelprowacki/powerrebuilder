"""Pipeline Pattern - Orchestration of sequential processing stages.

This pattern handles the flow of data through the 5-stage pipeline,
managing inter-stage communication and data transformation.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, TypeVar, Union

PathLike = Union[str, Path]
T = TypeVar("T")


@dataclass
class StageResult:
    """Result from a pipeline stage."""

    stage: str
    success: bool
    input_path: str
    output_path: str
    files_processed: int = 0
    files_failed: int = 0
    duration: float = 0.0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    """Result from complete pipeline execution."""

    success: bool
    stages_completed: List[str] = field(default_factory=list)
    stages_failed: List[str] = field(default_factory=list)
    total_duration: float = 0.0
    stage_results: Dict[str, StageResult] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class PipelineStage(Protocol):
    """Protocol for pipeline stages."""

    @property
    def stage_name(self) -> str:
        """Get stage name."""
        ...

    def process(self) -> StageResult:
        """Process this stage."""
        ...


class Pipeline:
    """Orchestrates execution of sequential pipeline stages.

    This replaces the scattered pipeline logic found in:
    - main.py
    - Various coordinator implementations
    - UniversalCoordinator
    """

    def __init__(
        self,
        stages: List[PipelineStage],
        stop_on_error: bool = True,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize pipeline.

        Args:
            stages: List of stages to execute in order
            stop_on_error: Whether to stop if a stage fails
            logger: Logger instance
        """
        self.stages = stages
        self.stop_on_error = stop_on_error
        self.logger = logger or logging.getLogger(__name__)
        self._results = []

    def execute(self) -> PipelineResult:
        """Execute all pipeline stages in sequence.

        Returns:
            Pipeline execution result
        """
        start_time = time.time()
        result = PipelineResult(success=True)

        self.logger.info(f"Starting pipeline with {len(self.stages)} stages")

        for i, stage in enumerate(self.stages, 1):
            stage_name = stage.stage_name
            self.logger.info(f"[{i}/{len(self.stages)}] Starting stage: {stage_name}")

            try:
                # Execute stage
                stage_result = stage.process()

                # Record result
                result.stage_results[stage_name] = stage_result

                if stage_result.success:
                    result.stages_completed.append(stage_name)
                    self.logger.info(
                        f"Stage {stage_name} completed: "
                        f"{stage_result.files_processed} files in "
                        f"{stage_result.duration:.2f}s"
                    )
                else:
                    result.stages_failed.append(stage_name)
                    result.errors.extend(stage_result.errors)
                    self.logger.error(f"Stage {stage_name} failed")

                    if self.stop_on_error:
                        result.success = False
                        self.logger.error("Stopping pipeline due to stage failure")
                        break

            except Exception as e:
                # Handle stage exception
                error_msg = f"Stage {stage_name} raised exception: {e}"
                self.logger.exception(error_msg)
                result.stages_failed.append(stage_name)
                result.errors.append(error_msg)
                result.success = False

                if self.stop_on_error:
                    break

        # Calculate total duration
        result.total_duration = time.time() - start_time

        # Log summary
        self._log_summary(result)

        return result

    def _log_summary(self, result: PipelineResult) -> None:
        """Log pipeline execution summary.

        Args:
            result: Pipeline result
        """
        self.logger.info("=" * 60)
        self.logger.info("PIPELINE SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Status: {'SUCCESS' if result.success else 'FAILED'}")
        self.logger.info(f"Duration: {result.total_duration:.2f}s")
        self.logger.info(f"Stages completed: {len(result.stages_completed)}")
        self.logger.info(f"Stages failed: {len(result.stages_failed)}")

        if result.stages_completed:
            self.logger.info(f"Completed: {', '.join(result.stages_completed)}")

        if result.stages_failed:
            self.logger.error(f"Failed: {', '.join(result.stages_failed)}")

        # Detailed stage results
        total_files = 0
        total_failed = 0

        for stage_name, stage_result in result.stage_results.items():
            total_files += stage_result.files_processed
            total_failed += stage_result.files_failed

        self.logger.info(f"Total files processed: {total_files}")
        if total_failed > 0:
            self.logger.error(f"Total files failed: {total_failed}")

        if result.errors:
            self.logger.error(f"Total errors: {len(result.errors)}")
            for error in result.errors[:5]:  # Show first 5 errors
                self.logger.error(f"  - {error}")
            if len(result.errors) > 5:
                self.logger.error(f"  ... and {len(result.errors) - 5} more")

        self.logger.info("=" * 60)


class StageConnector:
    """Manages data flow between pipeline stages.

    Handles the transformation of output from one stage to input for the next.
    """

    def __init__(self, intermediate_dir: Optional[PathLike] = None):
        """Initialize connector.

        Args:
            intermediate_dir: Directory for intermediate files between stages
        """
        self.intermediate_dir = Path(intermediate_dir) if intermediate_dir else None

    def connect_stages(
        self, from_stage: str, to_stage: str, output_path: Path, pattern: str = "*"
    ) -> Path:
        """Connect output from one stage to input of another.

        Args:
            from_stage: Source stage name
            to_stage: Target stage name
            output_path: Output directory of source stage
            pattern: File pattern to pass forward

        Returns:
            Input path for target stage
        """
        # For now, simple pass-through
        # Can be extended to handle transformations
        return output_path

    def validate_stage_output(
        self, stage: str, output_path: Path, required_patterns: List[str]
    ) -> bool:
        """Validate that stage produced expected output.

        Args:
            stage: Stage name
            output_path: Stage output directory
            required_patterns: Expected file patterns

        Returns:
            True if valid
        """
        for pattern in required_patterns:
            files = list(output_path.glob(pattern))
            if not files:
                raise ValueError(
                    f"Stage {stage} did not produce required files matching {pattern}"
                )
        return True
