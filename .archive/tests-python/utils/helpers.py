"""Test helper functions for PowerRebuilder tests."""

import hashlib
import json
import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Union
import time


# ============================================================================
# FILE HELPERS
# ============================================================================


def create_temp_file(
    content: Union[str, bytes], suffix: str = ".txt", dir: Optional[Path] = None
) -> Path:
    """Create a temporary file with content.

    Args:
        content: File content
        suffix: File suffix
        dir: Directory for temp file

    Returns:
        Path to created file
    """
    fd, path = tempfile.mkstemp(suffix=suffix, dir=dir)
    path_obj = Path(path)

    try:
        if isinstance(content, str):
            path_obj.write_text(content)
        else:
            path_obj.write_bytes(content)
        os.close(fd)
    except:
        os.close(fd)
        path_obj.unlink(missing_ok=True)
        raise

    return path_obj


@contextmanager
def temp_directory() -> Generator[Path, None, None]:
    """Context manager for temporary directory.

    Yields:
        Path to temporary directory
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="pb_test_"))
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def copy_test_files(
    source_dir: Path,
    dest_dir: Path,
    pattern: str = "*",
    max_files: Optional[int] = None,
) -> List[Path]:
    """Copy test files matching pattern.

    Args:
        source_dir: Source directory
        dest_dir: Destination directory
        pattern: File pattern
        max_files: Maximum files to copy

    Returns:
        List of copied file paths
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    copied = []

    for i, file in enumerate(source_dir.glob(pattern)):
        if max_files and i >= max_files:
            break

        dest_file = dest_dir / file.name
        shutil.copy2(file, dest_file)
        copied.append(dest_file)

    return copied


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA-256 hash of file.

    Args:
        file_path: Path to file

    Returns:
        Hex digest of hash
    """
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


# ============================================================================
# COMPARISON HELPERS
# ============================================================================


def compare_ast_nodes(
    node1: Dict[str, Any],
    node2: Dict[str, Any],
    ignore_fields: Optional[List[str]] = None,
) -> bool:
    """Compare two AST nodes for equality.

    Args:
        node1: First AST node
        node2: Second AST node
        ignore_fields: Fields to ignore in comparison

    Returns:
        True if nodes are equal
    """
    ignore_fields = ignore_fields or ["line", "column", "position"]

    # Compare node types
    if node1.get("node_type") != node2.get("node_type"):
        return False

    # Compare values
    if node1.get("value") != node2.get("value"):
        return False

    # Compare attributes (excluding ignored fields)
    attrs1 = {
        k: v for k, v in node1.get("attributes", {}).items() if k not in ignore_fields
    }
    attrs2 = {
        k: v for k, v in node2.get("attributes", {}).items() if k not in ignore_fields
    }

    if attrs1 != attrs2:
        return False

    # Compare children recursively
    children1 = node1.get("children", [])
    children2 = node2.get("children", [])

    if len(children1) != len(children2):
        return False

    for c1, c2 in zip(children1, children2):
        if not compare_ast_nodes(c1, c2, ignore_fields):
            return False

    return True


def compare_generated_code(
    actual: str, expected: str, language: str = "python"
) -> Dict[str, Any]:
    """Compare generated code with expected output.

    Args:
        actual: Actual generated code
        expected: Expected code
        language: Programming language

    Returns:
        Comparison result dictionary
    """
    result = {"match": False, "differences": [], "similarity": 0.0}

    # Normalize whitespace
    actual_lines = [line.strip() for line in actual.splitlines() if line.strip()]
    expected_lines = [line.strip() for line in expected.splitlines() if line.strip()]

    # Check exact match
    if actual_lines == expected_lines:
        result["match"] = True
        result["similarity"] = 1.0
        return result

    # Calculate similarity
    matching_lines = sum(1 for a, e in zip(actual_lines, expected_lines) if a == e)
    total_lines = max(len(actual_lines), len(expected_lines))
    result["similarity"] = matching_lines / total_lines if total_lines > 0 else 0

    # Find differences
    for i, (a, e) in enumerate(zip(actual_lines, expected_lines)):
        if a != e:
            result["differences"].append({"line": i + 1, "actual": a, "expected": e})

    return result


# ============================================================================
# VALIDATION HELPERS
# ============================================================================


def validate_pbd_file(file_path: Path) -> Dict[str, Any]:
    """Validate a PBD file structure.

    Args:
        file_path: Path to PBD file

    Returns:
        Validation result
    """
    result = {"valid": False, "errors": [], "warnings": [], "info": {}}

    if not file_path.exists():
        result["errors"].append(f"File not found: {file_path}")
        return result

    # Check file size
    size = file_path.stat().st_size
    result["info"]["size"] = size

    if size == 0:
        result["errors"].append("File is empty")
        return result

    if size > 100 * 1024 * 1024:  # 100MB
        result["warnings"].append("File is very large (>100MB)")

    # Check signature
    try:
        with open(file_path, "rb") as f:
            signature = f.read(4)
            if signature[:3] == b"PBD":
                result["valid"] = True
                result["info"]["signature"] = "PBD"
                result["info"]["version"] = signature[3] if len(signature) > 3 else None
            elif signature[:3] == b"PBL":
                result["valid"] = True
                result["info"]["signature"] = "PBL"
            else:
                result["errors"].append(f"Invalid signature: {signature}")
    except Exception as e:
        result["errors"].append(f"Error reading file: {e}")

    return result


def validate_ast_structure(ast: Dict[str, Any]) -> Dict[str, Any]:
    """Validate AST structure.

    Args:
        ast: AST dictionary

    Returns:
        Validation result
    """
    result = {"valid": True, "errors": [], "warnings": [], "stats": {}}

    def validate_node(node: Dict[str, Any], path: str = ""):
        """Recursively validate AST node."""
        # Check required fields
        if "node_type" not in node:
            result["errors"].append(f"Missing node_type at {path}")
            result["valid"] = False

        # Count node types
        node_type = node.get("node_type", "unknown")
        result["stats"][node_type] = result["stats"].get(node_type, 0) + 1

        # Validate children
        if "children" in node:
            if not isinstance(node["children"], list):
                result["errors"].append(f"Children must be a list at {path}")
                result["valid"] = False
            else:
                for i, child in enumerate(node["children"]):
                    child_path = f"{path}/{node_type}[{i}]"
                    validate_node(child, child_path)

    validate_node(ast)

    # Add summary stats
    result["stats"]["total_nodes"] = sum(result["stats"].values())
    result["stats"]["depth"] = calculate_ast_depth(ast)

    return result


def calculate_ast_depth(ast: Dict[str, Any]) -> int:
    """Calculate maximum depth of AST.

    Args:
        ast: AST dictionary

    Returns:
        Maximum depth
    """

    def get_depth(node: Dict[str, Any]) -> int:
        if not node.get("children"):
            return 1
        return 1 + max(get_depth(child) for child in node["children"])

    return get_depth(ast)


# ============================================================================
# PERFORMANCE HELPERS
# ============================================================================


class Timer:
    """Simple timer for performance measurements."""

    def __init__(self):
        self.times = {}
        self.start_times = {}

    def start(self, name: str = "default"):
        """Start timing an operation."""
        self.start_times[name] = time.perf_counter()

    def stop(self, name: str = "default") -> float:
        """Stop timing and return elapsed time."""
        if name not in self.start_times:
            return 0.0

        elapsed = time.perf_counter() - self.start_times[name]

        if name not in self.times:
            self.times[name] = []
        self.times[name].append(elapsed)

        del self.start_times[name]
        return elapsed

    @contextmanager
    def measure(self, name: str = "default"):
        """Context manager for timing."""
        self.start(name)
        yield
        self.stop(name)

    def get_stats(self, name: str = "default") -> Dict[str, float]:
        """Get timing statistics."""
        if name not in self.times or not self.times[name]:
            return {"count": 0}

        times = self.times[name]
        return {
            "count": len(times),
            "total": sum(times),
            "average": sum(times) / len(times),
            "min": min(times),
            "max": max(times),
        }


def measure_memory_usage() -> Dict[str, float]:
    """Measure current memory usage.

    Returns:
        Memory usage statistics in MB
    """
    import psutil

    process = psutil.Process()
    mem_info = process.memory_info()

    return {
        "rss_mb": mem_info.rss / 1024 / 1024,
        "vms_mb": mem_info.vms / 1024 / 1024,
        "percent": process.memory_percent(),
    }


# ============================================================================
# ASSERTION HELPERS
# ============================================================================


def assert_files_equal(file1: Path, file2: Path, encoding: str = "utf-8"):
    """Assert two files are equal.

    Args:
        file1: First file
        file2: Second file
        encoding: Text encoding

    Raises:
        AssertionError: If files are not equal
    """
    if file1.suffix in [".pbd", ".pbl", ".exe", ".dll"]:
        # Binary comparison
        content1 = file1.read_bytes()
        content2 = file2.read_bytes()
        assert content1 == content2, f"Binary files differ: {file1} vs {file2}"
    else:
        # Text comparison
        content1 = file1.read_text(encoding=encoding)
        content2 = file2.read_text(encoding=encoding)
        assert content1 == content2, f"Text files differ: {file1} vs {file2}"


def assert_json_equal(
    actual: Union[str, Dict],
    expected: Union[str, Dict],
    ignore_keys: Optional[List[str]] = None,
):
    """Assert two JSON objects are equal.

    Args:
        actual: Actual JSON (string or dict)
        expected: Expected JSON (string or dict)
        ignore_keys: Keys to ignore in comparison

    Raises:
        AssertionError: If JSON objects are not equal
    """
    if isinstance(actual, str):
        actual = json.loads(actual)
    if isinstance(expected, str):
        expected = json.loads(expected)

    def remove_keys(obj, keys):
        """Recursively remove keys from object."""
        if isinstance(obj, dict):
            return {
                k: remove_keys(v, keys) for k, v in obj.items() if k not in (keys or [])
            }
        elif isinstance(obj, list):
            return [remove_keys(item, keys) for item in obj]
        return obj

    if ignore_keys:
        actual = remove_keys(actual, ignore_keys)
        expected = remove_keys(expected, ignore_keys)

    assert actual == expected, (
        f"JSON objects differ:\nActual: {actual}\nExpected: {expected}"
    )


def assert_accuracy(actual: float, minimum: float, name: str = "accuracy"):
    """Assert accuracy meets minimum threshold.

    Args:
        actual: Actual accuracy
        minimum: Minimum required accuracy
        name: Metric name

    Raises:
        AssertionError: If accuracy is below minimum
    """
    assert actual >= minimum, f"{name} {actual:.2%} is below minimum {minimum:.2%}"


# ============================================================================
# MOCK HELPERS
# ============================================================================


class MockCoordinator:
    """Mock coordinator for testing."""

    def __init__(self, stage: str, success: bool = True):
        self.stage = stage
        self.success = success
        self.process_called = False
        self.input_path = None
        self.output_path = None

    def process(self):
        """Mock process method."""
        self.process_called = True

        from _patterns import CoordinatorResult

        return CoordinatorResult(
            success=self.success,
            stage=self.stage,
            input_path=str(self.input_path) if self.input_path else "",
            output_path=str(self.output_path) if self.output_path else "",
            files_processed=10 if self.success else 0,
            files_failed=0 if self.success else 5,
            errors=[] if self.success else ["Mock error"],
            duration=1.5,
        )


def create_mock_ast() -> Dict[str, Any]:
    """Create a mock AST for testing."""
    return {
        "node_type": "window",
        "value": "w_test",
        "attributes": {"width": 2000, "height": 1500},
        "children": [
            {
                "node_type": "control",
                "value": "cb_save",
                "attributes": {"type": "commandbutton"},
                "children": [],
            },
            {
                "node_type": "event",
                "value": "clicked",
                "attributes": {},
                "children": [],
            },
        ],
    }


def create_mock_model() -> Dict[str, Any]:
    """Create a mock model for testing."""
    return {
        "name": "TestWindow",
        "object_type": "window",
        "parent_class": "Window",
        "methods": [
            {
                "name": "save",
                "return_type": "void",
                "parameters": [],
                "implementation": "// Save implementation",
            }
        ],
        "properties": [
            {"name": "title", "type": "string", "initial_value": "Test Window"}
        ],
        "events": [{"name": "open", "parameters": [], "handler": "// Open event"}],
    }
