"""Report generator for accuracy metrics and test results.

Generates comprehensive HTML and JSON reports for pipeline accuracy testing.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import html

from testing.accuracy_metrics import (
    AccuracyMetrics,
    AccuracyLevel,
    MetricsAggregator,
)
from testing.semantic_validation import ValidationResult, ValidationSeverity


class ReportGenerator:
    """Generates accuracy and validation reports."""

    def __init__(self, output_dir: Path):
        """Initialize report generator.

        Args:
            output_dir: Directory for generated reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_accuracy_report(
        self, metrics: AccuracyMetrics, validation: Optional[ValidationResult] = None
    ) -> Path:
        """Generate HTML accuracy report.

        Args:
            metrics: Accuracy metrics
            validation: Optional validation results

        Returns:
            Path to generated report
        """
        report_path = (
            self.output_dir
            / f"accuracy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        )

        html_content = self._generate_html_report(metrics, validation)
        report_path.write_text(html_content)

        return report_path

    def generate_summary_report(self, aggregator: MetricsAggregator) -> Path:
        """Generate summary report across multiple tests.

        Args:
            aggregator: Metrics aggregator with multiple test results

        Returns:
            Path to generated report
        """
        report_path = (
            self.output_dir
            / f"summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        )

        html_content = self._generate_summary_html(aggregator)
        report_path.write_text(html_content)

        return report_path

    def generate_json_report(self, metrics: AccuracyMetrics) -> Path:
        """Generate JSON report for programmatic access.

        Args:
            metrics: Accuracy metrics

        Returns:
            Path to generated report
        """
        report_path = (
            self.output_dir / f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        json_data = metrics.to_dict()
        report_path.write_text(json.dumps(json_data, indent=2))

        return report_path

    def _generate_html_report(
        self, metrics: AccuracyMetrics, validation: Optional[ValidationResult] = None
    ) -> str:
        """Generate HTML content for accuracy report."""

        # Calculate summary stats
        failed_stages = metrics.get_failed_stages()
        low_accuracy_stages = metrics.get_low_accuracy_stages()

        html_parts = [
            self._get_html_header(),
            self._generate_summary_section(metrics),
            self._generate_stage_details(metrics),
        ]

        if validation:
            html_parts.append(self._generate_validation_section(validation))

        html_parts.extend(
            [self._generate_metrics_charts(metrics), self._get_html_footer()]
        )

        return "\n".join(html_parts)

    def _generate_summary_section(self, metrics: AccuracyMetrics) -> str:
        """Generate summary section HTML."""
        level_color = self._get_level_color(metrics.overall_level)

        return f"""
        <section class="summary">
            <h2>Summary</h2>
            <div class="summary-grid">
                <div class="summary-card">
                    <h3>Overall Accuracy</h3>
                    <div class="accuracy-score" style="color: {level_color}">
                        {metrics.overall_accuracy:.1f}%
                    </div>
                    <div class="accuracy-level">{metrics.overall_level.value.upper()}</div>
                </div>

                <div class="summary-card">
                    <h3>File Info</h3>
                    <div class="file-info">
                        <p><strong>Source:</strong> {html.escape(metrics.source_file)}</p>
                        <p><strong>Type:</strong> {metrics.source_type}</p>
                        <p><strong>Size:</strong> {self._format_size(metrics.source_size)}</p>
                    </div>
                </div>

                <div class="summary-card">
                    <h3>Performance</h3>
                    <div class="performance-info">
                        <p><strong>Total Time:</strong> {metrics.total_execution_time:.3f}s</p>
                        <p><strong>Stages Run:</strong> {len(metrics.stage_results)}</p>
                        <p><strong>Failed Stages:</strong> {len(metrics.get_failed_stages())}</p>
                    </div>
                </div>
            </div>
        </section>
        """

    def _generate_stage_details(self, metrics: AccuracyMetrics) -> str:
        """Generate stage details section HTML."""
        rows = []

        for stage_name, result in metrics.stage_results.items():
            level_color = self._get_level_color(result.accuracy_level)
            status_icon = "✓" if result.success else "✗"
            status_class = "success" if result.success else "failed"

            # Build metrics summary
            metrics_html = []
            for metric in result.metrics[:3]:  # Show top 3 metrics
                metrics_html.append(
                    f"<span class='metric'>{metric.name}: {metric.value:.0f}/{metric.expected or '?'}</span>"
                )

            rows.append(f"""
                <tr class="{status_class}">
                    <td>{stage_name.capitalize()}</td>
                    <td class="status">{status_icon}</td>
                    <td class="accuracy" style="color: {level_color}">{result.accuracy:.1f}%</td>
                    <td>{result.accuracy_level.value}</td>
                    <td>{result.execution_time:.3f}s</td>
                    <td class="metrics">{" • ".join(metrics_html)}</td>
                    <td>{len(result.errors)}/{len(result.warnings)}</td>
                </tr>
            """)

        return f"""
        <section class="stage-details">
            <h2>Stage Details</h2>
            <table>
                <thead>
                    <tr>
                        <th>Stage</th>
                        <th>Status</th>
                        <th>Accuracy</th>
                        <th>Level</th>
                        <th>Time</th>
                        <th>Metrics</th>
                        <th>Errors/Warnings</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(rows)}
                </tbody>
            </table>
        </section>
        """

    def _generate_validation_section(self, validation: ValidationResult) -> str:
        """Generate validation section HTML."""
        # Group issues by severity
        errors = [
            i for i in validation.issues if i.severity == ValidationSeverity.ERROR
        ]
        warnings = [
            i for i in validation.issues if i.severity == ValidationSeverity.WARNING
        ]
        info = [i for i in validation.issues if i.severity == ValidationSeverity.INFO]

        issues_html = []

        if errors:
            issues_html.append("<h3 class='error'>Errors</h3><ul class='error-list'>")
            for issue in errors[:10]:  # Show max 10
                issues_html.append(f"<li>{html.escape(issue.message)}</li>")
            issues_html.append("</ul>")

        if warnings:
            issues_html.append(
                "<h3 class='warning'>Warnings</h3><ul class='warning-list'>"
            )
            for issue in warnings[:10]:  # Show max 10
                issues_html.append(f"<li>{html.escape(issue.message)}</li>")
            issues_html.append("</ul>")

        return f"""
        <section class="validation">
            <h2>Semantic Validation</h2>
            <div class="validation-summary">
                <p><strong>Valid:</strong> {"Yes" if validation.valid else "No"}</p>
                <p><strong>Errors:</strong> {len(errors)}</p>
                <p><strong>Warnings:</strong> {len(warnings)}</p>
                <p><strong>Info:</strong> {len(info)}</p>
            </div>
            <div class="validation-issues">
                {"".join(issues_html)}
            </div>
            <div class="validation-metrics">
                <h3>Metrics</h3>
                {self._format_metrics_table(validation.metrics)}
            </div>
        </section>
        """

    def _generate_metrics_charts(self, metrics: AccuracyMetrics) -> str:
        """Generate metrics visualization section."""
        # Prepare data for chart
        stage_names = list(metrics.stage_results.keys())
        stage_accuracies = [r.accuracy for r in metrics.stage_results.values()]

        return f"""
        <section class="charts">
            <h2>Accuracy Visualization</h2>
            <div class="chart-container">
                <canvas id="accuracyChart"></canvas>
            </div>
            <script>
                const ctx = document.getElementById('accuracyChart').getContext('2d');
                new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: {json.dumps(stage_names)},
                        datasets: [{{
                            label: 'Accuracy (%)',
                            data: {json.dumps(stage_accuracies)},
                            backgroundColor: {json.dumps([self._get_level_color(self._get_level_for_accuracy(acc)) for acc in stage_accuracies])},
                            borderColor: '#333',
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                max: 100
                            }}
                        }}
                    }}
                }});
            </script>
        </section>
        """

    def _generate_summary_html(self, aggregator: MetricsAggregator) -> str:
        """Generate summary HTML for multiple tests."""
        summary = aggregator.generate_summary()

        html_parts = [
            self._get_html_header(),
            f"""
            <section class="multi-test-summary">
                <h1>Pipeline Accuracy Summary</h1>
                <div class="summary-stats">
                    <div class="stat-card">
                        <h3>Total Tests</h3>
                        <div class="stat-value">{summary["total_runs"]}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Average Accuracy</h3>
                        <div class="stat-value">{summary["average_accuracy"]:.1f}%</div>
                    </div>
                    <div class="stat-card">
                        <h3>Best Run</h3>
                        <div class="stat-value">{summary.get("best_run", "N/A")}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Worst Run</h3>
                        <div class="stat-value">{summary.get("worst_run", "N/A")}</div>
                    </div>
                </div>

                <h2>Stage Averages</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Stage</th>
                            <th>Average Accuracy</th>
                            <th>Failure Rate</th>
                        </tr>
                    </thead>
                    <tbody>
            """,
        ]

        for stage, accuracy in summary["stage_averages"].items():
            failure_rate = summary["failure_rates"].get(stage, 0)
            html_parts.append(f"""
                <tr>
                    <td>{stage.capitalize()}</td>
                    <td>{accuracy:.1f}%</td>
                    <td>{failure_rate:.1f}%</td>
                </tr>
            """)

        html_parts.extend(
            [
                """
                    </tbody>
                </table>
            </section>
            """,
                self._get_html_footer(),
            ]
        )

        return "\n".join(html_parts)

    def _get_html_header(self) -> str:
        """Get HTML header with styles."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>PowerRebuilder Accuracy Report</title>
            <meta charset="utf-8">
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: #f5f5f5;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }
                h1 {
                    color: #2c3e50;
                    margin-bottom: 30px;
                    font-size: 2.5em;
                    text-align: center;
                }
                h2 {
                    color: #34495e;
                    margin: 30px 0 20px 0;
                    border-bottom: 2px solid #ecf0f1;
                    padding-bottom: 10px;
                }
                section {
                    background: white;
                    border-radius: 10px;
                    padding: 20px;
                    margin-bottom: 30px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .summary-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-top: 20px;
                }
                .summary-card {
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    border: 1px solid #dee2e6;
                }
                .accuracy-score {
                    font-size: 3em;
                    font-weight: bold;
                    text-align: center;
                    margin: 10px 0;
                }
                .accuracy-level {
                    text-align: center;
                    font-size: 1.2em;
                    text-transform: uppercase;
                    font-weight: 600;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }
                th, td {
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #dee2e6;
                }
                th {
                    background: #f8f9fa;
                    font-weight: 600;
                    color: #495057;
                }
                tr:hover {
                    background: #f8f9fa;
                }
                tr.failed {
                    background: #fff5f5;
                }
                tr.failed:hover {
                    background: #ffe5e5;
                }
                .status {
                    font-weight: bold;
                    text-align: center;
                }
                .success .status { color: #27ae60; }
                .failed .status { color: #e74c3c; }
                .metric {
                    display: inline-block;
                    padding: 2px 8px;
                    background: #ecf0f1;
                    border-radius: 4px;
                    font-size: 0.9em;
                    margin: 2px;
                }
                .chart-container {
                    position: relative;
                    height: 400px;
                    margin-top: 20px;
                }
                .error { color: #e74c3c; }
                .warning { color: #f39c12; }
                .info { color: #3498db; }
                .validation-issues ul {
                    margin-left: 20px;
                    margin-bottom: 20px;
                }
                .stat-card {
                    text-align: center;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 8px;
                }
                .stat-value {
                    font-size: 2em;
                    font-weight: bold;
                    color: #2c3e50;
                    margin-top: 10px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>PowerRebuilder Pipeline Accuracy Report</h1>
                <p style="text-align: center; color: #7f8c8d; margin-bottom: 30px;">
                    Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
        """

    def _get_html_footer(self) -> str:
        """Get HTML footer."""
        return """
            </div>
        </body>
        </html>
        """

    def _get_level_color(self, level: AccuracyLevel) -> str:
        """Get color for accuracy level."""
        colors = {
            AccuracyLevel.PERFECT: "#27ae60",  # Green
            AccuracyLevel.EXCELLENT: "#2ecc71",  # Light green
            AccuracyLevel.GOOD: "#3498db",  # Blue
            AccuracyLevel.FAIR: "#f39c12",  # Orange
            AccuracyLevel.POOR: "#e67e22",  # Dark orange
            AccuracyLevel.FAILED: "#e74c3c",  # Red
        }
        return colors.get(level, "#95a5a6")

    def _get_level_for_accuracy(self, accuracy: float) -> AccuracyLevel:
        """Get accuracy level for a percentage."""
        if accuracy >= 100:
            return AccuracyLevel.PERFECT
        elif accuracy >= 95:
            return AccuracyLevel.EXCELLENT
        elif accuracy >= 85:
            return AccuracyLevel.GOOD
        elif accuracy >= 70:
            return AccuracyLevel.FAIR
        elif accuracy >= 50:
            return AccuracyLevel.POOR
        else:
            return AccuracyLevel.FAILED

    def _format_size(self, size: int) -> str:
        """Format byte size as human readable."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _format_metrics_table(self, metrics: Dict[str, Any]) -> str:
        """Format metrics dictionary as HTML table."""
        rows = []
        for key, value in metrics.items():
            if isinstance(value, float):
                value = f"{value:.2f}"
            rows.append(
                f"<tr><td>{key.replace('_', ' ').title()}</td><td>{value}</td></tr>"
            )

        return f"""
        <table>
            <thead>
                <tr><th>Metric</th><th>Value</th></tr>
            </thead>
            <tbody>
                {"".join(rows)}
            </tbody>
        </table>
        """
