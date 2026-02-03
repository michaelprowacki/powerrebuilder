"""Semantic validation for PowerBuilder code conversion.

This module validates the semantic correctness of converted PowerBuilder code,
ensuring that the transformation preserves business logic and functionality.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import logging

from src_new._core import (
    Event,
    PBObject,
    ObjectType,
)

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""

    ERROR = "error"  # Critical issue that breaks functionality
    WARNING = "warning"  # Issue that may affect behavior
    INFO = "info"  # Informational notice


@dataclass
class ValidationIssue:
    """A single validation issue."""

    severity: ValidationSeverity
    category: str
    message: str
    location: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of semantic validation."""

    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def error_count(self) -> int:
        """Count of error-level issues."""
        return sum(
            1 for issue in self.issues if issue.severity == ValidationSeverity.ERROR
        )

    @property
    def warning_count(self) -> int:
        """Count of warning-level issues."""
        return sum(
            1 for issue in self.issues if issue.severity == ValidationSeverity.WARNING
        )

    def add_issue(self, issue: ValidationIssue):
        """Add a validation issue."""
        self.issues.append(issue)
        # Mark as invalid if it's an error
        if issue.severity == ValidationSeverity.ERROR:
            self.valid = False


class SemanticValidator:
    """Validates semantic correctness of PowerBuilder models."""

    def __init__(self, strict_mode: bool = False):
        """Initialize validator.

        Args:
            strict_mode: Treat warnings as errors
        """
        self.strict_mode = strict_mode
        self.known_types: Set[str] = set()
        self.known_functions: Set[str] = set()
        self.known_events: Set[str] = set()

    def validate_object(self, pb_object: PBObject) -> ValidationResult:
        """Validate a PowerBuilder object.

        Args:
            pb_object: Object to validate

        Returns:
            Validation result
        """
        result = ValidationResult(valid=True)

        # Basic validation
        self._validate_object_structure(pb_object, result)

        # Type-specific validation
        if pb_object.object_type == ObjectType.WINDOW:
            self._validate_window(pb_object, result)
        elif pb_object.object_type == ObjectType.DATAWINDOW:
            self._validate_datawindow(pb_object, result)
        elif pb_object.object_type == ObjectType.USER_OBJECT:
            self._validate_user_object(pb_object, result)

        # Common validations
        self._validate_methods(pb_object, result)
        self._validate_properties(pb_object, result)
        self._validate_events(pb_object, result)
        self._validate_inheritance(pb_object, result)
        self._validate_dependencies(pb_object, result)

        # Calculate metrics
        result.metrics = self._calculate_metrics(pb_object)

        # Apply strict mode
        if self.strict_mode and result.warning_count > 0:
            result.valid = False

        return result

    def _validate_object_structure(self, pb_object: PBObject, result: ValidationResult):
        """Validate basic object structure."""
        # Check for required fields
        if not pb_object.name:
            result.add_issue(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="structure",
                    message="Object missing name",
                )
            )

        if not pb_object.object_type:
            result.add_issue(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="structure",
                    message="Object missing type",
                )
            )

        # Check for duplicate method names
        method_names = [m.name for m in pb_object.methods]
        duplicates = [name for name in method_names if method_names.count(name) > 1]
        for dup in set(duplicates):
            result.add_issue(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="structure",
                    message=f"Duplicate method name: {dup}",
                )
            )

        # Check for duplicate property names
        prop_names = [p.name for p in pb_object.properties]
        duplicates = [name for name in prop_names if prop_names.count(name) > 1]
        for dup in set(duplicates):
            result.add_issue(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="structure",
                    message=f"Duplicate property name: {dup}",
                )
            )

    def _validate_window(self, pb_object: PBObject, result: ValidationResult):
        """Validate window-specific semantics."""
        # Check for required window events
        event_names = [e.name for e in pb_object.events]

        if "open" not in event_names and "constructor" not in event_names:
            result.add_issue(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="window",
                    message="Window missing open/constructor event",
                )
            )

        # Check for controls
        if not pb_object.controls:
            result.add_issue(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category="window",
                    message="Window has no controls",
                )
            )

    def _validate_datawindow(self, pb_object: PBObject, result: ValidationResult):
        """Validate DataWindow-specific semantics."""
        # Check for data object
        has_dataobject = any(p.name == "dataobject" for p in pb_object.properties)
        if not has_dataobject:
            result.add_issue(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="datawindow",
                    message="DataWindow missing dataobject property",
                )
            )

        # Check for retrieve method
        has_retrieve = any(m.name == "retrieve" for m in pb_object.methods)
        if not has_retrieve:
            result.add_issue(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category="datawindow",
                    message="DataWindow missing retrieve method",
                )
            )

    def _validate_user_object(self, pb_object: PBObject, result: ValidationResult):
        """Validate user object semantics."""
        # User objects should have a constructor
        has_constructor = any(e.name == "constructor" for e in pb_object.events)
        if not has_constructor:
            result.add_issue(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category="user_object",
                    message="User object missing constructor",
                )
            )

    def _validate_methods(self, pb_object: PBObject, result: ValidationResult):
        """Validate method semantics."""
        for method in pb_object.methods:
            # Check return type
            if method.return_type and method.return_type not in self._get_valid_types():
                result.add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="method",
                        message=f"Unknown return type '{method.return_type}' in method {method.name}",
                        location=f"{pb_object.name}.{method.name}",
                    )
                )

            # Check parameter types
            for param in method.parameters:
                if param.data_type and param.data_type not in self._get_valid_types():
                    result.add_issue(
                        ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            category="method",
                            message=f"Unknown parameter type '{param.data_type}' in method {method.name}",
                            location=f"{pb_object.name}.{method.name}",
                        )
                    )

            # Check for empty implementation
            if not method.implementation or method.implementation.strip() == "":
                result.add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        category="method",
                        message=f"Empty method implementation: {method.name}",
                        location=f"{pb_object.name}.{method.name}",
                    )
                )

    def _validate_properties(self, pb_object: PBObject, result: ValidationResult):
        """Validate property semantics."""
        for prop in pb_object.properties:
            # Check property type
            if prop.type and prop.type not in self._get_valid_types():
                result.add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="property",
                        message=f"Unknown property type '{prop.type}' for {prop.name}",
                        location=f"{pb_object.name}.{prop.name}",
                    )
                )

            # Check for uninitialized required properties
            if prop.required and prop.initial_value is None:
                result.add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="property",
                        message=f"Required property not initialized: {prop.name}",
                        location=f"{pb_object.name}.{prop.name}",
                    )
                )

    def _validate_events(self, pb_object: PBObject, result: ValidationResult):
        """Validate event semantics."""
        for event in pb_object.events:
            # Check for standard events with wrong signatures
            if event.name in self._get_standard_events():
                expected_sig = self._get_standard_events()[event.name]
                if not self._matches_signature(event, expected_sig):
                    result.add_issue(
                        ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            category="event",
                            message=f"Non-standard signature for event {event.name}",
                            location=f"{pb_object.name}.{event.name}",
                        )
                    )

            # Check for empty event handlers
            if not event.handler or event.handler.strip() == "":
                result.add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        category="event",
                        message=f"Empty event handler: {event.name}",
                        location=f"{pb_object.name}.{event.name}",
                    )
                )

    def _validate_inheritance(self, pb_object: PBObject, result: ValidationResult):
        """Validate inheritance chain."""
        if pb_object.parent_class:
            # Check if parent exists
            if pb_object.parent_class not in self._get_known_classes():
                result.add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="inheritance",
                        message=f"Unknown parent class: {pb_object.parent_class}",
                    )
                )

            # Check for circular inheritance
            if self._has_circular_inheritance(pb_object):
                result.add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="inheritance",
                        message="Circular inheritance detected",
                    )
                )

    def _validate_dependencies(self, pb_object: PBObject, result: ValidationResult):
        """Validate object dependencies."""
        for dep in pb_object.dependencies:
            # Check if dependency exists
            if dep not in self._get_known_classes():
                result.add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="dependency",
                        message=f"Unknown dependency: {dep}",
                    )
                )

    def _calculate_metrics(self, pb_object: PBObject) -> Dict[str, Any]:
        """Calculate semantic metrics."""
        return {
            "method_count": len(pb_object.methods),
            "property_count": len(pb_object.properties),
            "event_count": len(pb_object.events),
            "control_count": len(pb_object.controls) if pb_object.controls else 0,
            "dependency_count": len(pb_object.dependencies),
            "complexity_score": self._calculate_complexity(pb_object),
            "completeness_score": self._calculate_completeness(pb_object),
        }

    def _calculate_complexity(self, pb_object: PBObject) -> int:
        """Calculate object complexity score."""
        score = 0

        # Method complexity
        score += len(pb_object.methods) * 2

        # Event complexity
        score += len(pb_object.events) * 3

        # Control complexity
        if pb_object.controls:
            score += len(pb_object.controls) * 2

        # Inheritance complexity
        if pb_object.parent_class:
            score += 5

        # Dependency complexity
        score += len(pb_object.dependencies) * 2

        return score

    def _calculate_completeness(self, pb_object: PBObject) -> float:
        """Calculate completeness score (0-100)."""
        total_points = 0
        earned_points = 0

        # Check for name
        total_points += 10
        if pb_object.name:
            earned_points += 10

        # Check for type
        total_points += 10
        if pb_object.object_type:
            earned_points += 10

        # Check for methods
        total_points += 20
        if pb_object.methods:
            earned_points += 20

        # Check for properties
        total_points += 20
        if pb_object.properties:
            earned_points += 20

        # Check for events
        total_points += 20
        if pb_object.events:
            earned_points += 20

        # Check for implementation
        total_points += 20
        non_empty_methods = sum(1 for m in pb_object.methods if m.implementation)
        if pb_object.methods:
            earned_points += int(20 * (non_empty_methods / len(pb_object.methods)))

        return (earned_points / total_points) * 100 if total_points > 0 else 0

    def _get_valid_types(self) -> Set[str]:
        """Get set of valid PowerBuilder types."""
        return {
            "integer",
            "long",
            "decimal",
            "real",
            "double",
            "boolean",
            "string",
            "char",
            "date",
            "datetime",
            "time",
            "blob",
            "any",
            "powerobject",
            "window",
            "datawindow",
            "menu",
            "userobject",
            "transaction",
            "application",
            "structure",
        }

    def _get_standard_events(self) -> Dict[str, Dict]:
        """Get standard event signatures."""
        return {
            "clicked": {"parameters": []},
            "constructor": {"parameters": []},
            "destructor": {"parameters": []},
            "open": {"parameters": []},
            "close": {"parameters": []},
            "activate": {"parameters": []},
            "deactivate": {"parameters": []},
            "resize": {
                "parameters": [
                    ("sizetype", "integer"),
                    ("newwidth", "integer"),
                    ("newheight", "integer"),
                ]
            },
        }

    def _get_known_classes(self) -> Set[str]:
        """Get known PowerBuilder classes."""
        # In real implementation, would load from project
        return {
            "window",
            "datawindow",
            "menu",
            "userobject",
            "transaction",
            "application",
            "commandbutton",
            "statictext",
            "singlelineedit",
            "multilineedit",
            "listbox",
            "dropdownlistbox",
            "checkbox",
            "radiobutton",
        }

    def _has_circular_inheritance(self, pb_object: PBObject) -> bool:
        """Check for circular inheritance."""
        # Simplified check - real implementation would traverse chain
        return False

    def _matches_signature(self, event: Event, expected: Dict) -> bool:
        """Check if event matches expected signature."""
        # Simplified check
        expected_params = expected.get("parameters", [])
        if len(event.parameters) != len(expected_params):
            return False

        # Check parameter types
        for i, param in enumerate(event.parameters):
            if i < len(expected_params):
                expected_type = expected_params[i][1]
                if param.data_type != expected_type:
                    return False

        return True


class CrossStageValidator:
    """Validates consistency across pipeline stages."""

    def __init__(self):
        """Initialize cross-stage validator."""
        self.stage_outputs = {}

    def add_stage_output(self, stage: str, output: Any):
        """Add output from a pipeline stage."""
        self.stage_outputs[stage] = output

    def validate_consistency(self) -> ValidationResult:
        """Validate consistency across stages."""
        result = ValidationResult(valid=True)

        # Validate extract -> decompile consistency
        if "extract" in self.stage_outputs and "decompile" in self.stage_outputs:
            self._validate_extract_decompile(result)

        # Validate decompile -> parse consistency
        if "decompile" in self.stage_outputs and "parse" in self.stage_outputs:
            self._validate_decompile_parse(result)

        # Validate parse -> model consistency
        if "parse" in self.stage_outputs and "model" in self.stage_outputs:
            self._validate_parse_model(result)

        # Validate model -> generate consistency
        if "model" in self.stage_outputs and "generate" in self.stage_outputs:
            self._validate_model_generate(result)

        return result

    def _validate_extract_decompile(self, result: ValidationResult):
        """Validate extract to decompile transition."""
        extract_files = self.stage_outputs["extract"].get("files", [])
        decompile_files = self.stage_outputs["decompile"].get("files", [])

        # Check file count consistency
        if len(extract_files) != len(decompile_files):
            result.add_issue(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="cross-stage",
                    message=f"File count mismatch: {len(extract_files)} extracted, {len(decompile_files)} decompiled",
                )
            )

    def _validate_decompile_parse(self, result: ValidationResult):
        """Validate decompile to parse transition."""
        # Check that all decompiled files were parsed
        pass

    def _validate_parse_model(self, result: ValidationResult):
        """Validate parse to model transition."""
        # Check AST to model conversion
        pass

    def _validate_model_generate(self, result: ValidationResult):
        """Validate model to generate transition."""
        # Check that all models were generated
        pass
