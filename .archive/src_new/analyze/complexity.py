"""Code Complexity Analysis - Analyze code complexity and quality metrics.

This module provides comprehensive code analysis including cyclomatic complexity,
maintainability index, code smells detection, and technical debt assessment.
"""

import ast
import json
import logging
import math
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ComplexityLevel(str, Enum):
    """Complexity level categories."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class CodeSmellType(str, Enum):
    """Types of code smells."""

    LONG_METHOD = "long_method"
    LARGE_CLASS = "large_class"
    LONG_PARAMETER_LIST = "long_parameter_list"
    DUPLICATE_CODE = "duplicate_code"
    DEAD_CODE = "dead_code"
    GOD_CLASS = "god_class"
    FEATURE_ENVY = "feature_envy"
    DATA_CLUMPS = "data_clumps"
    PRIMITIVE_OBSESSION = "primitive_obsession"
    SWITCH_STATEMENTS = "switch_statements"


@dataclass
class MethodMetrics:
    """Metrics for a single method/function."""

    name: str
    lines_of_code: int
    cyclomatic_complexity: int
    cognitive_complexity: int
    parameter_count: int
    return_points: int
    nesting_depth: int
    maintainability_index: float
    complexity_level: ComplexityLevel


@dataclass
class ClassMetrics:
    """Metrics for a class."""

    name: str
    lines_of_code: int
    method_count: int
    property_count: int
    cyclomatic_complexity: int
    coupling: int  # Number of dependencies
    cohesion: float  # LCOM (Lack of Cohesion of Methods)
    depth_of_inheritance: int
    methods: List[MethodMetrics] = field(default_factory=list)


@dataclass
class FileMetrics:
    """Metrics for a single file."""

    path: str
    language: str
    lines_of_code: int
    lines_of_comments: int
    blank_lines: int
    cyclomatic_complexity: int
    maintainability_index: float
    technical_debt_ratio: float
    classes: List[ClassMetrics] = field(default_factory=list)
    functions: List[MethodMetrics] = field(default_factory=list)
    code_smells: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CodeSmell:
    """Detected code smell."""

    type: CodeSmellType
    severity: str  # low, medium, high
    location: str  # file:line
    message: str
    suggestion: str


class ComplexityAnalyzer:
    """Analyze code complexity metrics."""

    def __init__(self):
        """Initialize complexity analyzer."""
        self.thresholds = {
            "max_method_lines": 30,
            "max_class_lines": 300,
            "max_parameters": 5,
            "max_cyclomatic_complexity": 10,
            "max_nesting_depth": 4,
            "min_maintainability_index": 20,
        }

    def analyze_file(self, file_path: Path) -> FileMetrics:
        """Analyze a single file.

        Args:
            file_path: Path to file

        Returns:
            File metrics
        """
        # Determine language
        language = self._detect_language(file_path)

        # Read file content
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.error("Failed to read %s: %s", file_path, e)
            return FileMetrics(
                path=str(file_path),
                language=language,
                lines_of_code=0,
                lines_of_comments=0,
                blank_lines=0,
                cyclomatic_complexity=0,
                maintainability_index=0,
                technical_debt_ratio=0,
            )

        # Count lines
        lines = content.splitlines()
        loc, comments, blanks = self._count_lines(lines, language)

        # Create metrics object
        metrics = FileMetrics(
            path=str(file_path),
            language=language,
            lines_of_code=loc,
            lines_of_comments=comments,
            blank_lines=blanks,
            cyclomatic_complexity=0,
            maintainability_index=0,
            technical_debt_ratio=0,
        )

        # Analyze based on language
        if language == "python":
            self._analyze_python(content, metrics)
        elif language == "powerbuilder":
            self._analyze_powerbuilder(content, metrics)
        elif language in ["javascript", "typescript"]:
            self._analyze_javascript(content, metrics)

        # Calculate overall metrics
        self._calculate_file_metrics(metrics)

        # Detect code smells
        metrics.code_smells = self._detect_code_smells(metrics)

        return metrics

    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension.

        Args:
            file_path: File path

        Returns:
            Language name
        """
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".sru": "powerbuilder",
            ".srw": "powerbuilder",
            ".srm": "powerbuilder",
            ".fun": "powerbuilder",
        }
        return ext_map.get(file_path.suffix.lower(), "unknown")

    def _count_lines(self, lines: List[str], language: str) -> Tuple[int, int, int]:
        """Count lines of code, comments, and blank lines.

        Args:
            lines: File lines
            language: Programming language

        Returns:
            Tuple of (loc, comments, blanks)
        """
        loc = 0
        comments = 0
        blanks = 0

        in_multiline_comment = False

        for line in lines:
            stripped = line.strip()

            # Blank line
            if not stripped:
                blanks += 1
                continue

            # Comments (simplified detection)
            if language in ["python"]:
                if stripped.startswith("#"):
                    comments += 1
                elif stripped.startswith('"""') or stripped.startswith("'''"):
                    in_multiline_comment = not in_multiline_comment
                    comments += 1
                elif in_multiline_comment:
                    comments += 1
                else:
                    loc += 1
            elif language in ["javascript", "typescript", "powerbuilder"]:
                if stripped.startswith("//"):
                    comments += 1
                elif stripped.startswith("/*"):
                    in_multiline_comment = True
                    comments += 1
                elif stripped.endswith("*/"):
                    in_multiline_comment = False
                    comments += 1
                elif in_multiline_comment:
                    comments += 1
                else:
                    loc += 1
            else:
                loc += 1

        return loc, comments, blanks

    def _analyze_python(self, content: str, metrics: FileMetrics) -> None:
        """Analyze Python code.

        Args:
            content: File content
            metrics: Metrics object to update
        """
        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_metrics = self._analyze_python_class(node)
                    metrics.classes.append(class_metrics)
                elif isinstance(node, ast.FunctionDef) and not any(
                    isinstance(parent, ast.ClassDef) for parent in ast.walk(tree)
                ):
                    func_metrics = self._analyze_python_function(node)
                    metrics.functions.append(func_metrics)

        except SyntaxError as e:
            logger.warning("Failed to parse Python code: %s", e)

    def _analyze_python_class(self, node: ast.ClassDef) -> ClassMetrics:
        """Analyze a Python class.

        Args:
            node: AST node for class

        Returns:
            Class metrics
        """
        class_metrics = ClassMetrics(
            name=node.name,
            lines_of_code=node.end_lineno - node.lineno + 1
            if hasattr(node, "end_lineno")
            else 0,
            method_count=0,
            property_count=0,
            cyclomatic_complexity=0,
            coupling=0,
            cohesion=0.0,
            depth_of_inheritance=0,
        )

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_metrics = self._analyze_python_function(item)
                class_metrics.methods.append(method_metrics)
                class_metrics.method_count += 1
                class_metrics.cyclomatic_complexity += (
                    method_metrics.cyclomatic_complexity
                )
            elif isinstance(item, ast.Assign):
                class_metrics.property_count += 1

        return class_metrics

    def _analyze_python_function(self, node: ast.FunctionDef) -> MethodMetrics:
        """Analyze a Python function.

        Args:
            node: AST node for function

        Returns:
            Method metrics
        """
        # Calculate cyclomatic complexity
        complexity = self._calculate_python_complexity(node)

        # Calculate cognitive complexity
        cognitive = self._calculate_cognitive_complexity(node)

        # Count parameters
        param_count = len(node.args.args)

        # Count return statements
        return_count = sum(1 for n in ast.walk(node) if isinstance(n, ast.Return))

        # Calculate nesting depth
        nesting = self._calculate_nesting_depth(node)

        # Lines of code
        loc = node.end_lineno - node.lineno + 1 if hasattr(node, "end_lineno") else 0

        # Maintainability index
        volume = loc * math.log2(param_count + 1) if param_count > 0 else loc
        mi = max(
            0, 171 - 5.2 * math.log(volume) - 0.23 * complexity - 16.2 * math.log(loc)
        )

        # Determine complexity level
        if complexity <= 5:
            level = ComplexityLevel.LOW
        elif complexity <= 10:
            level = ComplexityLevel.MODERATE
        elif complexity <= 20:
            level = ComplexityLevel.HIGH
        else:
            level = ComplexityLevel.VERY_HIGH

        return MethodMetrics(
            name=node.name,
            lines_of_code=loc,
            cyclomatic_complexity=complexity,
            cognitive_complexity=cognitive,
            parameter_count=param_count,
            return_points=return_count,
            nesting_depth=nesting,
            maintainability_index=mi,
            complexity_level=level,
        )

    def _calculate_python_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for Python function.

        Args:
            node: Function AST node

        Returns:
            Cyclomatic complexity
        """
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # and/or operators
                complexity += len(child.values) - 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1

        return complexity

    def _calculate_cognitive_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cognitive complexity.

        Args:
            node: Function AST node

        Returns:
            Cognitive complexity
        """
        # Simplified cognitive complexity calculation
        complexity = 0
        nesting_level = 0

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1 + nesting_level
                nesting_level += 1
            elif isinstance(child, ast.BoolOp):
                complexity += 1

        return complexity

    def _calculate_nesting_depth(self, node: ast.FunctionDef) -> int:
        """Calculate maximum nesting depth.

        Args:
            node: Function AST node

        Returns:
            Maximum nesting depth
        """
        max_depth = 0

        def get_depth(node, current_depth=0):
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)

            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.With)):
                    get_depth(child, current_depth + 1)
                else:
                    get_depth(child, current_depth)

        get_depth(node)
        return max_depth

    def _analyze_powerbuilder(self, content: str, metrics: FileMetrics) -> None:
        """Analyze PowerBuilder code.

        Args:
            content: File content
            metrics: Metrics object to update
        """
        # Simple pattern-based analysis for PowerBuilder
        lines = content.splitlines()

        # Find functions
        function_pattern = re.compile(
            r"^\s*(function|event)\s+(\w+)\s*\(", re.IGNORECASE
        )
        class_pattern = re.compile(r"^\s*type\s+(\w+)\s+from", re.IGNORECASE)

        current_function = None
        current_class = None
        function_start = 0

        for i, line in enumerate(lines):
            # Check for class
            class_match = class_pattern.match(line)
            if class_match:
                if current_class:
                    metrics.classes.append(current_class)
                current_class = ClassMetrics(
                    name=class_match.group(1),
                    lines_of_code=0,
                    method_count=0,
                    property_count=0,
                    cyclomatic_complexity=0,
                    coupling=0,
                    cohesion=0.0,
                    depth_of_inheritance=0,
                )

            # Check for function
            func_match = function_pattern.match(line)
            if func_match:
                if current_function:
                    # Complete previous function
                    current_function.lines_of_code = i - function_start
                    self._calculate_pb_complexity(
                        lines[function_start:i], current_function
                    )

                    if current_class:
                        current_class.methods.append(current_function)
                        current_class.method_count += 1
                    else:
                        metrics.functions.append(current_function)

                # Start new function
                current_function = MethodMetrics(
                    name=func_match.group(2),
                    lines_of_code=0,
                    cyclomatic_complexity=1,
                    cognitive_complexity=0,
                    parameter_count=0,
                    return_points=0,
                    nesting_depth=0,
                    maintainability_index=100,
                    complexity_level=ComplexityLevel.LOW,
                )
                function_start = i

        # Complete last function
        if current_function:
            current_function.lines_of_code = len(lines) - function_start
            self._calculate_pb_complexity(lines[function_start:], current_function)

            if current_class:
                current_class.methods.append(current_function)
            else:
                metrics.functions.append(current_function)

        # Complete last class
        if current_class:
            metrics.classes.append(current_class)

    def _calculate_pb_complexity(
        self, lines: List[str], metrics: MethodMetrics
    ) -> None:
        """Calculate PowerBuilder complexity.

        Args:
            lines: Function lines
            metrics: Method metrics to update
        """
        for line in lines:
            line_lower = line.lower().strip()

            # Control flow statements
            if any(
                keyword in line_lower
                for keyword in ["if ", "elseif ", "for ", "do ", "while ", "case "]
            ):
                metrics.cyclomatic_complexity += 1

            # Return statements
            if "return " in line_lower:
                metrics.return_points += 1

        # Update complexity level
        if metrics.cyclomatic_complexity <= 5:
            metrics.complexity_level = ComplexityLevel.LOW
        elif metrics.cyclomatic_complexity <= 10:
            metrics.complexity_level = ComplexityLevel.MODERATE
        elif metrics.cyclomatic_complexity <= 20:
            metrics.complexity_level = ComplexityLevel.HIGH
        else:
            metrics.complexity_level = ComplexityLevel.VERY_HIGH

    def _analyze_javascript(self, content: str, metrics: FileMetrics) -> None:
        """Analyze JavaScript/TypeScript code.

        Args:
            content: File content
            metrics: Metrics object to update
        """
        # Simple pattern-based analysis
        lines = content.splitlines()

        # Patterns
        function_pattern = re.compile(
            r"^\s*(function|const|let|var)\s+(\w+)\s*[=:]?\s*(?:function)?\s*\(",
            re.IGNORECASE,
        )
        class_pattern = re.compile(r"^\s*class\s+(\w+)", re.IGNORECASE)

        for i, line in enumerate(lines):
            # Check for class
            class_match = class_pattern.match(line)
            if class_match:
                class_metrics = ClassMetrics(
                    name=class_match.group(1),
                    lines_of_code=0,
                    method_count=0,
                    property_count=0,
                    cyclomatic_complexity=0,
                    coupling=0,
                    cohesion=0.0,
                    depth_of_inheritance=0,
                )
                metrics.classes.append(class_metrics)

            # Check for function
            func_match = function_pattern.match(line)
            if func_match:
                func_metrics = MethodMetrics(
                    name=func_match.group(2)
                    if func_match.lastindex >= 2
                    else "anonymous",
                    lines_of_code=0,
                    cyclomatic_complexity=1,
                    cognitive_complexity=0,
                    parameter_count=0,
                    return_points=0,
                    nesting_depth=0,
                    maintainability_index=100,
                    complexity_level=ComplexityLevel.LOW,
                )
                metrics.functions.append(func_metrics)

    def _calculate_file_metrics(self, metrics: FileMetrics) -> None:
        """Calculate overall file metrics.

        Args:
            metrics: File metrics to update
        """
        # Total cyclomatic complexity
        total_complexity = sum(c.cyclomatic_complexity for c in metrics.classes)
        total_complexity += sum(f.cyclomatic_complexity for f in metrics.functions)
        metrics.cyclomatic_complexity = total_complexity

        # Maintainability index (average)
        all_mi = []
        for c in metrics.classes:
            all_mi.extend(m.maintainability_index for m in c.methods)
        all_mi.extend(f.maintainability_index for f in metrics.functions)

        if all_mi:
            metrics.maintainability_index = sum(all_mi) / len(all_mi)
        else:
            metrics.maintainability_index = 100

        # Technical debt ratio (simplified)
        # Based on complexity and maintainability
        if metrics.maintainability_index < 20:
            debt_ratio = 0.3
        elif metrics.maintainability_index < 50:
            debt_ratio = 0.2
        elif metrics.maintainability_index < 70:
            debt_ratio = 0.1
        else:
            debt_ratio = 0.05

        # Adjust for complexity
        if total_complexity > 50:
            debt_ratio += 0.1
        elif total_complexity > 100:
            debt_ratio += 0.2

        metrics.technical_debt_ratio = min(debt_ratio, 1.0)

    def _detect_code_smells(self, metrics: FileMetrics) -> List[Dict[str, Any]]:
        """Detect code smells in file.

        Args:
            metrics: File metrics

        Returns:
            List of detected code smells
        """
        smells = []

        # Check for long methods
        for func in metrics.functions:
            if func.lines_of_code > self.thresholds["max_method_lines"]:
                smells.append(
                    {
                        "type": CodeSmellType.LONG_METHOD.value,
                        "severity": "high" if func.lines_of_code > 50 else "medium",
                        "location": f"{metrics.path}:{func.name}",
                        "message": f"Method {func.name} has {func.lines_of_code} lines (threshold: {self.thresholds['max_method_lines']})",
                        "suggestion": "Consider breaking this method into smaller, more focused methods",
                    }
                )

            if func.parameter_count > self.thresholds["max_parameters"]:
                smells.append(
                    {
                        "type": CodeSmellType.LONG_PARAMETER_LIST.value,
                        "severity": "medium",
                        "location": f"{metrics.path}:{func.name}",
                        "message": f"Method {func.name} has {func.parameter_count} parameters",
                        "suggestion": "Consider using a parameter object or builder pattern",
                    }
                )

        # Check for large classes
        for cls in metrics.classes:
            if cls.lines_of_code > self.thresholds["max_class_lines"]:
                smells.append(
                    {
                        "type": CodeSmellType.LARGE_CLASS.value,
                        "severity": "high",
                        "location": f"{metrics.path}:{cls.name}",
                        "message": f"Class {cls.name} has {cls.lines_of_code} lines",
                        "suggestion": "Consider splitting into smaller, more focused classes",
                    }
                )

            # God class detection
            if cls.method_count > 20 or cls.property_count > 15:
                smells.append(
                    {
                        "type": CodeSmellType.GOD_CLASS.value,
                        "severity": "high",
                        "location": f"{metrics.path}:{cls.name}",
                        "message": f"Class {cls.name} has too many responsibilities",
                        "suggestion": "Apply Single Responsibility Principle",
                    }
                )

        return smells

    def generate_report(
        self, metrics_list: List[FileMetrics], output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Generate complexity analysis report.

        Args:
            metrics_list: List of file metrics
            output_path: Optional path to save report

        Returns:
            Report dictionary
        """
        report = {
            "summary": {
                "total_files": len(metrics_list),
                "total_lines": sum(m.lines_of_code for m in metrics_list),
                "average_complexity": 0,
                "average_maintainability": 0,
                "total_code_smells": 0,
            },
            "complexity_distribution": {
                "low": 0,
                "moderate": 0,
                "high": 0,
                "very_high": 0,
            },
            "top_complex_methods": [],
            "top_complex_files": [],
            "code_smells_summary": {},
            "files": [],
        }

        # Aggregate metrics
        all_methods = []
        all_smells = []

        for file_metrics in metrics_list:
            # Add file summary
            report["files"].append(
                {
                    "path": file_metrics.path,
                    "loc": file_metrics.lines_of_code,
                    "complexity": file_metrics.cyclomatic_complexity,
                    "maintainability": file_metrics.maintainability_index,
                    "debt_ratio": file_metrics.technical_debt_ratio,
                    "smells": len(file_metrics.code_smells),
                }
            )

            # Collect methods
            for cls in file_metrics.classes:
                all_methods.extend(cls.methods)
            all_methods.extend(file_metrics.functions)

            # Collect smells
            all_smells.extend(file_metrics.code_smells)

        # Calculate summary
        if metrics_list:
            report["summary"]["average_complexity"] = sum(
                m.cyclomatic_complexity for m in metrics_list
            ) / len(metrics_list)
            report["summary"]["average_maintainability"] = sum(
                m.maintainability_index for m in metrics_list
            ) / len(metrics_list)
            report["summary"]["total_code_smells"] = len(all_smells)

        # Complexity distribution
        for method in all_methods:
            report["complexity_distribution"][method.complexity_level.value] += 1

        # Top complex methods
        all_methods.sort(key=lambda m: m.cyclomatic_complexity, reverse=True)
        report["top_complex_methods"] = [
            {
                "name": m.name,
                "complexity": m.cyclomatic_complexity,
                "loc": m.lines_of_code,
            }
            for m in all_methods[:10]
        ]

        # Top complex files
        metrics_list.sort(key=lambda f: f.cyclomatic_complexity, reverse=True)
        report["top_complex_files"] = [
            {
                "path": f.path,
                "complexity": f.cyclomatic_complexity,
                "loc": f.lines_of_code,
            }
            for f in metrics_list[:10]
        ]

        # Code smells summary
        smell_counts = {}
        for smell in all_smells:
            smell_type = smell["type"]
            if smell_type not in smell_counts:
                smell_counts[smell_type] = 0
            smell_counts[smell_type] += 1
        report["code_smells_summary"] = smell_counts

        # Save report if path provided
        if output_path:
            with output_path.open("w") as f:
                json.dump(report, f, indent=2)
            logger.info("Complexity report saved to %s", output_path)

        return report
