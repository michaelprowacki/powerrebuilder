"""Reporting App - Migration Report Generator.

Application layer that collects events from all pipeline stages
and generates comprehensive migration reports.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import json

# Import event types from all domains
from src_new.domain.extract.extract_pbl import (
    ObjectExtracted,
    ExtractionFailed,
    HeaderParsed,
    LibraryValidated,
    ExtractionEvent,
)
from src_new.domain.decompile.decompile_pcode import DecompileResult
from src_new.domain.parse.parse_datawindow import (
    DataWindowParsed,
    ColumnParsed,
    ControlParsed,
    SQLExtracted,
    DataWindowWarning,
    DataWindowEvent,
)
from src_new.domain.model.symbol_resolution import (
    SymbolResolved,
    UnresolvedReference,
    CircularDependency,
    DependencyFound,
    SymbolTableBuilt,
    SymbolEvent,
)
from src_new.domain.generate.generate_flutter import (
    WidgetGenerated,
    DartFileGenerated,
    ProjectConfigured,
    GenerationWarning,
    FlutterEvent,
)


# ============================================================================
# REPORT TYPES
# ============================================================================


class ReportFormat(str, Enum):
    """Output formats for migration reports."""

    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"
    CSV = "csv"


class SeverityLevel(str, Enum):
    """Severity levels for issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass(frozen=True)
class MigrationIssue:
    """A single issue found during migration."""

    stage: str
    component: str
    description: str
    severity: SeverityLevel
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class StageMetrics:
    """Metrics for a single pipeline stage."""

    stage_name: str
    files_processed: int = 0
    objects_extracted: int = 0
    errors_count: int = 0
    warnings_count: int = 0
    success_rate: float = 0.0
    processing_time: float = 0.0
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MigrationReport:
    """Complete migration report."""

    project_name: str
    timestamp: datetime
    source_path: str
    target_path: str
    stages: Dict[str, StageMetrics]
    issues: List[MigrationIssue]
    dependencies: Dict[str, List[str]]
    summary: Dict[str, Any]
    events: List[Dict[str, Any]]  # Raw events for detailed analysis


# ============================================================================
# REPORT GENERATOR
# ============================================================================


class MigrationReporter:
    """Generates migration reports from pipeline events."""

    def __init__(self):
        """Initialize reporter."""
        self.events = []
        self.issues = []
        self.stages = {}
        self.dependencies = {}

    def collect_extraction_events(self, events: List[ExtractionEvent]) -> None:
        """Collect events from extraction stage."""
        if "extract" not in self.stages:
            self.stages["extract"] = StageMetrics(stage_name="Extract")

        metrics = self.stages["extract"]

        for event in events:
            self.events.append(
                {
                    "stage": "extract",
                    "type": type(event).__name__,
                    "data": event.__dict__,
                }
            )

            if isinstance(event, ObjectExtracted):
                metrics.objects_extracted += 1
                metrics.custom_metrics[event.object_type.value] = (
                    metrics.custom_metrics.get(event.object_type.value, 0) + 1
                )

            elif isinstance(event, ExtractionFailed):
                metrics.errors_count += 1
                self.issues.append(
                    MigrationIssue(
                        stage="extract",
                        component=event.object_name,
                        description=event.reason,
                        severity=SeverityLevel.ERROR
                        if not event.recoverable
                        else SeverityLevel.WARNING,
                        file_path=None,
                        line_number=None,
                        suggestion="Check file format and integrity",
                    )
                )

            elif isinstance(event, LibraryValidated):
                metrics.custom_metrics["valid_libraries"] = metrics.custom_metrics.get(
                    "valid_libraries", 0
                ) + (1 if event.is_valid else 0)
                if event.issues_found > 0:
                    metrics.warnings_count += event.issues_found

            elif isinstance(event, HeaderParsed):
                metrics.files_processed += 1
                metrics.custom_metrics["total_entries"] = (
                    metrics.custom_metrics.get("total_entries", 0) + event.entry_count
                )

        # Calculate success rate
        if metrics.files_processed > 0:
            metrics.success_rate = (
                metrics.files_processed - metrics.errors_count
            ) / metrics.files_processed

    def collect_decompile_events(self, results: List[DecompileResult]) -> None:
        """Collect results from decompilation stage."""
        if "decompile" not in self.stages:
            self.stages["decompile"] = StageMetrics(stage_name="Decompile")

        metrics = self.stages["decompile"]

        for result in results:
            metrics.files_processed += 1

            # Record result
            self.events.append(
                {
                    "stage": "decompile",
                    "type": "DecompileResult",
                    "data": {
                        "success": hasattr(result, "source"),
                        "instructions": getattr(result, "instructions_processed", 0),
                        "warnings": len(getattr(result, "warnings", [])),
                    },
                }
            )

            if hasattr(result, "source"):  # Success
                metrics.custom_metrics["instructions_processed"] = (
                    metrics.custom_metrics.get("instructions_processed", 0)
                    + result.instructions_processed
                )

                for warning in result.warnings:
                    metrics.warnings_count += 1
                    self.issues.append(
                        MigrationIssue(
                            stage="decompile",
                            component="p-code",
                            description=warning,
                            severity=SeverityLevel.WARNING,
                        )
                    )
            else:  # Failed
                metrics.errors_count += 1
                self.issues.append(
                    MigrationIssue(
                        stage="decompile",
                        component="p-code",
                        description=result.error,
                        severity=SeverityLevel.ERROR,
                    )
                )

        # Calculate success rate
        if metrics.files_processed > 0:
            metrics.success_rate = (
                metrics.files_processed - metrics.errors_count
            ) / metrics.files_processed

    def collect_parse_events(self, events: List[DataWindowEvent]) -> None:
        """Collect events from parsing stage."""
        if "parse" not in self.stages:
            self.stages["parse"] = StageMetrics(stage_name="Parse")

        metrics = self.stages["parse"]

        for event in events:
            self.events.append(
                {"stage": "parse", "type": type(event).__name__, "data": event.__dict__}
            )

            if isinstance(event, DataWindowParsed):
                metrics.files_processed += 1
                metrics.custom_metrics["datawindows"] = (
                    metrics.custom_metrics.get("datawindows", 0) + 1
                )
                metrics.custom_metrics[f"dw_{event.type}"] = (
                    metrics.custom_metrics.get(f"dw_{event.type}", 0) + 1
                )

            elif isinstance(event, ColumnParsed):
                metrics.custom_metrics["columns"] = (
                    metrics.custom_metrics.get("columns", 0) + 1
                )

            elif isinstance(event, ControlParsed):
                metrics.custom_metrics["controls"] = (
                    metrics.custom_metrics.get("controls", 0) + 1
                )

            elif isinstance(event, SQLExtracted):
                metrics.custom_metrics["sql_statements"] = (
                    metrics.custom_metrics.get("sql_statements", 0) + 1
                )
                if event.has_joins:
                    metrics.custom_metrics["complex_queries"] = (
                        metrics.custom_metrics.get("complex_queries", 0) + 1
                    )

            elif isinstance(event, DataWindowWarning):
                metrics.warnings_count += 1
                self.issues.append(
                    MigrationIssue(
                        stage="parse",
                        component=event.component,
                        description=event.issue,
                        severity=SeverityLevel.WARNING,
                        line_number=event.line,
                    )
                )

    def collect_model_events(self, events: List[SymbolEvent]) -> None:
        """Collect events from model stage."""
        if "model" not in self.stages:
            self.stages["model"] = StageMetrics(stage_name="Model")

        metrics = self.stages["model"]

        for event in events:
            self.events.append(
                {"stage": "model", "type": type(event).__name__, "data": event.__dict__}
            )

            if isinstance(event, SymbolResolved):
                metrics.custom_metrics["symbols_resolved"] = (
                    metrics.custom_metrics.get("symbols_resolved", 0) + 1
                )

            elif isinstance(event, UnresolvedReference):
                metrics.warnings_count += 1
                self.issues.append(
                    MigrationIssue(
                        stage="model",
                        component="symbol_resolution",
                        description=f"Unresolved reference: {event.reference}",
                        severity=SeverityLevel.WARNING,
                        file_path=event.from_location,
                        line_number=event.line_number,
                        suggestion=f"Possible matches: {', '.join(event.possible_matches)}",
                    )
                )

            elif isinstance(event, CircularDependency):
                severity = (
                    SeverityLevel.ERROR
                    if event.severity == "high"
                    else SeverityLevel.WARNING
                )
                self.issues.append(
                    MigrationIssue(
                        stage="model",
                        component="dependency_analysis",
                        description=f"Circular dependency: {' -> '.join(event.cycle)}",
                        severity=severity,
                        suggestion="Refactor to break circular dependency",
                    )
                )

            elif isinstance(event, DependencyFound):
                if event.from_module not in self.dependencies:
                    self.dependencies[event.from_module] = []
                self.dependencies[event.from_module].append(event.to_module)

            elif isinstance(event, SymbolTableBuilt):
                metrics.files_processed += 1
                metrics.custom_metrics["total_symbols"] = event.total_symbols
                metrics.custom_metrics["resolution_rate"] = event.resolution_rate
                metrics.success_rate = event.resolution_rate

    def collect_generation_events(self, events: List[FlutterEvent]) -> None:
        """Collect events from generation stage."""
        if "generate" not in self.stages:
            self.stages["generate"] = StageMetrics(stage_name="Generate")

        metrics = self.stages["generate"]

        for event in events:
            self.events.append(
                {
                    "stage": "generate",
                    "type": type(event).__name__,
                    "data": event.__dict__,
                }
            )

            if isinstance(event, WidgetGenerated):
                metrics.custom_metrics["widgets"] = (
                    metrics.custom_metrics.get("widgets", 0) + 1
                )
                metrics.custom_metrics["total_loc"] = (
                    metrics.custom_metrics.get("total_loc", 0) + event.lines_of_code
                )

            elif isinstance(event, DartFileGenerated):
                metrics.files_processed += 1
                metrics.custom_metrics[f"{event.file_type}_files"] = (
                    metrics.custom_metrics.get(f"{event.file_type}_files", 0) + 1
                )

            elif isinstance(event, ProjectConfigured):
                metrics.custom_metrics["project_configured"] = True
                metrics.custom_metrics["total_files"] = event.total_files
                metrics.custom_metrics["total_widgets"] = event.total_widgets

            elif isinstance(event, GenerationWarning):
                severity_map = {
                    "high": SeverityLevel.ERROR,
                    "medium": SeverityLevel.WARNING,
                    "low": SeverityLevel.INFO,
                }
                self.issues.append(
                    MigrationIssue(
                        stage="generate",
                        component=event.component,
                        description=event.issue,
                        severity=severity_map.get(
                            event.severity, SeverityLevel.WARNING
                        ),
                    )
                )

    def generate_report(
        self, project_name: str, source_path: str, target_path: str
    ) -> MigrationReport:
        """Generate complete migration report.

        Aggregates all collected events and metrics.
        """
        # Calculate summary metrics
        total_files = sum(s.files_processed for s in self.stages.values())
        total_errors = sum(s.errors_count for s in self.stages.values())
        total_warnings = sum(s.warnings_count for s in self.stages.values())
        overall_success_rate = (
            (total_files - total_errors) / total_files if total_files > 0 else 0
        )

        summary = {
            "total_files_processed": total_files,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "overall_success_rate": overall_success_rate,
            "critical_issues": len(
                [i for i in self.issues if i.severity == SeverityLevel.CRITICAL]
            ),
            "stages_completed": len(self.stages),
            "dependencies_mapped": len(self.dependencies),
            "circular_dependencies": len(
                [i for i in self.issues if "circular" in i.description.lower()]
            ),
        }

        return MigrationReport(
            project_name=project_name,
            timestamp=datetime.now(),
            source_path=source_path,
            target_path=target_path,
            stages=self.stages,
            issues=self.issues,
            dependencies=self.dependencies,
            summary=summary,
            events=self.events,
        )

    def format_report(self, report: MigrationReport, format: ReportFormat) -> str:
        """Format report in requested format."""
        if format == ReportFormat.JSON:
            return self._format_json(report)
        elif format == ReportFormat.MARKDOWN:
            return self._format_markdown(report)
        elif format == ReportFormat.HTML:
            return self._format_html(report)
        elif format == ReportFormat.CSV:
            return self._format_csv(report)
        else:
            raise ValueError(f"Unknown report format: {format}")

    def _format_json(self, report: MigrationReport) -> str:
        """Format report as JSON."""
        data = {
            "project_name": report.project_name,
            "timestamp": report.timestamp.isoformat(),
            "source_path": report.source_path,
            "target_path": report.target_path,
            "summary": report.summary,
            "stages": {
                name: {
                    "stage_name": metrics.stage_name,
                    "files_processed": metrics.files_processed,
                    "objects_extracted": metrics.objects_extracted,
                    "errors_count": metrics.errors_count,
                    "warnings_count": metrics.warnings_count,
                    "success_rate": metrics.success_rate,
                    "custom_metrics": metrics.custom_metrics,
                }
                for name, metrics in report.stages.items()
            },
            "issues": [
                {
                    "stage": issue.stage,
                    "component": issue.component,
                    "description": issue.description,
                    "severity": issue.severity,
                    "file_path": issue.file_path,
                    "line_number": issue.line_number,
                    "suggestion": issue.suggestion,
                }
                for issue in report.issues
            ],
            "dependencies": report.dependencies,
            "events_count": len(report.events),
        }
        return json.dumps(data, indent=2)

    def _format_markdown(self, report: MigrationReport) -> str:
        """Format report as Markdown."""
        lines = []

        # Header
        lines.append(f"# Migration Report: {report.project_name}")
        lines.append(
            f"\n**Generated:** {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        lines.append(f"**Source:** `{report.source_path}`")
        lines.append(f"**Target:** `{report.target_path}`")

        # Summary
        lines.append("\n## Summary")
        lines.append(
            f"- **Total Files Processed:** {report.summary['total_files_processed']}"
        )
        lines.append(
            f"- **Overall Success Rate:** {report.summary['overall_success_rate']:.1%}"
        )
        lines.append(f"- **Total Errors:** {report.summary['total_errors']}")
        lines.append(f"- **Total Warnings:** {report.summary['total_warnings']}")
        lines.append(f"- **Critical Issues:** {report.summary['critical_issues']}")
        lines.append(
            f"- **Circular Dependencies:** {report.summary['circular_dependencies']}"
        )

        # Stage Metrics
        lines.append("\n## Pipeline Stages")
        for stage_name, metrics in report.stages.items():
            lines.append(f"\n### {metrics.stage_name}")
            lines.append(f"- Files Processed: {metrics.files_processed}")
            lines.append(f"- Success Rate: {metrics.success_rate:.1%}")
            lines.append(f"- Errors: {metrics.errors_count}")
            lines.append(f"- Warnings: {metrics.warnings_count}")

            if metrics.custom_metrics:
                lines.append("- **Metrics:**")
                for key, value in metrics.custom_metrics.items():
                    if isinstance(value, float):
                        lines.append(f"  - {key}: {value:.2f}")
                    else:
                        lines.append(f"  - {key}: {value}")

        # Issues
        if report.issues:
            lines.append("\n## Issues")

            # Group by severity
            for severity in [
                SeverityLevel.CRITICAL,
                SeverityLevel.ERROR,
                SeverityLevel.WARNING,
                SeverityLevel.INFO,
            ]:
                issues = [i for i in report.issues if i.severity == severity]
                if issues:
                    lines.append(f"\n### {severity.value.capitalize()} ({len(issues)})")
                    for issue in issues[:10]:  # Limit to first 10
                        lines.append(f"- **[{issue.stage}]** {issue.description}")
                        if issue.suggestion:
                            lines.append(f"  - *Suggestion:* {issue.suggestion}")
                    if len(issues) > 10:
                        lines.append(f"  - *...and {len(issues) - 10} more*")

        # Dependencies
        if report.dependencies:
            lines.append("\n## Dependencies")
            lines.append(f"Found {len(report.dependencies)} modules with dependencies:")
            for module, deps in list(report.dependencies.items())[:10]:
                lines.append(f"- **{module}** → {', '.join(deps[:5])}")
                if len(deps) > 5:
                    lines.append(f"  *...and {len(deps) - 5} more*")

        return "\n".join(lines)

    def _format_html(self, report: MigrationReport) -> str:
        """Format report as HTML."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Migration Report: {report.project_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; border-bottom: 2px solid #eee; padding-bottom: 5px; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
        .metric {{ display: inline-block; margin: 10px 20px; }}
        .error {{ color: #d32f2f; }}
        .warning {{ color: #f57c00; }}
        .info {{ color: #1976d2; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #f5f5f5; }}
    </style>
</head>
<body>
    <h1>Migration Report: {report.project_name}</h1>
    <p>Generated: {report.timestamp.strftime("%Y-%m-%d %H:%M:%S")}</p>

    <div class="summary">
        <h2>Summary</h2>
        <div class="metric">Files Processed: <strong>{report.summary["total_files_processed"]}</strong></div>
        <div class="metric">Success Rate: <strong>{report.summary["overall_success_rate"]:.1%}</strong></div>
        <div class="metric error">Errors: <strong>{report.summary["total_errors"]}</strong></div>
        <div class="metric warning">Warnings: <strong>{report.summary["total_warnings"]}</strong></div>
    </div>

    <h2>Pipeline Stages</h2>
    <table>
        <tr>
            <th>Stage</th>
            <th>Files</th>
            <th>Success Rate</th>
            <th>Errors</th>
            <th>Warnings</th>
        </tr>
"""

        for stage_name, metrics in report.stages.items():
            html += f"""
        <tr>
            <td>{metrics.stage_name}</td>
            <td>{metrics.files_processed}</td>
            <td>{metrics.success_rate:.1%}</td>
            <td class="error">{metrics.errors_count}</td>
            <td class="warning">{metrics.warnings_count}</td>
        </tr>
"""

        html += """
    </table>
</body>
</html>
"""
        return html

    def _format_csv(self, report: MigrationReport) -> str:
        """Format report as CSV."""
        lines = []

        # Header
        lines.append("Stage,Files Processed,Success Rate,Errors,Warnings")

        # Data
        for stage_name, metrics in report.stages.items():
            lines.append(
                f"{metrics.stage_name},{metrics.files_processed},"
                f"{metrics.success_rate:.2f},{metrics.errors_count},"
                f"{metrics.warnings_count}"
            )

        return "\n".join(lines)
