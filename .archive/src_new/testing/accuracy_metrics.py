"""Accuracy metrics for measuring pipeline conversion quality."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import json
from pathlib import Path


class AccuracyLevel(str, Enum):
    """Accuracy levels for stage results."""

    PERFECT = "perfect"  # 100% accurate
    EXCELLENT = "excellent"  # 95-99% accurate
    GOOD = "good"  # 85-94% accurate
    FAIR = "fair"  # 70-84% accurate
    POOR = "poor"  # 50-69% accurate
    FAILED = "failed"  # <50% accurate


@dataclass
class MetricValue:
    """Single metric measurement."""

    name: str
    value: float
    expected: Optional[float] = None
    unit: str = "percent"
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def accuracy(self) -> float:
        """Calculate accuracy as percentage."""
        if self.expected is None or self.expected == 0:
            return 100.0 if self.value > 0 else 0.0
        return min(100.0, (self.value / self.expected) * 100)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "expected": self.expected,
            "unit": self.unit,
            "accuracy": self.accuracy,
            "details": self.details,
        }


@dataclass
class StageResult:
    """Result from a single pipeline stage."""

    stage_name: str
    success: bool
    accuracy: float  # Overall accuracy percentage
    metrics: List[MetricValue] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    output_size: int = 0
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def accuracy_level(self) -> AccuracyLevel:
        """Determine accuracy level based on percentage."""
        if self.accuracy >= 100:
            return AccuracyLevel.PERFECT
        elif self.accuracy >= 95:
            return AccuracyLevel.EXCELLENT
        elif self.accuracy >= 85:
            return AccuracyLevel.GOOD
        elif self.accuracy >= 70:
            return AccuracyLevel.FAIR
        elif self.accuracy >= 50:
            return AccuracyLevel.POOR
        else:
            return AccuracyLevel.FAILED

    def add_metric(
        self,
        name: str,
        value: float,
        expected: Optional[float] = None,
        unit: str = "percent",
        details: Optional[Dict] = None,
    ):
        """Add a metric measurement."""
        metric = MetricValue(
            name=name, value=value, expected=expected, unit=unit, details=details or {}
        )
        self.metrics.append(metric)

    def calculate_accuracy(self):
        """Recalculate overall accuracy from metrics."""
        if not self.metrics:
            self.accuracy = 100.0 if self.success else 0.0
        else:
            accuracies = [m.accuracy for m in self.metrics]
            self.accuracy = sum(accuracies) / len(accuracies)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "stage_name": self.stage_name,
            "success": self.success,
            "accuracy": self.accuracy,
            "accuracy_level": self.accuracy_level.value,
            "metrics": [m.to_dict() for m in self.metrics],
            "errors": self.errors,
            "warnings": self.warnings,
            "execution_time": self.execution_time,
            "output_size": self.output_size,
            "details": self.details,
        }


@dataclass
class AccuracyMetrics:
    """Comprehensive accuracy metrics for pipeline conversion."""

    # File information
    source_file: str
    source_size: int
    source_type: str

    # Stage results
    stage_results: Dict[str, StageResult] = field(default_factory=dict)

    # Overall metrics
    overall_accuracy: float = 0.0
    total_execution_time: float = 0.0

    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Additional details
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_stage_result(self, result: StageResult):
        """Add a stage result."""
        self.stage_results[result.stage_name] = result
        self._recalculate_overall()

    def _recalculate_overall(self):
        """Recalculate overall metrics."""
        if not self.stage_results:
            self.overall_accuracy = 0.0
            self.total_execution_time = 0.0
            return

        # Calculate average accuracy across all stages
        accuracies = [r.accuracy for r in self.stage_results.values()]
        self.overall_accuracy = sum(accuracies) / len(accuracies)

        # Sum execution times
        self.total_execution_time = sum(
            r.execution_time for r in self.stage_results.values()
        )

    @property
    def overall_level(self) -> AccuracyLevel:
        """Determine overall accuracy level."""
        if self.overall_accuracy >= 100:
            return AccuracyLevel.PERFECT
        elif self.overall_accuracy >= 95:
            return AccuracyLevel.EXCELLENT
        elif self.overall_accuracy >= 85:
            return AccuracyLevel.GOOD
        elif self.overall_accuracy >= 70:
            return AccuracyLevel.FAIR
        elif self.overall_accuracy >= 50:
            return AccuracyLevel.POOR
        else:
            return AccuracyLevel.FAILED

    def get_stage_accuracy(self, stage_name: str) -> Optional[float]:
        """Get accuracy for a specific stage."""
        if stage_name in self.stage_results:
            return self.stage_results[stage_name].accuracy
        return None

    def get_failed_stages(self) -> List[str]:
        """Get list of failed stages."""
        return [
            name for name, result in self.stage_results.items() if not result.success
        ]

    def get_low_accuracy_stages(self, threshold: float = 70.0) -> List[tuple]:
        """Get stages below accuracy threshold."""
        return [
            (name, result.accuracy)
            for name, result in self.stage_results.items()
            if result.accuracy < threshold
        ]

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "source_file": self.source_file,
            "source_size": self.source_size,
            "source_type": self.source_type,
            "overall_accuracy": self.overall_accuracy,
            "overall_level": self.overall_level.value,
            "total_execution_time": self.total_execution_time,
            "stage_results": {
                name: result.to_dict() for name, result in self.stage_results.items()
            },
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "metadata": self.metadata,
        }

    def save_to_file(self, path: Path):
        """Save metrics to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, path: Path) -> "AccuracyMetrics":
        """Load metrics from JSON file."""
        with open(path) as f:
            data = json.load(f)

        # Reconstruct object
        metrics = cls(
            source_file=data["source_file"],
            source_size=data["source_size"],
            source_type=data["source_type"],
        )

        # Reconstruct stage results
        for name, result_data in data.get("stage_results", {}).items():
            result = StageResult(
                stage_name=result_data["stage_name"],
                success=result_data["success"],
                accuracy=result_data["accuracy"],
                errors=result_data.get("errors", []),
                warnings=result_data.get("warnings", []),
                execution_time=result_data.get("execution_time", 0.0),
                output_size=result_data.get("output_size", 0),
                details=result_data.get("details", {}),
            )

            # Reconstruct metrics
            for metric_data in result_data.get("metrics", []):
                metric = MetricValue(
                    name=metric_data["name"],
                    value=metric_data["value"],
                    expected=metric_data.get("expected"),
                    unit=metric_data.get("unit", "percent"),
                    details=metric_data.get("details", {}),
                )
                result.metrics.append(metric)

            metrics.stage_results[name] = result

        metrics.overall_accuracy = data.get("overall_accuracy", 0.0)
        metrics.total_execution_time = data.get("total_execution_time", 0.0)
        metrics.metadata = data.get("metadata", {})

        if data.get("started_at"):
            metrics.started_at = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            metrics.completed_at = datetime.fromisoformat(data["completed_at"])

        return metrics


class AccuracyCalculator:
    """Calculate accuracy metrics for different pipeline stages."""

    @staticmethod
    def calculate_extraction_accuracy(
        extracted_files: int, expected_files: int, extracted_size: int, source_size: int
    ) -> StageResult:
        """Calculate extraction stage accuracy."""
        result = StageResult(stage_name="extract", success=extracted_files > 0)

        # File count accuracy
        result.add_metric("file_count", extracted_files, expected_files, unit="files")

        # Size preservation
        if source_size > 0:
            size_ratio = (extracted_size / source_size) * 100
            result.add_metric("size_preservation", size_ratio, 100, unit="percent")

        result.calculate_accuracy()
        return result

    @staticmethod
    def calculate_decompile_accuracy(
        decompiled_functions: int,
        total_functions: int,
        successful_opcodes: int,
        total_opcodes: int,
    ) -> StageResult:
        """Calculate decompile stage accuracy."""
        result = StageResult(stage_name="decompile", success=decompiled_functions > 0)

        # Function decompilation rate
        result.add_metric(
            "function_decompilation",
            decompiled_functions,
            total_functions,
            unit="functions",
        )

        # Opcode recognition rate
        if total_opcodes > 0:
            result.add_metric(
                "opcode_recognition", successful_opcodes, total_opcodes, unit="opcodes"
            )

        result.calculate_accuracy()
        return result

    @staticmethod
    def calculate_parse_accuracy(
        parsed_objects: int,
        total_objects: int,
        valid_syntax: int,
        total_statements: int,
    ) -> StageResult:
        """Calculate parse stage accuracy."""
        result = StageResult(stage_name="parse", success=parsed_objects > 0)

        # Object parsing rate
        result.add_metric(
            "object_parsing", parsed_objects, total_objects, unit="objects"
        )

        # Syntax validity rate
        if total_statements > 0:
            result.add_metric(
                "syntax_validity", valid_syntax, total_statements, unit="statements"
            )

        result.calculate_accuracy()
        return result

    @staticmethod
    def calculate_model_accuracy(
        resolved_dependencies: int, total_dependencies: int, semantic_validity: float
    ) -> StageResult:
        """Calculate model stage accuracy."""
        result = StageResult(stage_name="model", success=semantic_validity > 50)

        # Dependency resolution
        if total_dependencies > 0:
            result.add_metric(
                "dependency_resolution",
                resolved_dependencies,
                total_dependencies,
                unit="dependencies",
            )

        # Semantic validity
        result.add_metric("semantic_validity", semantic_validity, 100, unit="percent")

        result.calculate_accuracy()
        return result

    @staticmethod
    def calculate_generate_accuracy(
        generated_files: int,
        expected_files: int,
        compilable_code: bool,
        test_coverage: float,
    ) -> StageResult:
        """Calculate generate stage accuracy."""
        result = StageResult(stage_name="generate", success=generated_files > 0)

        # File generation rate
        result.add_metric(
            "file_generation", generated_files, expected_files, unit="files"
        )

        # Code quality
        result.add_metric(
            "compilable", 100 if compilable_code else 0, 100, unit="percent"
        )

        # Test coverage
        result.add_metric(
            "test_coverage",
            test_coverage,
            80,  # Target 80% coverage
            unit="percent",
        )

        result.calculate_accuracy()
        return result


class MetricsAggregator:
    """Aggregate metrics across multiple test runs."""

    def __init__(self):
        self.metrics_list: List[AccuracyMetrics] = []

    def add_metrics(self, metrics: AccuracyMetrics):
        """Add a metrics result."""
        self.metrics_list.append(metrics)

    def get_average_accuracy(self) -> float:
        """Get average accuracy across all runs."""
        if not self.metrics_list:
            return 0.0

        accuracies = [m.overall_accuracy for m in self.metrics_list]
        return sum(accuracies) / len(accuracies)

    def get_stage_averages(self) -> Dict[str, float]:
        """Get average accuracy for each stage."""
        stage_accuracies = {}
        stage_counts = {}

        for metrics in self.metrics_list:
            for stage_name, result in metrics.stage_results.items():
                if stage_name not in stage_accuracies:
                    stage_accuracies[stage_name] = 0.0
                    stage_counts[stage_name] = 0

                stage_accuracies[stage_name] += result.accuracy
                stage_counts[stage_name] += 1

        # Calculate averages
        return {
            stage: acc / stage_counts[stage] for stage, acc in stage_accuracies.items()
        }

    def get_failure_rate(self) -> Dict[str, float]:
        """Get failure rate for each stage."""
        stage_failures = {}
        stage_counts = {}

        for metrics in self.metrics_list:
            for stage_name, result in metrics.stage_results.items():
                if stage_name not in stage_failures:
                    stage_failures[stage_name] = 0
                    stage_counts[stage_name] = 0

                if not result.success:
                    stage_failures[stage_name] += 1
                stage_counts[stage_name] += 1

        # Calculate failure rates
        return {
            stage: (failures / stage_counts[stage]) * 100
            for stage, failures in stage_failures.items()
        }

    def generate_summary(self) -> dict:
        """Generate summary statistics."""
        return {
            "total_runs": len(self.metrics_list),
            "average_accuracy": self.get_average_accuracy(),
            "stage_averages": self.get_stage_averages(),
            "failure_rates": self.get_failure_rate(),
            "best_run": max(
                self.metrics_list, key=lambda m: m.overall_accuracy
            ).source_file
            if self.metrics_list
            else None,
            "worst_run": min(
                self.metrics_list, key=lambda m: m.overall_accuracy
            ).source_file
            if self.metrics_list
            else None,
        }
