"""Incremental Processing - Process only changed files for efficiency.

This module tracks file changes and enables incremental processing
to avoid reprocessing unchanged files.
"""

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class FileState:
    """State of a file for change tracking."""

    path: str
    size: int
    modified_time: float
    checksum: str
    last_processed: Optional[float] = None
    processing_result: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)


@dataclass
class ChangeSet:
    """Set of file changes."""

    added: List[Path] = field(default_factory=list)
    modified: List[Path] = field(default_factory=list)
    deleted: List[Path] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return bool(self.added or self.modified or self.deleted)

    @property
    def total_changes(self) -> int:
        """Get total number of changes."""
        return len(self.added) + len(self.modified) + len(self.deleted)


class IncrementalTracker:
    """Track file changes for incremental processing."""

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        use_checksum: bool = True,
    ):
        """Initialize incremental tracker.

        Args:
            cache_dir: Directory to store tracking data
            use_checksum: Use checksums for change detection
        """
        self.cache_dir = cache_dir or Path(".powerrebuilder_cache")
        self.use_checksum = use_checksum
        self.state_file = self.cache_dir / "file_state.json"
        self.file_states: Dict[str, FileState] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}

        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load existing state
        self._load_state()

    def _load_state(self) -> None:
        """Load existing file state from cache."""
        if self.state_file.exists():
            try:
                with self.state_file.open("r") as f:
                    data = json.load(f)

                # Reconstruct file states
                for path, state_data in data.get("files", {}).items():
                    self.file_states[path] = FileState(**state_data)

                # Reconstruct dependency graph
                for path, deps in data.get("dependencies", {}).items():
                    self.dependency_graph[path] = set(deps)

                logger.info(
                    "Loaded incremental state for %d files",
                    len(self.file_states),
                )
            except Exception as e:
                logger.warning("Failed to load state: %s", e)
                self.file_states = {}
                self.dependency_graph = {}

    def _save_state(self) -> None:
        """Save current file state to cache."""
        try:
            data = {
                "files": {
                    path: {
                        "path": state.path,
                        "size": state.size,
                        "modified_time": state.modified_time,
                        "checksum": state.checksum,
                        "last_processed": state.last_processed,
                        "processing_result": state.processing_result,
                        "dependencies": state.dependencies,
                    }
                    for path, state in self.file_states.items()
                },
                "dependencies": {
                    path: list(deps) for path, deps in self.dependency_graph.items()
                },
                "timestamp": time.time(),
            }

            with self.state_file.open("w") as f:
                json.dump(data, f, indent=2)

            logger.debug("Saved incremental state")
        except Exception as e:
            logger.error("Failed to save state: %s", e)

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate file checksum.

        Args:
            file_path: Path to file

        Returns:
            File checksum
        """
        if not self.use_checksum:
            return ""

        hasher = hashlib.md5()
        try:
            with file_path.open("rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.warning("Failed to calculate checksum for %s: %s", file_path, e)
            return ""

    def _get_file_state(self, file_path: Path) -> FileState:
        """Get current state of a file.

        Args:
            file_path: File path

        Returns:
            File state
        """
        stat = file_path.stat()
        return FileState(
            path=str(file_path),
            size=stat.st_size,
            modified_time=stat.st_mtime,
            checksum=self._calculate_checksum(file_path),
        )

    def track_file(self, file_path: Path) -> bool:
        """Track a file and check if it has changed.

        Args:
            file_path: File to track

        Returns:
            True if file has changed
        """
        if not file_path.exists():
            return False

        current_state = self._get_file_state(file_path)
        path_str = str(file_path)

        # Check if file is new
        if path_str not in self.file_states:
            self.file_states[path_str] = current_state
            return True

        # Check if file has changed
        old_state = self.file_states[path_str]
        has_changed = False

        # Check size and modification time first (fast)
        if old_state.size != current_state.size:
            has_changed = True
        elif old_state.modified_time != current_state.modified_time:
            # If mod time changed but size didn't, check checksum
            if self.use_checksum:
                has_changed = old_state.checksum != current_state.checksum
            else:
                has_changed = True

        if has_changed:
            self.file_states[path_str] = current_state

        return has_changed

    def get_changes(
        self,
        input_dir: Path,
        patterns: Optional[List[str]] = None,
    ) -> ChangeSet:
        """Get all file changes in a directory.

        Args:
            input_dir: Directory to scan
            patterns: File patterns to include

        Returns:
            Set of changes
        """
        changes = ChangeSet()
        current_files = set()

        # Default patterns
        if patterns is None:
            patterns = ["*.pbl", "*.pbd", "*.sru", "*.srw", "*.fun"]

        # Scan directory for files
        for pattern in patterns:
            for file_path in input_dir.rglob(pattern):
                if file_path.is_file():
                    current_files.add(str(file_path))

                    if self.track_file(file_path):
                        path_str = str(file_path)
                        if (
                            path_str in self.file_states
                            and self.file_states[path_str].last_processed
                        ):
                            changes.modified.append(file_path)
                        else:
                            changes.added.append(file_path)

        # Check for deleted files
        tracked_files = set(self.file_states.keys())
        deleted_files = tracked_files - current_files

        for path_str in deleted_files:
            changes.deleted.append(Path(path_str))
            del self.file_states[path_str]

        # Save updated state
        self._save_state()

        logger.info(
            "Detected changes: %d added, %d modified, %d deleted",
            len(changes.added),
            len(changes.modified),
            len(changes.deleted),
        )

        return changes

    def mark_processed(
        self,
        file_path: Path,
        result: Optional[str] = "success",
    ) -> None:
        """Mark a file as processed.

        Args:
            file_path: File that was processed
            result: Processing result
        """
        path_str = str(file_path)
        if path_str in self.file_states:
            self.file_states[path_str].last_processed = time.time()
            self.file_states[path_str].processing_result = result
            self._save_state()

    def add_dependency(self, file_path: Path, dependency: Path) -> None:
        """Add a dependency between files.

        Args:
            file_path: File that depends on another
            dependency: File that is depended upon
        """
        path_str = str(file_path)
        dep_str = str(dependency)

        if path_str not in self.dependency_graph:
            self.dependency_graph[path_str] = set()
        self.dependency_graph[path_str].add(dep_str)

        # Update file state
        if path_str in self.file_states:
            if dep_str not in self.file_states[path_str].dependencies:
                self.file_states[path_str].dependencies.append(dep_str)

    def get_affected_files(self, changed_file: Path) -> List[Path]:
        """Get files affected by a change.

        Args:
            changed_file: File that changed

        Returns:
            List of affected files
        """
        affected = set()
        to_check = [str(changed_file)]
        checked = set()

        while to_check:
            current = to_check.pop()
            if current in checked:
                continue
            checked.add(current)

            # Find files that depend on current
            for file_path, dependencies in self.dependency_graph.items():
                if current in dependencies:
                    affected.add(file_path)
                    to_check.append(file_path)

        return [Path(p) for p in affected]

    def should_process(
        self,
        file_path: Path,
        force: bool = False,
    ) -> bool:
        """Check if a file should be processed.

        Args:
            file_path: File to check
            force: Force processing

        Returns:
            True if file should be processed
        """
        if force:
            return True

        # New or changed files should be processed
        if self.track_file(file_path):
            return True

        # Check if any dependencies have changed
        path_str = str(file_path)
        if path_str in self.file_states:
            for dep in self.file_states[path_str].dependencies:
                if dep in self.file_states:
                    dep_path = Path(dep)
                    if dep_path.exists() and self.track_file(dep_path):
                        return True

        return False

    def clear_cache(self) -> None:
        """Clear all cached state."""
        self.file_states = {}
        self.dependency_graph = {}
        if self.state_file.exists():
            self.state_file.unlink()
        logger.info("Cleared incremental processing cache")

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about tracked files.

        Returns:
            Statistics dictionary
        """
        total_files = len(self.file_states)
        processed_files = sum(
            1 for state in self.file_states.values() if state.last_processed is not None
        )
        failed_files = sum(
            1
            for state in self.file_states.values()
            if state.processing_result == "failed"
        )

        total_size = sum(state.size for state in self.file_states.values())
        avg_size = total_size / total_files if total_files > 0 else 0

        return {
            "total_files": total_files,
            "processed_files": processed_files,
            "failed_files": failed_files,
            "success_rate": (processed_files - failed_files) / processed_files
            if processed_files > 0
            else 0,
            "total_size_bytes": total_size,
            "average_file_size": avg_size,
            "total_dependencies": sum(
                len(deps) for deps in self.dependency_graph.values()
            ),
        }


class IncrementalProcessor:
    """Process files incrementally based on changes."""

    def __init__(
        self,
        tracker: IncrementalTracker,
        process_func: callable,
    ):
        """Initialize incremental processor.

        Args:
            tracker: Incremental tracker
            process_func: Function to process files
        """
        self.tracker = tracker
        self.process_func = process_func

    def process_changes(
        self,
        input_dir: Path,
        output_dir: Path,
        patterns: Optional[List[str]] = None,
        process_dependencies: bool = True,
    ) -> Dict[str, Any]:
        """Process only changed files.

        Args:
            input_dir: Input directory
            output_dir: Output directory
            patterns: File patterns to process
            process_dependencies: Also process dependent files

        Returns:
            Processing results
        """
        # Get changes
        changes = self.tracker.get_changes(input_dir, patterns)

        if not changes.has_changes:
            logger.info("No changes detected, skipping processing")
            return {
                "processed": 0,
                "skipped": len(self.tracker.file_states),
                "failed": 0,
            }

        # Determine files to process
        files_to_process = set(changes.added + changes.modified)

        # Add affected files if processing dependencies
        if process_dependencies:
            for file_path in list(files_to_process):
                affected = self.tracker.get_affected_files(file_path)
                files_to_process.update(affected)

        # Process files
        processed = 0
        failed = 0
        skipped = 0

        for file_path in files_to_process:
            if not file_path.exists():
                continue

            try:
                # Process file
                self.process_func(file_path, output_dir)
                self.tracker.mark_processed(file_path, "success")
                processed += 1
                logger.debug("Processed: %s", file_path)
            except Exception as e:
                self.tracker.mark_processed(file_path, "failed")
                failed += 1
                logger.error("Failed to process %s: %s", file_path, e)

        # Count skipped files
        all_files = set()
        for pattern in patterns or ["*"]:
            for file_path in input_dir.rglob(pattern):
                if file_path.is_file():
                    all_files.add(file_path)

        skipped = len(all_files) - len(files_to_process)

        logger.info(
            "Incremental processing complete: %d processed, %d skipped, %d failed",
            processed,
            skipped,
            failed,
        )

        return {
            "processed": processed,
            "skipped": skipped,
            "failed": failed,
            "changes": {
                "added": len(changes.added),
                "modified": len(changes.modified),
                "deleted": len(changes.deleted),
            },
        }
