"""Rich Progress Integration - Beautiful terminal output with progress tracking.

This module integrates the Rich library to provide enhanced terminal output
with progress bars, tables, and colored logging.
"""

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional

try:
    from rich.console import Console
    from rich.live import Live
    from rich.logging import RichHandler
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        SpinnerColumn,
        TextColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
    )
    from rich.table import Table
    from rich.tree import Tree

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None
    Progress = None
    Table = None
    Tree = None

logger = logging.getLogger(__name__)


@dataclass
class ProgressMetrics:
    """Progress tracking metrics."""

    total_items: int
    processed: int
    failed: int
    skipped: int
    elapsed_time: float
    estimated_remaining: float

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.processed == 0:
            return 0.0
        return (self.processed - self.failed) / self.processed * 100

    @property
    def items_per_second(self) -> float:
        """Calculate processing speed."""
        if self.elapsed_time == 0:
            return 0.0
        return self.processed / self.elapsed_time


class RichProgress:
    """Rich progress bar manager."""

    def __init__(self, use_rich: bool = True):
        """Initialize Rich progress.

        Args:
            use_rich: Whether to use Rich output
        """
        self.use_rich = use_rich and RICH_AVAILABLE

        if self.use_rich:
            self.console = Console()
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                console=self.console,
                refresh_per_second=10,
            )
        else:
            self.console = None
            self.progress = None

        self.tasks: Dict[str, Any] = {}  # TaskID type
        self.start_times: Dict[str, float] = {}

    def start(self) -> "RichProgress":
        """Start progress display.

        Returns:
            Self for chaining
        """
        if self.use_rich:
            self.progress.start()
        return self

    def stop(self) -> None:
        """Stop progress display."""
        if self.use_rich:
            self.progress.stop()

    def add_task(
        self,
        name: str,
        description: str,
        total: int,
    ) -> Optional[Any]:
        """Add a new progress task.

        Args:
            name: Task name (for reference)
            description: Task description
            total: Total items to process

        Returns:
            Task ID or None
        """
        if self.use_rich:
            task_id = self.progress.add_task(description, total=total)
            self.tasks[name] = task_id
            self.start_times[name] = time.time()
            return task_id
        else:
            print(f"Starting: {description} (0/{total})")
            self.start_times[name] = time.time()
            return None

    def update(
        self,
        name: str,
        advance: int = 1,
        description: Optional[str] = None,
    ) -> None:
        """Update progress for a task.

        Args:
            name: Task name
            advance: Items completed
            description: New description
        """
        if self.use_rich and name in self.tasks:
            kwargs = {"advance": advance}
            if description:
                kwargs["description"] = description
            self.progress.update(self.tasks[name], **kwargs)
        elif not self.use_rich:
            if description:
                print(f"Progress: {description}")

    def complete(self, name: str) -> None:
        """Mark task as complete.

        Args:
            name: Task name
        """
        if self.use_rich and name in self.tasks:
            self.progress.update(self.tasks[name], completed=True)
        else:
            elapsed = time.time() - self.start_times.get(name, 0)
            print(f"Completed: {name} in {elapsed:.2f}s")

    @contextmanager
    def track(
        self,
        items: List[Any],
        description: str = "Processing",
    ) -> Iterator[Any]:
        """Track progress for items.

        Args:
            items: Items to process
            description: Task description

        Yields:
            Items to process
        """
        task_name = f"task_{time.time()}"
        self.add_task(task_name, description, len(items))

        try:
            for item in items:
                yield item
                self.update(task_name)
        finally:
            self.complete(task_name)

    def print(self, message: str, style: Optional[str] = None) -> None:
        """Print message with optional style.

        Args:
            message: Message to print
            style: Rich style string
        """
        if self.use_rich:
            if style:
                self.console.print(message, style=style)
            else:
                self.console.print(message)
        else:
            print(message)

    def print_table(self, data: List[Dict], title: Optional[str] = None) -> None:
        """Print data as table.

        Args:
            data: List of dictionaries
            title: Table title
        """
        if not data:
            return

        if self.use_rich:
            table = Table(title=title or "Results")

            # Add columns
            for key in data[0].keys():
                table.add_column(str(key).title(), style="cyan")

            # Add rows
            for row in data:
                table.add_row(*[str(v) for v in row.values()])

            self.console.print(table)
        else:
            # Simple table output
            if title:
                print(f"\n{title}")
                print("=" * 50)

            # Headers
            headers = list(data[0].keys())
            print(" | ".join(str(h).title() for h in headers))
            print("-" * 50)

            # Rows
            for row in data:
                print(" | ".join(str(v) for v in row.values()))

    def print_tree(self, root: str, items: Dict[str, Any]) -> None:
        """Print hierarchical data as tree.

        Args:
            root: Root node label
            items: Nested dictionary
        """
        if self.use_rich:
            tree = Tree(root)
            self._build_tree(tree, items)
            self.console.print(tree)
        else:
            # Simple tree output
            print(root)
            self._print_simple_tree(items, prefix="  ")

    def _build_tree(self, tree: "Tree", items: Dict[str, Any]) -> None:
        """Build Rich tree recursively.

        Args:
            tree: Tree node
            items: Items to add
        """
        for key, value in items.items():
            if isinstance(value, dict):
                branch = tree.add(str(key))
                self._build_tree(branch, value)
            else:
                tree.add(f"{key}: {value}")

    def _print_simple_tree(
        self,
        items: Dict[str, Any],
        prefix: str = "",
    ) -> None:
        """Print simple tree structure.

        Args:
            items: Items to print
            prefix: Line prefix
        """
        for key, value in items.items():
            if isinstance(value, dict):
                print(f"{prefix}├── {key}")
                self._print_simple_tree(value, prefix + "│   ")
            else:
                print(f"{prefix}├── {key}: {value}")

    def print_panel(
        self,
        content: str,
        title: Optional[str] = None,
        style: Optional[str] = None,
    ) -> None:
        """Print content in a panel.

        Args:
            content: Panel content
            title: Panel title
            style: Panel style
        """
        if self.use_rich:
            panel = Panel(content, title=title, style=style)
            self.console.print(panel)
        else:
            # Simple panel output
            if title:
                print(f"\n╔══ {title} " + "═" * (50 - len(title) - 5) + "╗")
            else:
                print("\n╔" + "═" * 50 + "╗")

            for line in content.split("\n"):
                print(f"║ {line:<48} ║")

            print("╚" + "═" * 50 + "╝")

    def __enter__(self) -> "RichProgress":
        """Context manager entry."""
        return self.start()

    def __exit__(self, *args) -> None:
        """Context manager exit."""
        self.stop()


class RichLogger:
    """Rich logging configuration."""

    @staticmethod
    def setup(
        level: str = "INFO",
        show_time: bool = True,
        show_path: bool = False,
    ) -> None:
        """Setup Rich logging.

        Args:
            level: Logging level
            show_time: Show timestamps
            show_path: Show file paths
        """
        if not RICH_AVAILABLE:
            # Fallback to standard logging
            logging.basicConfig(
                level=level,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
            return

        # Configure Rich handler
        handler = RichHandler(
            rich_tracebacks=True,
            show_time=show_time,
            show_path=show_path,
        )

        logging.basicConfig(
            level=level,
            format="%(message)s",
            handlers=[handler],
        )


class ProgressTracker:
    """High-level progress tracking."""

    def __init__(self, total_stages: int = 5):
        """Initialize tracker.

        Args:
            total_stages: Total pipeline stages
        """
        self.total_stages = total_stages
        self.current_stage = 0
        self.stage_progress = RichProgress()
        self.metrics: Dict[str, ProgressMetrics] = {}

    def start_stage(self, name: str, total_items: int) -> None:
        """Start a new stage.

        Args:
            name: Stage name
            total_items: Items to process
        """
        self.current_stage += 1

        self.stage_progress.print_panel(
            f"Stage {self.current_stage}/{self.total_stages}: {name}\n"
            f"Items to process: {total_items}",
            title="Pipeline Progress",
            style="blue",
        )

        self.metrics[name] = ProgressMetrics(
            total_items=total_items,
            processed=0,
            failed=0,
            skipped=0,
            elapsed_time=0,
            estimated_remaining=0,
        )

    def update_stage(
        self,
        name: str,
        processed: int = 0,
        failed: int = 0,
        skipped: int = 0,
    ) -> None:
        """Update stage progress.

        Args:
            name: Stage name
            processed: Items processed
            failed: Items failed
            skipped: Items skipped
        """
        if name in self.metrics:
            self.metrics[name].processed += processed
            self.metrics[name].failed += failed
            self.metrics[name].skipped += skipped

    def complete_stage(self, name: str) -> None:
        """Complete a stage.

        Args:
            name: Stage name
        """
        if name in self.metrics:
            metrics = self.metrics[name]

            # Show completion summary
            summary_data = [
                {
                    "Metric": "Total Items",
                    "Value": metrics.total_items,
                },
                {
                    "Metric": "Processed",
                    "Value": metrics.processed,
                },
                {
                    "Metric": "Failed",
                    "Value": metrics.failed,
                },
                {
                    "Metric": "Success Rate",
                    "Value": f"{metrics.success_rate:.1f}%",
                },
            ]

            self.stage_progress.print_table(
                summary_data,
                title=f"{name} Stage Complete",
            )

    def show_final_summary(self) -> None:
        """Show final pipeline summary."""
        total_processed = sum(m.processed for m in self.metrics.values())
        total_failed = sum(m.failed for m in self.metrics.values())

        self.stage_progress.print_panel(
            f"Pipeline Complete!\n\n"
            f"Total Stages: {self.current_stage}/{self.total_stages}\n"
            f"Total Items Processed: {total_processed}\n"
            f"Total Failures: {total_failed}\n"
            f"Overall Success Rate: {((total_processed - total_failed) / total_processed * 100) if total_processed > 0 else 0:.1f}%",
            title="Pipeline Summary",
            style="green" if total_failed == 0 else "yellow",
        )


# Singleton instances
_progress = None
_tracker = None


def get_progress() -> RichProgress:
    """Get global progress instance.

    Returns:
        Progress instance
    """
    global _progress
    if _progress is None:
        _progress = RichProgress()
    return _progress


def get_tracker() -> ProgressTracker:
    """Get global tracker instance.

    Returns:
        Tracker instance
    """
    global _tracker
    if _tracker is None:
        _tracker = ProgressTracker()
    return _tracker
