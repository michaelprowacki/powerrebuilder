"""Coordination layer for PowerRebuilder pipeline stages."""

from pathlib import Path

from src.adapters.coordinators.powerbuilder_coordinator import (
    PowerBuilderCoordinator,
    PowerBuilderParseCoordinator,
)
from src.domain.models import PipelineStage
from src.infrastructure.container import create_container


class UniversalCoordinator:
    """Universal coordinator that orchestrates the entire pipeline using DI."""

    def __init__(
        self, stage: PipelineStage, input_dir: str, output_dir: str, config: dict = None
    ):
        """Initialize the universal coordinator.

        Args:
            stage: The pipeline stage(s) to execute
            input_dir: Input directory path
            output_dir: Output directory path
            config: Optional configuration dictionary
        """
        self.stage = stage
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.config = config or {}

        # Create DI container with configuration
        self.container = create_container(
            log_level=self.config.get("log_level", "INFO"),
            show_progress=self.config.get("show_progress", True),
            cache_enabled=self.config.get("cache_enabled", True),
            debug_mode=self.config.get("debug_mode", False),
            verbose=self.config.get("verbose", False),
        )

        # Create pipeline coordinator
        self.pipeline_coordinator = self.container.create_pipeline_coordinator()

    def process(self) -> dict:
        """Process the pipeline stage(s).

        Returns:
            Dictionary with processing results
        """
        # Determine which stages to run
        if self.stage == PipelineStage.ALL:
            # Run all stages in sequence
            stages = [
                PipelineStage.EXTRACT,
                PipelineStage.DECOMPILE,
                PipelineStage.PARSE,
                PipelineStage.MODEL,
                PipelineStage.GENERATE,
            ]
        else:
            # Run single stage
            stages = [self.stage]

        # Get target platform from config
        target = self.config.get("generate", {}).get("target", "flutter")

        # Run the pipeline
        result = self.pipeline_coordinator.run_pipeline_sync(
            stages=stages,
            input_path=self.input_dir,
            output_path=self.output_dir,
            target=target,
        )

        return result


def create_extract_coordinator(
    input_path: Path, output_dir: Path, recovery_enabled: bool = True
):
    """Create an extract coordinator."""
    return PowerBuilderCoordinator(
        input_dir=str(input_path), output_dir=str(output_dir)
    )


def create_decompile_coordinator(
    input_dir: Path,
    output_dir: str,
    parallel_enabled: bool = False,
    cache_enabled: bool = True,
    max_workers: int | None = None,
):
    """Create a decompile coordinator."""
    return PowerBuilderCoordinator(input_dir=str(input_dir), output_dir=output_dir)


def create_parse_coordinator(input_dir: Path, output_dir: Path):
    """Create a parse coordinator."""
    return PowerBuilderParseCoordinator(
        input_dir=str(input_dir), output_dir=str(output_dir)
    )


def create_model_coordinator(input_dir: Path, output_dir: Path):
    """Create a model coordinator."""
    return PowerBuilderParseCoordinator(
        input_dir=str(input_dir), output_dir=str(output_dir)
    )


def create_generate_coordinator(
    input_dir: Path, output_dir: Path, target: str = "flutter"
):
    """Create and configure a generate coordinator.

    Args:
        input_dir: Path to input models directory
        output_dir: Path to output generated code directory
        target: Target platform (flutter, python, react-typescript)

    Returns:
        Configured GenerateCoordinator instance
    """
    from ..application.coordinators.generate_coordinator import GenerateCoordinator
    from ..adapters.generators.flutter_generator import FlutterGenerator
    from ..adapters.generators.python_generator import PythonGenerator
    from ..adapters.generators.react_typescript_generator import (
        ReactTypeScriptGenerator,
    )
    from ..adapters.generators.tauri_generator import TauriGenerator
    from ..adapters.filesystem import AiofilesAdapter
    from ..adapters.logger import PythonLoggerAdapter
    from ..adapters.progress import ConsoleProgressAdapter

    # Create adapters
    filesystem = AiofilesAdapter()
    logger = PythonLoggerAdapter()
    progress = ConsoleProgressAdapter()

    # Select generator based on target
    generator = None
    if target in ["flutter", "dart"]:
        try:
            generator = FlutterGenerator()
        except ImportError:
            logger.warning("Flutter generator not available")
    elif target in ["python", "litestar"]:
        try:
            generator = PythonGenerator()
        except ImportError:
            logger.warning("Python generator not available")
    elif target in ["react-typescript", "react", "typescript"]:
        try:
            generator = ReactTypeScriptGenerator()
        except ImportError:
            logger.warning("React/TypeScript generator not available")
    elif target == "tauri":
        try:
            generator = TauriGenerator()
        except ImportError:
            logger.warning("Tauri generator not available")
    elif target == "dioxus":
        try:
            from ..adapters.generators.dioxus_generator import DioxusGenerator

            generator = DioxusGenerator()
        except ImportError:
            logger.warning("Dioxus generator not available")

    # Create coordinator
    coordinator = GenerateCoordinator(
        generator=generator,
        filesystem=filesystem,
        logger=logger,
        progress=progress,
        input_path=input_dir,
        output_path=output_dir,
        target=target,
    )

    return coordinator
