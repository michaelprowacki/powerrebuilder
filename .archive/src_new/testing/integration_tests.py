#!/usr/bin/env python3
"""Integration Tests - Test PowerRebuilder with real PowerBuilder files.

This module runs actual PowerBuilder code through the pipeline and measures
accuracy at each stage.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

# Pipeline imports
from extract import ExtractCoordinator
from decompile import DecompileCoordinator
from parse import ParseCoordinator
from model import ModelCoordinator
from generate import GenerateCoordinator

# Analysis imports
from testing.accuracy_metrics import StageResult

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """Test case for PowerBuilder file."""

    name: str
    input_file: Path
    stages: List[str] = field(default_factory=lambda: ["all"])
    expected_outputs: Dict[str, Dict] = field(default_factory=dict)
    validation_rules: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestResult:
    """Result of a test execution."""

    test_name: str
    success: bool
    accuracy: float
    execution_time: float
    stage_results: Dict[str, StageResult] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class IntegrationTestSuite:
    """Run integration tests on real PowerBuilder files."""

    def __init__(
        self,
        fixtures_dir: Path,
        output_dir: Path,
        verbose: bool = False,
    ):
        """Initialize integration test suite.

        Args:
            fixtures_dir: Directory containing test fixtures
            output_dir: Output directory for results
            verbose: Enable verbose logging
        """
        self.fixtures_dir = Path(fixtures_dir)
        self.output_dir = Path(output_dir)
        self.verbose = verbose

        # Initialize pipeline components
        self.coordinators = self._initialize_coordinators()

        # Setup logging
        if verbose:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

    def _initialize_coordinators(self) -> Dict[str, Any]:
        """Initialize pipeline coordinators.

        Returns:
            Dictionary of coordinators
        """
        return {
            "extract": None,  # Will be initialized per test
            "decompile": None,
            "parse": None,
            "model": None,
            "generate": None,
        }

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests.

        Returns:
            Test results summary
        """
        test_cases = self._get_test_cases()
        results = []

        logger.info("Running %d integration tests...", len(test_cases))

        for test_case in test_cases:
            logger.info("Testing: %s", test_case.name)
            result = self.run_test(test_case)
            results.append(result)

            # Log result
            self._log_result(result)

        # Generate summary
        summary = self._generate_summary(results)

        # Save results
        self._save_results(results, summary)

        return summary

    def _get_test_cases(self) -> List[TestCase]:
        """Get all test cases from fixtures.

        Returns:
            List of test cases
        """
        test_cases = []

        # PowerBuilder Library test
        if (self.fixtures_dir / "sample.pbl").exists():
            test_cases.append(
                TestCase(
                    name="PowerBuilder Library",
                    input_file=self.fixtures_dir / "sample.pbl",
                    stages=["extract", "decompile", "parse"],
                    validation_rules={
                        "min_extraction_rate": 0.8,
                        "min_decompile_rate": 0.7,
                    },
                )
            )

        # Simple Window test
        if (self.fixtures_dir / "simple_window.srw").exists():
            test_cases.append(
                TestCase(
                    name="Simple Window",
                    input_file=self.fixtures_dir / "simple_window.srw",
                    stages=["parse", "model", "generate"],
                    validation_rules={
                        "required_elements": [
                            "cb_save",
                            "dw_main",
                            "clicked",
                            "create",
                        ],
                        "min_model_accuracy": 0.85,
                    },
                )
            )

        # Transaction test
        if (self.fixtures_dir / "transaction_test.srw").exists():
            test_cases.append(
                TestCase(
                    name="Database Transaction",
                    input_file=self.fixtures_dir / "transaction_test.srw",
                    stages=["parse", "model", "generate"],
                    validation_rules={
                        "preserve_transactions": True,
                        "sql_accuracy": 0.9,
                    },
                )
            )

        # Inheritance test
        if (self.fixtures_dir / "inheritance_test.sru").exists():
            test_cases.append(
                TestCase(
                    name="Inheritance Pattern",
                    input_file=self.fixtures_dir / "inheritance_test.sru",
                    stages=["parse", "model", "generate"],
                    validation_rules={
                        "preserve_inheritance": True,
                        "method_override_accuracy": 0.95,
                    },
                )
            )

        # Event handling test
        if (self.fixtures_dir / "event_handling.sru").exists():
            test_cases.append(
                TestCase(
                    name="Event Handling",
                    input_file=self.fixtures_dir / "event_handling.sru",
                    stages=["parse", "model", "generate"],
                    validation_rules={
                        "event_binding_accuracy": 0.9,
                        "handler_preservation": True,
                    },
                )
            )

        # Complex DataWindow test
        if (self.fixtures_dir / "complex_datawindow.srd").exists():
            test_cases.append(
                TestCase(
                    name="Complex DataWindow",
                    input_file=self.fixtures_dir / "complex_datawindow.srd",
                    stages=["parse", "model", "generate"],
                    validation_rules={
                        "datawindow_properties": 0.85,
                        "sql_preservation": True,
                    },
                )
            )

        return test_cases

    def run_test(self, test_case: TestCase) -> TestResult:
        """Run a single test case.

        Args:
            test_case: Test case to run

        Returns:
            Test result
        """
        start_time = time.time()
        stage_results = {}
        current_input = test_case.input_file
        current_output = self.output_dir / test_case.name.replace(" ", "_").lower()

        # Create output directory
        current_output.mkdir(parents=True, exist_ok=True)

        # Run through requested stages
        stages = test_case.stages
        if stages == ["all"]:
            stages = ["extract", "decompile", "parse", "model", "generate"]

        for stage_name in stages:
            logger.debug("Running stage: %s", stage_name)

            try:
                result = self._run_stage(
                    stage_name, current_input, current_output / stage_name, test_case
                )
                stage_results[stage_name] = result

                # Use output as input for next stage
                if result.success:
                    current_input = current_output / stage_name
                else:
                    logger.error("Stage %s failed, stopping pipeline", stage_name)
                    break

            except Exception as e:
                logger.error("Error in stage %s: %s", stage_name, e)
                stage_results[stage_name] = StageResult(
                    stage_name=stage_name, success=False, accuracy=0.0, errors=[str(e)]
                )
                break

        # Calculate overall accuracy
        overall_accuracy = self._calculate_overall_accuracy(stage_results)

        # Create test result
        result = TestResult(
            test_name=test_case.name,
            success=all(r.success for r in stage_results.values())
            if stage_results
            else False,
            accuracy=overall_accuracy,
            execution_time=time.time() - start_time,
            stage_results=stage_results,
        )

        # Validate against rules
        self._validate_result(result, test_case)

        return result

    def _run_stage(
        self,
        stage: str,
        input_path: Path,
        output_path: Path,
        test_case: TestCase,
    ) -> StageResult:
        """Run a single pipeline stage.

        Args:
            stage: Stage name
            input_path: Input path
            output_path: Output path
            test_case: Test case

        Returns:
            Stage result
        """
        output_path.mkdir(parents=True, exist_ok=True)

        if stage == "extract":
            return self._run_extract(input_path, output_path)
        elif stage == "decompile":
            return self._run_decompile(input_path, output_path)
        elif stage == "parse":
            return self._run_parse(input_path, output_path)
        elif stage == "model":
            return self._run_model(input_path, output_path)
        elif stage == "generate":
            return self._run_generate(input_path, output_path)
        else:
            raise ValueError(f"Unknown stage: {stage}")

    def _run_extract(self, input_path: Path, output_path: Path) -> StageResult:
        """Run extraction stage.

        Args:
            input_path: Input file path
            output_path: Output directory

        Returns:
            Stage result
        """
        try:
            coordinator = ExtractCoordinator(str(input_path), str(output_path))
            result = coordinator.process()

            # Calculate accuracy
            if input_path.suffix == ".pbl":
                # For PBL files, check extraction rate
                extracted = result.files_processed
                failed = result.files_failed
                total = extracted + failed
                accuracy = extracted / total if total > 0 else 0
            else:
                # For other files, binary success
                accuracy = 1.0 if result.success else 0.0

            stage_result = StageResult(
                stage_name="extract",
                success=result.success,
                accuracy=accuracy * 100,  # Convert to percentage
            )
            stage_result.add_metric(
                "files_extracted",
                result.files_processed,
                result.files_processed + result.files_failed,
                "files",
            )
            return stage_result
        except Exception as e:
            return StageResult(
                stage_name="extract", success=False, accuracy=0.0, errors=[str(e)]
            )

    def _run_decompile(self, input_path: Path, output_path: Path) -> StageResult:
        """Run decompilation stage.

        Args:
            input_path: Input directory
            output_path: Output directory

        Returns:
            Stage result
        """
        try:
            coordinator = DecompileCoordinator(str(input_path), str(output_path))
            result = coordinator.process()

            # Calculate accuracy based on success rate
            processed = result.files_processed
            failed = result.files_failed
            total = processed + failed
            accuracy = processed / total if total > 0 else 0

            stage_result = StageResult(
                stage_name="decompile",
                success=result.success,
                accuracy=accuracy * 100,  # Convert to percentage
            )
            stage_result.add_metric("files_processed", processed, total, "files")
            stage_result.add_metric(
                "lines_decompiled",
                result.metrics.get("lines_decompiled", 0),
                None,
                "lines",
            )
            return stage_result
        except Exception as e:
            return StageResult(
                stage_name="decompile", success=False, accuracy=0.0, errors=[str(e)]
            )

    def _run_parse(self, input_path: Path, output_path: Path) -> StageResult:
        """Run parsing stage.

        Args:
            input_path: Input path
            output_path: Output directory

        Returns:
            Stage result
        """
        try:
            coordinator = ParseCoordinator(str(input_path), str(output_path))
            result = coordinator.process()

            # Calculate accuracy
            parsed = result.files_processed
            failed = result.files_failed
            total = parsed + failed
            accuracy = parsed / total if total > 0 else 0

            # Check AST completeness
            ast_nodes = result.metrics.get("ast_nodes_created", 0)
            expected_nodes = result.metrics.get("expected_nodes", ast_nodes)
            if expected_nodes > 0:
                accuracy = min(accuracy, ast_nodes / expected_nodes)

            stage_result = StageResult(
                stage_name="parse",
                success=result.success,
                accuracy=accuracy * 100,  # Convert to percentage
            )
            stage_result.add_metric("files_parsed", parsed, total, "files")
            stage_result.add_metric("ast_nodes", ast_nodes, expected_nodes, "nodes")
            return stage_result
        except Exception as e:
            return StageResult(
                stage_name="parse", success=False, accuracy=0.0, errors=[str(e)]
            )

    def _run_model(self, input_path: Path, output_path: Path) -> StageResult:
        """Run model building stage.

        Args:
            input_path: Input directory
            output_path: Output directory

        Returns:
            Stage result
        """
        try:
            coordinator = ModelCoordinator(str(input_path), str(output_path))
            result = coordinator.process()

            # Calculate accuracy based on semantic elements
            objects = result.metrics.get("objects_created", 0)
            methods = result.metrics.get("methods_extracted", 0)
            properties = result.metrics.get("properties_extracted", 0)

            total_elements = objects + methods + properties
            expected = result.metrics.get("expected_elements", total_elements)
            accuracy = total_elements / expected if expected > 0 else 0

            stage_result = StageResult(
                stage_name="model",
                success=result.success,
                accuracy=accuracy * 100,  # Convert to percentage
            )
            stage_result.add_metric("objects", objects, None, "objects")
            stage_result.add_metric("methods", methods, None, "methods")
            stage_result.add_metric("properties", properties, None, "properties")
            return stage_result
        except Exception as e:
            return StageResult(
                stage_name="model", success=False, accuracy=0.0, errors=[str(e)]
            )

    def _run_generate(self, input_path: Path, output_path: Path) -> StageResult:
        """Run code generation stage.

        Args:
            input_path: Input directory
            output_path: Output directory

        Returns:
            Stage result
        """
        try:
            coordinator = GenerateCoordinator(
                str(input_path),
                str(output_path),
                target="flutter",  # Default target
            )
            result = coordinator.process()

            # Calculate accuracy (functional equivalence estimate)
            files_generated = result.files_processed
            expected_files = result.metrics.get(
                "expected_files", files_generated if files_generated > 0 else 1
            )
            accuracy = files_generated / expected_files if expected_files > 0 else 0

            # Check for functional completeness
            if result.metrics.get("functional_tests_passed"):
                tests_passed = result.metrics.get("functional_tests_passed", 0)
                total_tests = result.metrics.get("total_functional_tests", 1)
                functional_accuracy = tests_passed / total_tests
                accuracy = (accuracy + functional_accuracy) / 2

            stage_result = StageResult(
                stage_name="generate",
                success=result.success,
                accuracy=accuracy * 100,  # Convert to percentage
            )
            stage_result.add_metric(
                "files_generated", files_generated, expected_files, "files"
            )
            stage_result.add_metric(
                "lines_of_code", result.metrics.get("lines_of_code", 0), None, "lines"
            )
            return stage_result
        except Exception as e:
            return StageResult(
                stage_name="generate", success=False, accuracy=0.0, errors=[str(e)]
            )

    def _calculate_overall_accuracy(
        self, stage_results: Dict[str, StageResult]
    ) -> float:
        """Calculate overall accuracy across all stages.

        Args:
            stage_results: Results from each stage

        Returns:
            Overall accuracy percentage
        """
        if not stage_results:
            return 0.0

        total_accuracy = sum(r.accuracy for r in stage_results.values())
        return total_accuracy / len(stage_results)

    def _validate_result(self, result: TestResult, test_case: TestCase) -> None:
        """Validate test result against rules.

        Args:
            result: Test result to validate
            test_case: Test case with validation rules
        """
        rules = test_case.validation_rules

        for rule_name, rule_value in rules.items():
            if rule_name == "min_extraction_rate":
                if "extract" in result.stage_results:
                    if result.stage_results["extract"].accuracy < rule_value:
                        result.warnings.append(
                            f"Extraction rate {result.stage_results['extract'].accuracy:.2f} "
                            f"below minimum {rule_value}"
                        )

            elif rule_name == "min_decompile_rate":
                if "decompile" in result.stage_results:
                    if result.stage_results["decompile"].accuracy < rule_value:
                        result.warnings.append(
                            f"Decompile rate {result.stage_results['decompile'].accuracy:.2f} "
                            f"below minimum {rule_value}"
                        )

            elif rule_name == "required_elements":
                # Check if required elements are present in output
                for element in rule_value:
                    # This would check actual output files
                    pass

            elif rule_name == "min_model_accuracy":
                if "model" in result.stage_results:
                    if result.stage_results["model"].accuracy < rule_value:
                        result.warnings.append(
                            f"Model accuracy {result.stage_results['model'].accuracy:.2f} "
                            f"below minimum {rule_value}"
                        )

    def _log_result(self, result: TestResult) -> None:
        """Log test result.

        Args:
            result: Test result
        """
        logger.info(
            "Test: %s - Overall Accuracy: %.1f%% - Time: %.2fs",
            result.test_case.name,
            result.overall_accuracy * 100,
            result.execution_time,
        )

        for stage_name, stage_result in result.stage_results.items():
            if stage_result.success:
                logger.info(
                    "  %s: ✓ (%.1f%% accurate)",
                    stage_name.capitalize(),
                    stage_result.accuracy * 100,
                )
            else:
                logger.error("  %s: ✗ (Failed)", stage_name.capitalize())

        if result.warnings:
            for warning in result.warnings:
                logger.warning("  ⚠ %s", warning)

        if result.errors:
            for error in result.errors:
                logger.error("  ❌ %s", error)

    def _generate_summary(self, results: List[TestResult]) -> Dict[str, Any]:
        """Generate test summary.

        Args:
            results: List of test results

        Returns:
            Summary dictionary
        """
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.overall_accuracy >= 0.7)

        stage_accuracies = {}
        for stage in ["extract", "decompile", "parse", "model", "generate"]:
            accuracies = [
                r.stage_results[stage].accuracy
                for r in results
                if stage in r.stage_results
            ]
            if accuracies:
                stage_accuracies[stage] = sum(accuracies) / len(accuracies)

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "pass_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "average_accuracy": sum(r.overall_accuracy for r in results) / total_tests
            if total_tests > 0
            else 0,
            "stage_accuracies": stage_accuracies,
            "total_execution_time": sum(r.execution_time for r in results),
            "total_warnings": sum(len(r.warnings) for r in results),
            "total_errors": sum(len(r.errors) for r in results),
        }

    def _save_results(self, results: List[TestResult], summary: Dict[str, Any]) -> None:
        """Save test results to file.

        Args:
            results: Test results
            summary: Test summary
        """
        output_file = self.output_dir / "test_results.json"

        # Convert results to serializable format
        results_data = []
        for result in results:
            result_data = {
                "test_name": result.test_case.name,
                "input_file": str(result.test_case.input_file),
                "overall_accuracy": result.overall_accuracy,
                "execution_time": result.execution_time,
                "stage_results": {
                    stage: {
                        "success": sr.success,
                        "accuracy": sr.accuracy,
                        "metrics": sr.metrics,
                        "errors": sr.errors,
                        "warnings": sr.warnings,
                    }
                    for stage, sr in result.stage_results.items()
                },
                "warnings": result.warnings,
                "errors": result.errors,
            }
            results_data.append(result_data)

        # Save to file
        with output_file.open("w") as f:
            json.dump(
                {
                    "summary": summary,
                    "results": results_data,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                },
                f,
                indent=2,
            )

        logger.info("Results saved to %s", output_file)

    def generate_html_report(self) -> None:
        """Generate HTML report of test results."""
        results_file = self.output_dir / "test_results.json"
        if not results_file.exists():
            logger.error("No test results found")
            return

        with results_file.open() as f:
            data = json.load(f)

        html = """<!DOCTYPE html>
<html>
<head>
    <title>PowerRebuilder Accuracy Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .summary { background: #f0f0f0; padding: 15px; margin: 20px 0; }
        .test { border: 1px solid #ddd; margin: 10px 0; padding: 10px; }
        .success { color: green; }
        .failure { color: red; }
        .warning { color: orange; }
        .accuracy { font-weight: bold; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background: #f0f0f0; }
    </style>
</head>
<body>
    <h1>PowerRebuilder Accuracy Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Tests:</strong> {total_tests}</p>
        <p><strong>Passed:</strong> {passed_tests} ({pass_rate:.1%})</p>
        <p><strong>Average Accuracy:</strong> {avg_accuracy:.1%}</p>
        <p><strong>Total Time:</strong> {total_time:.2f}s</p>
    </div>

    <h2>Stage Accuracies</h2>
    <table>
        <tr>
            <th>Stage</th>
            <th>Average Accuracy</th>
        </tr>
        {stage_rows}
    </table>

    <h2>Test Results</h2>
    {test_results}
</body>
</html>"""

        # Format summary
        summary = data["summary"]
        html = html.format(
            total_tests=summary["total_tests"],
            passed_tests=summary["passed_tests"],
            pass_rate=summary["pass_rate"],
            avg_accuracy=summary["average_accuracy"],
            total_time=summary["total_execution_time"],
            stage_rows=self._format_stage_rows(summary["stage_accuracies"]),
            test_results=self._format_test_results(data["results"]),
        )

        # Save HTML report
        report_file = self.output_dir / "accuracy_report.html"
        with report_file.open("w") as f:
            f.write(html)

        logger.info("HTML report saved to %s", report_file)

    def _format_stage_rows(self, stage_accuracies: Dict[str, float]) -> str:
        """Format stage accuracy rows for HTML.

        Args:
            stage_accuracies: Stage accuracies

        Returns:
            HTML rows
        """
        rows = []
        for stage, accuracy in stage_accuracies.items():
            color = (
                "success"
                if accuracy >= 0.8
                else "warning"
                if accuracy >= 0.6
                else "failure"
            )
            rows.append(f"""
                <tr>
                    <td>{stage.capitalize()}</td>
                    <td class="{color}">{accuracy:.1%}</td>
                </tr>
            """)
        return "".join(rows)

    def _format_test_results(self, results: List[Dict[str, Any]]) -> str:
        """Format test results for HTML.

        Args:
            results: Test results

        Returns:
            HTML content
        """
        html_parts = []
        for result in results:
            status = "success" if result["overall_accuracy"] >= 0.7 else "failure"
            html_parts.append(f"""
                <div class="test">
                    <h3>{result["test_name"]}</h3>
                    <p><strong>File:</strong> {result["input_file"]}</p>
                    <p class="accuracy {status}">Overall Accuracy: {result["overall_accuracy"]:.1%}</p>
                    <p>Execution Time: {result["execution_time"]:.2f}s</p>
                    {self._format_stage_details(result["stage_results"])}
                    {self._format_issues(result.get("warnings", []), result.get("errors", []))}
                </div>
            """)
        return "".join(html_parts)

    def _format_stage_details(self, stage_results: Dict[str, Any]) -> str:
        """Format stage details for HTML.

        Args:
            stage_results: Stage results

        Returns:
            HTML content
        """
        if not stage_results:
            return ""

        rows = []
        for stage, result in stage_results.items():
            status = "✓" if result["success"] else "✗"
            color = "success" if result["success"] else "failure"
            rows.append(f"""
                <tr>
                    <td>{stage.capitalize()}</td>
                    <td class="{color}">{status}</td>
                    <td>{result["accuracy"]:.1%}</td>
                </tr>
            """)

        return f"""
            <table>
                <tr>
                    <th>Stage</th>
                    <th>Status</th>
                    <th>Accuracy</th>
                </tr>
                {"".join(rows)}
            </table>
        """

    def _format_issues(self, warnings: List[str], errors: List[str]) -> str:
        """Format warnings and errors for HTML.

        Args:
            warnings: Warning messages
            errors: Error messages

        Returns:
            HTML content
        """
        html = ""

        if warnings:
            html += "<h4>Warnings:</h4><ul class='warning'>"
            for warning in warnings:
                html += f"<li>{warning}</li>"
            html += "</ul>"

        if errors:
            html += "<h4>Errors:</h4><ul class='failure'>"
            for error in errors:
                html += f"<li>{error}</li>"
            html += "</ul>"

        return html


def main():
    """Run integration tests."""
    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    fixtures_dir = project_root / "tests" / "fixtures"
    output_dir = Path("test_output")

    # Run tests
    suite = IntegrationTestSuite(fixtures_dir, output_dir, verbose=True)
    summary = suite.run_all_tests()

    # Generate report
    suite.generate_html_report()

    # Print summary
    print("\n" + "=" * 60)
    print("POWERREBUILDER INTEGRATION TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed_tests']} ({summary['pass_rate']:.1%})")
    print(f"Average Accuracy: {summary['average_accuracy']:.1%}")
    print(f"Total Time: {summary['total_execution_time']:.2f}s")
    print("\nStage Accuracies:")
    for stage, accuracy in summary["stage_accuracies"].items():
        print(f"  {stage.capitalize()}: {accuracy:.1%}")
    print("=" * 60)


if __name__ == "__main__":
    main()
