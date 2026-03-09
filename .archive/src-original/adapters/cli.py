"""Infrastructure - CLI Adapter for Functional Pipeline.

Bridges Click CLI with the functional pipeline coordinator.
Converts CLI arguments to value objects and handles results.
"""

import json
import sys
from typing import Dict, Any
from datetime import datetime

import click

from src_new._core.result import Result, Success, Failure
from src_new._core.value_objects import FilePath, DirectoryPath
from src_new._core.dependencies import (
    create_production_dependencies,
    create_test_dependencies,
)
from src_new._core.errors import DomainError, error_to_json
from src_new._core.workflow import PipelineStage

from src_new.app.pipeline_coordinator import PipelineConfig, create_pipeline_coordinator


# ============================================================================
# CLI OUTPUT FORMATTING
# ============================================================================


class CliFormatter:
    """Formats output for CLI display."""

    @staticmethod
    def success(message: str) -> None:
        """Print success message."""
        click.secho(f"✓ {message}", fg="green")

    @staticmethod
    def error(message: str) -> None:
        """Print error message."""
        click.secho(f"✗ {message}", fg="red", err=True)

    @staticmethod
    def warning(message: str) -> None:
        """Print warning message."""
        click.secho(f"⚠ {message}", fg="yellow")

    @staticmethod
    def info(message: str) -> None:
        """Print info message."""
        click.echo(f"ℹ {message}")

    @staticmethod
    def progress(message: str) -> None:
        """Print progress message."""
        click.echo(f"→ {message}")

    @staticmethod
    def stage_header(stage: str) -> None:
        """Print stage header."""
        click.echo("")
        click.secho(f"{'=' * 60}", fg="blue")
        click.secho(f" STAGE: {stage.upper()}", fg="blue", bold=True)
        click.secho(f"{'=' * 60}", fg="blue")

    @staticmethod
    def print_summary(result: Dict[str, Any]) -> None:
        """Print execution summary."""
        click.echo("")
        click.secho("EXECUTION SUMMARY", fg="cyan", bold=True)
        click.secho("-" * 40, fg="cyan")

        stages = result.get("stages_completed", 0)
        errors = result.get("total_errors", 0)
        duration = result.get("duration_ms", 0)
        events = result.get("events_generated", 0)

        click.echo(f"Stages Completed: {stages}/5")
        click.echo(f"Total Errors:     {errors}")
        click.echo(f"Duration:         {duration:.2f}ms")
        click.echo(f"Events Generated: {events}")

        if "output_path" in result:
            click.echo(f"Output Path:      {result['output_path']}")

    @staticmethod
    def print_events(events: list) -> None:
        """Print events in readable format."""
        if not events:
            return

        click.echo("")
        click.secho("EVENTS", fg="cyan", bold=True)
        click.secho("-" * 40, fg="cyan")

        for event in events[:10]:  # Limit to first 10
            event_type = event.event_type if hasattr(event, "event_type") else "unknown"
            timestamp = (
                event.timestamp if hasattr(event, "timestamp") else datetime.now()
            )
            click.echo(f"[{timestamp.strftime('%H:%M:%S')}] {event_type}")

        if len(events) > 10:
            click.echo(f"... and {len(events) - 10} more events")


# ============================================================================
# CLI ADAPTER
# ============================================================================


class FunctionalCliAdapter:
    """Adapts CLI commands to functional pipeline."""

    def __init__(self, test_mode: bool = False):
        """Initialize adapter with dependencies."""
        if test_mode:
            self.deps = create_test_dependencies()
        else:
            self.deps = create_production_dependencies()

        self.formatter = CliFormatter()
        self.coordinator = create_pipeline_coordinator(self.deps)

    def validate_paths(
        self, source: str, output: str
    ) -> Result[tuple[FilePath, DirectoryPath], str]:
        """Validate and create path value objects."""
        # Validate source path
        source_result = FilePath.create(source, must_exist=True)
        if source_result.is_failure():
            return Failure(f"Invalid source path: {source_result.error()}")

        # Validate output path (create if needed)
        output_result = DirectoryPath.create(output, must_exist=False)
        if output_result.is_failure():
            return Failure(f"Invalid output path: {output_result.error()}")

        # Create output directory if it doesn't exist
        output_path = output_result.value()
        create_result = self.deps.file_system.create_directory(output_path)
        if create_result.is_failure():
            return Failure(f"Cannot create output directory: {create_result.error()}")

        return Success((source_result.value(), output_path))

    def execute_pipeline(
        self,
        source: str,
        output: str,
        target: str = "flutter",
        parallel: bool = True,
        workers: int = 4,
        skip_errors: bool = True,
        verbose: bool = False,
    ) -> int:
        """Execute the complete pipeline.

        Returns exit code: 0 for success, 1 for failure.
        """
        self.formatter.info("PowerRebuilder Functional Pipeline v1.0.0")
        self.formatter.info(f"Source: {source}")
        self.formatter.info(f"Output: {output}")
        self.formatter.info(f"Target: {target}")

        # Validate paths
        path_result = self.validate_paths(source, output)
        if path_result.is_failure():
            self.formatter.error(path_result.error())
            return 1

        source_path, output_path = path_result.value()

        # Create pipeline configuration
        config = PipelineConfig(
            source_path=source_path,
            output_path=output_path,
            target_language=target,
            parallel_files=parallel,
            max_workers=workers,
            skip_errors=skip_errors,
            generate_reports=True,
            log_level="DEBUG" if verbose else "INFO",
        )

        # Execute pipeline
        self.formatter.progress("Starting pipeline execution...")
        result = self.coordinator.execute_pipeline(config)

        # Handle result
        if result.result.is_success():
            output_data = result.result.value()

            self.formatter.success("Pipeline completed successfully!")
            self.formatter.print_summary(output_data)

            if verbose:
                self.formatter.print_events(result.events)

            # Generate and save report
            if config.generate_reports:
                self._save_report(output_path, output_data, result.events)

            return 0
        else:
            error = result.result.error()

            if isinstance(error, DomainError):
                self.formatter.error(f"Pipeline failed: {error.user_message}")
                if verbose:
                    error_json = error_to_json(error)
                    click.echo(json.dumps(error_json, indent=2))
            else:
                self.formatter.error(f"Pipeline failed: {error}")

            # Still print partial results
            if result.events:
                self.formatter.warning(
                    f"Partial execution: {len(result.events)} events generated"
                )
                if verbose:
                    self.formatter.print_events(result.events)

            return 1

    def execute_stage(
        self, stage: str, source: str, output: str, verbose: bool = False
    ) -> int:
        """Execute a single pipeline stage.

        Returns exit code: 0 for success, 1 for failure.
        """
        # Map stage name to enum
        stage_map = {
            "extract": PipelineStage.EXTRACT,
            "decompile": PipelineStage.DECOMPILE,
            "parse": PipelineStage.PARSE,
            "model": PipelineStage.MODEL,
            "generate": PipelineStage.GENERATE,
        }

        pipeline_stage = stage_map.get(stage.lower())
        if not pipeline_stage:
            self.formatter.error(f"Unknown stage: {stage}")
            return 1

        self.formatter.stage_header(stage)

        # Validate paths
        path_result = self.validate_paths(source, output)
        if path_result.is_failure():
            self.formatter.error(path_result.error())
            return 1

        source_path, output_path = path_result.value()

        # Create configuration
        config = PipelineConfig(
            source_path=source_path,
            output_path=output_path,
            log_level="DEBUG" if verbose else "INFO",
        )

        # Execute stage
        self.formatter.progress(f"Executing {stage} stage...")
        result = self.coordinator.execute_stage(pipeline_stage, config)

        # Handle result
        if result.result.is_success():
            output_data = result.result.value()

            self.formatter.success(f"{stage.capitalize()} completed successfully!")

            # Print stage-specific output
            if "count" in output_data:
                self.formatter.info(f"Items processed: {output_data['count']}")
            if "output_files" in output_data:
                self.formatter.info(f"Files generated: {output_data['output_files']}")

            if verbose:
                self.formatter.print_events(result.events)

            return 0
        else:
            self.formatter.error(
                f"{stage.capitalize()} failed: {result.result.error()}"
            )
            return 1

    def _save_report(
        self, output_path: DirectoryPath, result: Dict[str, Any], events: list
    ) -> None:
        """Save execution report to file."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "result": result,
            "event_count": len(events),
            "events": [
                {
                    "type": e.event_type if hasattr(e, "event_type") else "unknown",
                    "timestamp": e.timestamp.isoformat()
                    if hasattr(e, "timestamp")
                    else None,
                }
                for e in events[:100]  # Limit events in report
            ],
        }

        report_path = output_path.join("pipeline_report.json")

        try:
            report_file = FilePath.create(str(report_path))
            if report_file.is_success():
                report_json = json.dumps(report, indent=2)
                write_result = self.deps.file_system.write_file(
                    report_file.value(), report_json.encode("utf-8")
                )
                if write_result.is_success():
                    self.formatter.info(f"Report saved to: {report_path}")
        except Exception as e:
            self.formatter.warning(f"Could not save report: {e}")


# ============================================================================
# CLI COMMANDS
# ============================================================================


@click.group()
@click.option("--functional", is_flag=True, help="Use functional pipeline")
@click.option("--test-mode", is_flag=True, help="Use test dependencies")
@click.pass_context
def cli(ctx, functional: bool, test_mode: bool):
    """PowerRebuilder Functional Pipeline CLI."""
    ctx.ensure_object(dict)
    ctx.obj["functional"] = functional
    ctx.obj["test_mode"] = test_mode


@cli.command()
@click.argument("source")
@click.argument("output")
@click.option(
    "--target",
    "-t",
    default="flutter",
    type=click.Choice(["flutter", "python", "react"]),
    help="Target language/framework",
)
@click.option(
    "--parallel/--no-parallel", default=True, help="Enable parallel processing"
)
@click.option("--workers", "-w", default=4, type=int, help="Number of parallel workers")
@click.option("--skip-errors/--fail-fast", default=True, help="Continue on errors")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def all(
    ctx,
    source: str,
    output: str,
    target: str,
    parallel: bool,
    workers: int,
    skip_errors: bool,
    verbose: bool,
):
    """Execute complete pipeline (all stages)."""
    if not ctx.obj.get("functional"):
        click.echo("Use --functional flag to use the new functional pipeline")
        return 1

    adapter = FunctionalCliAdapter(test_mode=ctx.obj.get("test_mode", False))
    return adapter.execute_pipeline(
        source, output, target, parallel, workers, skip_errors, verbose
    )


@cli.command()
@click.argument("source")
@click.argument("output")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def extract(ctx, source: str, output: str, verbose: bool):
    """Execute extraction stage only."""
    if not ctx.obj.get("functional"):
        click.echo("Use --functional flag to use the new functional pipeline")
        return 1

    adapter = FunctionalCliAdapter(test_mode=ctx.obj.get("test_mode", False))
    return adapter.execute_stage("extract", source, output, verbose)


@cli.command()
@click.argument("source")
@click.argument("output")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def decompile(ctx, source: str, output: str, verbose: bool):
    """Execute decompilation stage only."""
    if not ctx.obj.get("functional"):
        click.echo("Use --functional flag to use the new functional pipeline")
        return 1

    adapter = FunctionalCliAdapter(test_mode=ctx.obj.get("test_mode", False))
    return adapter.execute_stage("decompile", source, output, verbose)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main():
    """Main entry point for functional CLI."""
    try:
        sys.exit(cli())
    except Exception as e:
        click.secho(f"Unexpected error: {e}", fg="red", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
