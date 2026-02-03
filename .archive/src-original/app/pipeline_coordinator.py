"""Application - Functional Pipeline Coordinator.

Orchestrates the complete PowerRebuilder pipeline using functional patterns.
This is the main workflow that coordinates all stages using the new approach.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
import time
import uuid
from datetime import datetime

from src_new._core.result import Result, Success, Failure, EventfulResult
from src_new._core.value_objects import FilePath, DirectoryPath
from src_new._core.dependencies import Dependencies
from src_new._core.events import DomainEvent, EventStore
from src_new._core.errors import DomainError
from src_new._core.workflow import (
    WorkflowStep,
    StepResult,
    Workflow,
    WorkflowDefinition,
    WorkflowBuilder,
    PipelineStage,
)

# Import functional domain functions
from src_new.domain.extract.extract_pbl_functional import extract_pbl_pure


# ============================================================================
# PIPELINE CONFIGURATION
# ============================================================================


@dataclass(frozen=True)
class PipelineConfig:
    """Configuration for the pipeline execution."""

    source_path: FilePath
    output_path: DirectoryPath
    target_language: str = "flutter"  # flutter, python, react
    parallel_files: bool = True
    max_workers: int = 4
    skip_errors: bool = True
    generate_reports: bool = True
    log_level: str = "INFO"
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# PIPELINE EVENTS
# ============================================================================


@dataclass(frozen=True)
class PipelineStartedEvent(DomainEvent):
    """Pipeline execution started."""

    config: PipelineConfig
    stages: List[str]

    @property
    def event_type(self) -> str:
        return "pipeline.started"

    @property
    def event_version(self) -> int:
        return 1


@dataclass(frozen=True)
class StageStartedEvent(DomainEvent):
    """Stage execution started."""

    stage: PipelineStage
    input_files: int

    @property
    def event_type(self) -> str:
        return "stage.started"

    @property
    def event_version(self) -> int:
        return 1


@dataclass(frozen=True)
class StageCompletedEvent(DomainEvent):
    """Stage execution completed."""

    stage: PipelineStage
    duration_ms: float
    output_files: int
    errors: int

    @property
    def event_type(self) -> str:
        return "stage.completed"

    @property
    def event_version(self) -> int:
        return 1


@dataclass(frozen=True)
class PipelineCompletedEvent(DomainEvent):
    """Pipeline execution completed."""

    total_duration_ms: float
    stages_completed: int
    total_errors: int
    output_path: str

    @property
    def event_type(self) -> str:
        return "pipeline.completed"

    @property
    def event_version(self) -> int:
        return 1


# ============================================================================
# WORKFLOW STEPS
# ============================================================================


class ExtractStep(WorkflowStep):
    """Extract stage using functional approach."""

    def __init__(self, deps: Dependencies):
        self.deps = deps

    @property
    def name(self) -> str:
        return PipelineStage.EXTRACT.value

    def execute(self, config: PipelineConfig) -> Result[StepResult, str]:
        """Execute extraction stage."""
        start_time = time.time()
        events = []

        # Emit stage started event
        events.append(
            StageStartedEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                stage=PipelineStage.EXTRACT,
                input_files=1,
            )
        )

        # Read library file
        read_result = self.deps.file_system.read_file(config.source_path)
        if read_result.is_failure():
            return Failure(f"Cannot read source file: {read_result.error()}")

        library_data = read_result.value()

        # Extract using pure function
        extraction_result = extract_pbl_pure(library_data)

        if extraction_result.result.is_failure():
            error = extraction_result.result.error()
            if isinstance(error, DomainError):
                return Failure(error.user_message)
            return Failure(str(error))

        entries = extraction_result.result.value()
        events.extend(extraction_result.events)

        # Write extracted files
        output_count = 0
        for entry in entries:
            file_name = f"{entry.name.value}.fun"
            file_path = config.output_path.join("extracted", file_name)

            # Create FilePath value object
            path_result = FilePath.create(str(file_path))
            if path_result.is_success():
                write_result = self.deps.file_system.write_file(
                    path_result.value(), entry.data
                )
                if write_result.is_success():
                    output_count += 1

        # Emit stage completed event
        duration_ms = (time.time() - start_time) * 1000
        events.append(
            StageCompletedEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                stage=PipelineStage.EXTRACT,
                duration_ms=duration_ms,
                output_files=output_count,
                errors=0,
            )
        )

        return Success(
            StepResult(
                output={
                    "entries": entries,
                    "count": len(entries),
                    "output_files": output_count,
                },
                events=events,
                metadata={"stage": self.name, "duration_ms": duration_ms},
            )
        )


class DecompileStep(WorkflowStep):
    """Decompile stage (placeholder for now)."""

    def __init__(self, deps: Dependencies):
        self.deps = deps

    @property
    def name(self) -> str:
        return PipelineStage.DECOMPILE.value

    def execute(self, input: Dict) -> Result[StepResult, str]:
        """Execute decompilation stage."""
        # TODO: Implement functional decompilation
        # For now, pass through
        return Success(
            StepResult(
                output=input,
                events=[],
                metadata={"stage": self.name, "status": "not_implemented"},
            )
        )


class ParseStep(WorkflowStep):
    """Parse stage (placeholder for now)."""

    def __init__(self, deps: Dependencies):
        self.deps = deps

    @property
    def name(self) -> str:
        return PipelineStage.PARSE.value

    def execute(self, input: Dict) -> Result[StepResult, str]:
        """Execute parsing stage."""
        # TODO: Implement functional parsing
        return Success(
            StepResult(
                output=input,
                events=[],
                metadata={"stage": self.name, "status": "not_implemented"},
            )
        )


class ModelStep(WorkflowStep):
    """Model stage (placeholder for now)."""

    def __init__(self, deps: Dependencies):
        self.deps = deps

    @property
    def name(self) -> str:
        return PipelineStage.MODEL.value

    def execute(self, input: Dict) -> Result[StepResult, str]:
        """Execute modeling stage."""
        # TODO: Implement functional modeling
        return Success(
            StepResult(
                output=input,
                events=[],
                metadata={"stage": self.name, "status": "not_implemented"},
            )
        )


class GenerateStep(WorkflowStep):
    """Generate stage (placeholder for now)."""

    def __init__(self, deps: Dependencies):
        self.deps = deps

    @property
    def name(self) -> str:
        return PipelineStage.GENERATE.value

    def execute(self, input: Dict) -> Result[StepResult, str]:
        """Execute generation stage."""
        # TODO: Implement functional generation
        return Success(
            StepResult(
                output={"generated": True, "files": []},
                events=[],
                metadata={"stage": self.name, "status": "not_implemented"},
            )
        )


# ============================================================================
# PIPELINE COORDINATOR
# ============================================================================


class FunctionalPipelineCoordinator:
    """Coordinates the complete pipeline using functional approach."""

    def __init__(self, deps: Dependencies):
        """Initialize with dependencies."""
        self.deps = deps
        self.event_store = EventStore()

    def create_pipeline_workflow(self, config: PipelineConfig) -> WorkflowDefinition:
        """Create the pipeline workflow definition."""
        builder = WorkflowBuilder("PowerRebuilder Pipeline")

        workflow = (
            builder.with_description(
                "Complete PowerRebuilder pipeline with functional approach"
            )
            .add_step(ExtractStep(self.deps))
            .add_step(DecompileStep(self.deps))
            .add_step(ParseStep(self.deps))
            .add_step(ModelStep(self.deps))
            .add_step(GenerateStep(self.deps))
            .build()
        )

        return workflow

    def execute_pipeline(
        self, config: PipelineConfig
    ) -> EventfulResult[Dict[str, Any], str]:
        """Execute the complete pipeline.

        Returns EventfulResult with output and all events.
        """
        start_time = time.time()
        all_events = []

        # Log pipeline start
        self.deps.logger.info(
            f"Starting pipeline: {config.source_path} -> {config.output_path}"
        )

        # Emit pipeline started event
        all_events.append(
            PipelineStartedEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                config=config,
                stages=[s.value for s in PipelineStage],
            )
        )

        # Create workflow
        workflow_def = self.create_pipeline_workflow(config)
        workflow = Workflow(workflow_def)

        # Execute workflow
        # Note: Currently workflow expects dict input, so we pass config as first step input
        first_input = config

        # Execute each step manually for now (workflow needs enhancement for our use case)
        stages_completed = 0
        total_errors = 0
        current_output = None

        # Extract stage
        extract_result = ExtractStep(self.deps).execute(config)
        if extract_result.is_failure():
            return EventfulResult.failure(extract_result.error(), all_events)

        extract_output = extract_result.value()
        all_events.extend(extract_output.events)
        stages_completed += 1
        current_output = extract_output.output

        # Other stages (placeholders for now)
        for StepClass in [DecompileStep, ParseStep, ModelStep, GenerateStep]:
            step = StepClass(self.deps)
            result = step.execute(current_output)

            if result.is_failure():
                self.deps.logger.error(f"Stage {step.name} failed: {result.error()}")
                if not config.skip_errors:
                    return EventfulResult.failure(result.error(), all_events)
                total_errors += 1
            else:
                step_output = result.value()
                all_events.extend(step_output.events)
                stages_completed += 1
                current_output = step_output.output

        # Calculate total duration
        total_duration_ms = (time.time() - start_time) * 1000

        # Emit pipeline completed event
        all_events.append(
            PipelineCompletedEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                total_duration_ms=total_duration_ms,
                stages_completed=stages_completed,
                total_errors=total_errors,
                output_path=str(config.output_path),
            )
        )

        # Store all events
        self.event_store.append_many(all_events)

        # Log completion
        self.deps.logger.info(
            f"Pipeline completed in {total_duration_ms:.2f}ms: "
            f"{stages_completed} stages, {total_errors} errors"
        )

        # Return final result
        final_output = {
            "stages_completed": stages_completed,
            "total_errors": total_errors,
            "duration_ms": total_duration_ms,
            "output_path": str(config.output_path),
            "events_generated": len(all_events),
            "final_output": current_output,
        }

        return EventfulResult.success(final_output, all_events)

    def execute_stage(
        self, stage: PipelineStage, config: PipelineConfig
    ) -> EventfulResult[Dict[str, Any], str]:
        """Execute a single pipeline stage.

        For testing individual stages.
        """
        stage_map = {
            PipelineStage.EXTRACT: ExtractStep,
            PipelineStage.DECOMPILE: DecompileStep,
            PipelineStage.PARSE: ParseStep,
            PipelineStage.MODEL: ModelStep,
            PipelineStage.GENERATE: GenerateStep,
        }

        StepClass = stage_map.get(stage)
        if not StepClass:
            return EventfulResult.failure(f"Unknown stage: {stage}")

        step = StepClass(self.deps)

        # For extract, pass config; for others, need input from previous stage
        if stage == PipelineStage.EXTRACT:
            result = step.execute(config)
        else:
            # Would need input from previous stage in real usage
            result = step.execute({})

        if result.is_failure():
            return EventfulResult.failure(result.error(), [])

        step_output = result.value()
        return EventfulResult.success(step_output.output, step_output.events)

    def get_events(self) -> List[DomainEvent]:
        """Get all events from the event store."""
        return self.event_store.get_all()

    def generate_report(self) -> Dict[str, Any]:
        """Generate execution report from events."""
        events = self.get_events()

        report = {
            "total_events": len(events),
            "stages": {},
            "errors": [],
            "warnings": [],
        }

        for event in events:
            if isinstance(event, StageCompletedEvent):
                report["stages"][event.stage.value] = {
                    "duration_ms": event.duration_ms,
                    "output_files": event.output_files,
                    "errors": event.errors,
                }

        return report


# ============================================================================
# FACTORY FUNCTION
# ============================================================================


def create_pipeline_coordinator(deps: Dependencies) -> FunctionalPipelineCoordinator:
    """Create a pipeline coordinator with dependencies."""
    return FunctionalPipelineCoordinator(deps)


# ============================================================================
# USAGE EXAMPLE
# ============================================================================


def example_usage():
    """Example of using the functional pipeline coordinator."""
    from src_new._core.dependencies import create_test_dependencies

    # Create test dependencies
    deps = create_test_dependencies()

    # Create configuration
    source = FilePath.create("/path/to/library.pbl").value()
    output = DirectoryPath.create("/path/to/output").value()

    config = PipelineConfig(
        source_path=source,
        output_path=output,
        target_language="flutter",
        generate_reports=True,
    )

    # Create coordinator
    coordinator = create_pipeline_coordinator(deps)

    # Execute pipeline
    result = coordinator.execute_pipeline(config)

    # Check result
    if result.result.is_success():
        output = result.result.value()
        events = result.events

        print("Pipeline completed successfully!")
        print(f"Stages completed: {output['stages_completed']}")
        print(f"Events generated: {output['events_generated']}")
        print(f"Duration: {output['duration_ms']:.2f}ms")

        # Generate report
        report = coordinator.generate_report()
        print(f"Report: {report}")
    else:
        print(f"Pipeline failed: {result.result.error()}")

    return result
