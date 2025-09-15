#!/usr/bin/env python3
"""
Comprehensive Test Runner for PowerRebuilder

Orchestrates the execution of the comprehensive test suite with proper
categorization, reporting, and performance analysis.

Usage:
    python run_comprehensive_tests.py [options]

Options:
    --fast: Run only fast tests (skip slow/performance tests)
    --security: Run only security-related tests
    --performance: Run only performance benchmarks
    --integration: Run only integration tests
    --coverage: Generate coverage report
    --parallel: Run tests in parallel
    --report: Generate comprehensive test report
"""

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class TestResult:
    """Result of a test execution."""

    category: str
    passed: int
    failed: int
    skipped: int
    errors: int
    duration: float
    coverage_percent: float | None = None


@dataclass
class TestReport:
    """Comprehensive test report."""

    timestamp: str
    total_duration: float
    overall_passed: int
    overall_failed: int
    overall_skipped: int
    overall_errors: int
    coverage_percent: float | None
    results_by_category: dict[str, TestResult]
    performance_regressions: list[str]
    security_issues: list[str]
    recommendations: list[str]


class ComprehensiveTestRunner:
    """Orchestrates comprehensive test execution."""

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.test_results: dict[str, TestResult] = {}

    def run_test_category(
        self,
        category: str,
        test_path: str,
        markers: list[str] = None,
        extra_args: list[str] = None,
    ) -> TestResult:
        """Run tests for a specific category."""
        print(f"\n{'=' * 60}")
        print(f"Running {category} tests...")
        print(f"{'=' * 60}")

        cmd = ["python", "-m", "pytest", test_path, "-v"]

        # Add markers
        if markers:
            for marker in markers:
                cmd.extend(["-m", marker])

        # Add extra arguments
        if extra_args:
            cmd.extend(extra_args)

        start_time = time.time()
        try:
            result = subprocess.run(
                cmd, check=False, cwd=self.base_dir, capture_output=True, text=True
            )
            duration = time.time() - start_time

            # Parse pytest output
            passed, failed, skipped, errors = self.parse_pytest_output(result.stdout)

            test_result = TestResult(
                category=category,
                passed=passed,
                failed=failed,
                skipped=skipped,
                errors=errors,
                duration=duration,
            )

            print(
                f"Results: {passed} passed, {failed} failed, {skipped} skipped, {errors} errors"
            )
            print(f"Duration: {duration:.2f}s")

            if result.returncode != 0 and failed == 0 and errors == 0:
                print(
                    "Warning: Test execution had issues but no test failures reported"
                )
                print("STDOUT:", result.stdout[-500:] if result.stdout else "None")
                print("STDERR:", result.stderr[-500:] if result.stderr else "None")

            return test_result

        except subprocess.CalledProcessError as e:
            print(f"Error running {category} tests: {e}")
            return TestResult(category, 0, 0, 0, 1, time.time() - start_time)
        except Exception as e:
            print(f"Unexpected error running {category} tests: {e}")
            return TestResult(category, 0, 0, 0, 1, time.time() - start_time)

    def parse_pytest_output(self, output: str) -> tuple[int, int, int, int]:
        """Parse pytest output to extract test counts."""
        passed = failed = skipped = errors = 0

        # Look for final summary line
        lines = output.split("\n")
        for line in reversed(lines):
            if "passed" in line or "failed" in line or "error" in line:
                # Parse summary line like "5 passed, 2 failed, 1 skipped in 10.23s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed" and i > 0:
                        try:
                            passed = int(parts[i - 1])
                        except ValueError:
                            pass
                    elif part == "failed" and i > 0:
                        try:
                            failed = int(parts[i - 1])
                        except ValueError:
                            pass
                    elif part == "skipped" and i > 0:
                        try:
                            skipped = int(parts[i - 1])
                        except ValueError:
                            pass
                    elif part == "error" and i > 0:
                        try:
                            errors = int(parts[i - 1])
                        except ValueError:
                            pass
                break

        return passed, failed, skipped, errors

    def run_coverage_analysis(self) -> float | None:
        """Run coverage analysis on the codebase."""
        print(f"\n{'=' * 60}")
        print("Running coverage analysis...")
        print(f"{'=' * 60}")

        cmd = [
            "python",
            "-m",
            "pytest",
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=json",
            "-x",  # Stop on first failure for coverage
        ]

        try:
            result = subprocess.run(
                cmd, check=False, cwd=self.base_dir, capture_output=True, text=True
            )

            # Parse coverage from JSON report
            coverage_file = self.base_dir / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file) as f:
                    coverage_data = json.load(f)
                    coverage_percent = coverage_data.get("totals", {}).get(
                        "percent_covered", 0
                    )
                    print(f"Overall coverage: {coverage_percent:.1f}%")
                    return coverage_percent

            # Fallback: parse from stdout
            for line in result.stdout.split("\n"):
                if "TOTAL" in line and "%" in line:
                    parts = line.split()
                    for part in parts:
                        if part.endswith("%"):
                            try:
                                return float(part[:-1])
                            except ValueError:
                                pass

        except Exception as e:
            print(f"Error running coverage analysis: {e}")

        return None

    def run_fast_tests(self) -> TestResult:
        """Run fast tests only."""
        return self.run_test_category(
            "Fast Tests",
            "tests/unit",
            markers=["not slow", "not performance"],
            extra_args=["--maxfail=10"],
        )

    def run_security_tests(self) -> TestResult:
        """Run security-related tests."""
        return self.run_test_category(
            "Security Tests",
            "tests/unit/generate/test_security_fixes.py",
            markers=["security"],
            extra_args=["--tb=long"],
        )

    def run_performance_tests(self) -> TestResult:
        """Run performance benchmarks."""
        return self.run_test_category(
            "Performance Tests",
            "tests/benchmarks",
            markers=["performance"],
            extra_args=["--benchmark-only", "--benchmark-sort=mean"],
        )

    def run_integration_tests(self) -> TestResult:
        """Run integration tests."""
        return self.run_test_category(
            "Integration Tests",
            "tests/integration",
            markers=["integration"],
            extra_args=["--maxfail=5"],
        )

    def run_tiered_detector_tests(self) -> TestResult:
        """Run TieredPCodeDetector comprehensive tests."""
        return self.run_test_category(
            "Tiered Detector Tests",
            "tests/unit/decompile/test_tiered_detector_comprehensive.py",
            extra_args=["--tb=short"],
        )

    def run_error_handling_tests(self) -> TestResult:
        """Run comprehensive error handling tests."""
        return self.run_test_category(
            "Error Handling Tests",
            "tests/unit/extract/test_error_handling_comprehensive.py",
            markers=["error_handling"],
            extra_args=["--tb=line"],
        )

    def analyze_performance_regressions(self) -> list[str]:
        """Analyze performance test results for regressions."""
        regressions = []

        # This would analyze benchmark results against baselines
        # For now, return empty list

        return regressions

    def identify_security_issues(self) -> list[str]:
        """Identify security issues from test results."""
        issues = []

        # Check if security tests failed
        if "Security Tests" in self.test_results:
            security_result = self.test_results["Security Tests"]
            if security_result.failed > 0 or security_result.errors > 0:
                issues.append(
                    f"Security tests failed: {security_result.failed} failed, {security_result.errors} errors"
                )

        return issues

    def generate_recommendations(self, coverage_percent: float | None) -> list[str]:
        """Generate recommendations based on test results."""
        recommendations = []

        # Coverage recommendations
        if coverage_percent is not None:
            if coverage_percent < 60:
                recommendations.append(
                    "CRITICAL: Test coverage is below 60%. Add more unit tests."
                )
            elif coverage_percent < 80:
                recommendations.append(
                    "Test coverage is below 80%. Consider adding more tests for edge cases."
                )
            else:
                recommendations.append(
                    "Good test coverage! Consider adding more integration tests."
                )

        # Performance recommendations
        if "Performance Tests" in self.test_results:
            perf_result = self.test_results["Performance Tests"]
            if perf_result.failed > 0:
                recommendations.append(
                    "Performance tests failed. Review algorithm complexity and optimization."
                )

        # Error handling recommendations
        if "Error Handling Tests" in self.test_results:
            error_result = self.test_results["Error Handling Tests"]
            if error_result.failed > 0:
                recommendations.append(
                    "Error handling tests failed. Improve defensive programming."
                )

        # Integration recommendations
        if "Integration Tests" in self.test_results:
            integration_result = self.test_results["Integration Tests"]
            if integration_result.failed > 0:
                recommendations.append(
                    "Integration tests failed. Check component interactions."
                )

        return recommendations

    def generate_report(self, coverage_percent: float | None) -> TestReport:
        """Generate comprehensive test report."""
        total_duration = sum(r.duration for r in self.test_results.values())
        overall_passed = sum(r.passed for r in self.test_results.values())
        overall_failed = sum(r.failed for r in self.test_results.values())
        overall_skipped = sum(r.skipped for r in self.test_results.values())
        overall_errors = sum(r.errors for r in self.test_results.values())

        return TestReport(
            timestamp=datetime.now().isoformat(),
            total_duration=total_duration,
            overall_passed=overall_passed,
            overall_failed=overall_failed,
            overall_skipped=overall_skipped,
            overall_errors=overall_errors,
            coverage_percent=coverage_percent,
            results_by_category=self.test_results,
            performance_regressions=self.analyze_performance_regressions(),
            security_issues=self.identify_security_issues(),
            recommendations=self.generate_recommendations(coverage_percent),
        )

    def print_report(self, report: TestReport):
        """Print comprehensive test report."""
        print(f"\n{'=' * 80}")
        print("COMPREHENSIVE TEST REPORT")
        print(f"{'=' * 80}")
        print(f"Timestamp: {report.timestamp}")
        print(f"Total Duration: {report.total_duration:.2f}s")
        print()

        print("OVERALL RESULTS:")
        print(f"  Passed:  {report.overall_passed}")
        print(f"  Failed:  {report.overall_failed}")
        print(f"  Skipped: {report.overall_skipped}")
        print(f"  Errors:  {report.overall_errors}")

        if report.coverage_percent is not None:
            print(f"  Coverage: {report.coverage_percent:.1f}%")
        print()

        print("RESULTS BY CATEGORY:")
        for category, result in report.results_by_category.items():
            status = "✓" if result.failed == 0 and result.errors == 0 else "✗"
            print(
                f"  {status} {category}: {result.passed}P {result.failed}F {result.skipped}S {result.errors}E ({result.duration:.1f}s)"
            )
        print()

        if report.performance_regressions:
            print("PERFORMANCE REGRESSIONS:")
            for regression in report.performance_regressions:
                print(f"  ⚠ {regression}")
            print()

        if report.security_issues:
            print("SECURITY ISSUES:")
            for issue in report.security_issues:
                print(f"  ⚠ {issue}")
            print()

        if report.recommendations:
            print("RECOMMENDATIONS:")
            for rec in report.recommendations:
                print(f"  → {rec}")

        print(f"{'=' * 80}")

    def save_report(self, report: TestReport):
        """Save test report to file."""
        report_file = self.base_dir / "test_report.json"
        with open(report_file, "w") as f:
            json.dump(asdict(report), f, indent=2)
        print(f"Detailed report saved to: {report_file}")

    def run_comprehensive_suite(self, args) -> TestReport:
        """Run the comprehensive test suite."""
        start_time = time.time()

        print("Starting PowerRebuilder Comprehensive Test Suite")
        print(f"Arguments: {vars(args)}")

        # Run test categories based on arguments
        if args.fast or not (args.security or args.performance or args.integration):
            self.test_results["Fast Tests"] = self.run_fast_tests()

        if args.security or args.all:
            self.test_results["Security Tests"] = self.run_security_tests()

        if args.performance or args.all:
            self.test_results["Performance Tests"] = self.run_performance_tests()

        if args.integration or args.all:
            self.test_results["Integration Tests"] = self.run_integration_tests()

        # Always run our new comprehensive test suites
        if not args.fast:
            self.test_results["Tiered Detector Tests"] = (
                self.run_tiered_detector_tests()
            )
            self.test_results["Error Handling Tests"] = self.run_error_handling_tests()

        # Run coverage analysis if requested
        coverage_percent = None
        if args.coverage or args.all:
            coverage_percent = self.run_coverage_analysis()

        # Generate and display report
        report = self.generate_report(coverage_percent)
        self.print_report(report)

        if args.report:
            self.save_report(report)

        total_duration = time.time() - start_time
        print(f"\nTotal execution time: {total_duration:.2f}s")

        return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="PowerRebuilder Comprehensive Test Runner"
    )
    parser.add_argument("--fast", action="store_true", help="Run only fast tests")
    parser.add_argument(
        "--security", action="store_true", help="Run only security tests"
    )
    parser.add_argument(
        "--performance", action="store_true", help="Run only performance tests"
    )
    parser.add_argument(
        "--integration", action="store_true", help="Run only integration tests"
    )
    parser.add_argument(
        "--coverage", action="store_true", help="Generate coverage report"
    )
    parser.add_argument(
        "--report", action="store_true", help="Save detailed test report"
    )
    parser.add_argument("--all", action="store_true", help="Run all test categories")

    args = parser.parse_args()

    # If no specific categories requested, default to fast tests
    if not any([args.security, args.performance, args.integration, args.all]):
        args.fast = True

    runner = ComprehensiveTestRunner()
    report = runner.run_comprehensive_suite(args)

    # Exit with appropriate code
    if report.overall_failed > 0 or report.overall_errors > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
