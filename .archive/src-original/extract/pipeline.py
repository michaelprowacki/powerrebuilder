"""Pipeline integration example for the refactored ExtractCoordinator.

This module shows how to integrate the new ExtractCoordinator into the
existing pipeline infrastructure.
"""

from pathlib import Path
from typing import cast

from src.contracts.types import ExtractionStatsDict
from src.extract.coordinator import ExtractCoordinator
from src.extract.factory import ExtractCoordinatorFactory, create_extract_coordinator


def create_coordinator_for_pipeline(
    input_path: str | Path,
    output_path: str | Path,
    enable_byte_recovery: bool = False,
    extract_resources: bool = True,
    show_progress: bool = True,
) -> ExtractCoordinator:
    """Create an ExtractCoordinator for pipeline usage.

    This function provides a simple interface for the pipeline to create
    a properly configured ExtractCoordinator.

    Args:
        input_path: Input file or directory
        output_path: Output directory
        enable_byte_recovery: Enable byte-level recovery
        extract_resources: Extract embedded resources
        show_progress: Show progress information

    Returns:
        Configured ExtractCoordinator
    """
    # Use the factory to create a coordinator with default components
    return cast(
        ExtractCoordinator,
        ExtractCoordinatorFactory.create_simple(
            input_path=input_path,
            output_path=output_path,
            enable_byte_recovery=enable_byte_recovery,
            extract_resources=extract_resources,
            show_progress=show_progress,
        ),
    )


# For backward compatibility with existing pipeline code
class LegacyExtractCoordinator:
    """Wrapper to provide backward compatibility with the old ExtractCoordinator API.

    This class wraps the new refactored coordinator to maintain compatibility
    with existing pipeline code that expects the old API.
    """

    def __init__(
        self,
        input_path: str | Path,
        output_dir: str | Path,
        enable_byte_recovery: bool = False,
        extract_resources: bool = True,
        show_progress: bool = True,
    ) -> None:
        """Initialize with old-style parameters.

        Args:
            input_path: Input file or directory
            output_dir: Output directory (note: was output_dir in old API)
            enable_byte_recovery: Enable byte-level recovery
            extract_resources: Extract embedded resources
            show_progress: Show progress information
        """
        # Create the new coordinator using factory
        self._coordinator = create_extract_coordinator(
            input_path=input_path,
            output_path=output_dir,  # Map output_dir to output_path
            enable_byte_recovery=enable_byte_recovery,
            extract_resources=extract_resources,
            show_progress=show_progress,
        )

        # Store attributes for compatibility
        self.input_path = self._coordinator.input_path
        self.output_dir = self._coordinator.output_path
        self.enable_byte_recovery = enable_byte_recovery
        self.extract_resources = extract_resources
        self.show_progress = show_progress

    def extract(self) -> ExtractionStatsDict:
        """Extract files using old method name.

        Returns:
            Extraction statistics
        """
        return cast(ExtractionStatsDict, self._coordinator.process())

    def process(self) -> ExtractionStatsDict:
        """Process extraction (delegates to new coordinator).

        Returns:
            Extraction statistics
        """
        return cast(ExtractionStatsDict, self._coordinator.process())

    def extract_single_file(
        self, file_path: str | Path, output_dir: str | Path | None = None
    ) -> bool:
        """Extract a single file.

        Args:
            file_path: Path to file
            output_dir: Output directory

        Returns:
            True if successful
        """
        return cast(bool, self._coordinator.extract_single_file(file_path, output_dir))

    def get_statistics(self) -> ExtractionStatsDict:
        """Get extraction statistics.

        Returns:
            Statistics dictionary
        """
        return cast(ExtractionStatsDict, self._coordinator.get_statistics())

    def validate_inputs(self) -> bool:
        """Validate inputs.

        Returns:
            True if valid
        """
        return cast(bool, self._coordinator.validate_inputs())


# Example of how to update the main pipeline
def example_pipeline_update() -> None:
    """Example showing how to update pipeline code."""
    # Old way (still works with LegacyExtractCoordinator)
    old_coordinator = LegacyExtractCoordinator(
        input_path="data/input", output_dir="data/output", enable_byte_recovery=True
    )
    old_result = old_coordinator.extract()

    # New way (recommended)
    new_coordinator = create_coordinator_for_pipeline(
        input_path="data/input", output_path="data/output", enable_byte_recovery=True
    )
    new_result = new_coordinator.process()

    # Both produce the same results
    assert old_result.keys() == new_result.keys()


# Drop-in replacement function for minimal code changes
def ExtractCoordinator(
    input_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    **kwargs,
) -> ExtractCoordinator | LegacyExtractCoordinator:
    """Factory function that mimics the old ExtractCoordinator constructor.

    This allows existing code to work with minimal changes:

    Old code:
        from src.extract.coordinator import ExtractCoordinator
        coord = ExtractCoordinator(input_path, output_dir)

    New code (no change needed if using this function):
        from src.extract.pipeline import ExtractCoordinator
        coord = ExtractCoordinator(input_path, output_dir)

    Args:
        input_path: Input path
        output_dir: Output directory
        **kwargs: Additional options

    Returns:
        ExtractCoordinator instance
    """
    # Check if using old-style parameters
    if output_dir is not None:
        # Old-style call, use legacy wrapper
        return LegacyExtractCoordinator(
            input_path=input_path, output_dir=output_dir, **kwargs
        )
    # New-style call or no parameters
    return cast(
        ExtractCoordinator,
        create_extract_coordinator(
            input_path=input_path, output_path=kwargs.get("output_path"), **kwargs
        ),
    )
