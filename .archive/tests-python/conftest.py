"""Global pytest configuration and fixtures for PowerRebuilder tests."""

import logging
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator, List

import pytest
from _pytest.config import Config
from _pytest.fixtures import FixtureRequest

# Add src_new to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src_new"
sys.path.insert(0, str(src_path))

# Test data paths
TEST_ROOT = Path(__file__).parent
FIXTURES_DIR = TEST_ROOT / "fixtures"
PBD_FILES_DIR = FIXTURES_DIR / "pbd_files"
PB_CODE_DIR = FIXTURES_DIR / "pb_code"
EXPECTED_OUTPUTS_DIR = FIXTURES_DIR / "expected_outputs"
DATA_DIR = project_root / "data"


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--pb-version",
        action="store",
        default="all",
        help="PowerBuilder version to test: 6, 8, 12, 2022, or all",
    )
    parser.addoption(
        "--profile",
        action="store_true",
        default=False,
        help="Enable CPU profiling with pyinstrument",
    )
    parser.addoption(
        "--benchmark",
        action="store_true",
        default=False,
        help="Run performance benchmarks",
    )
    parser.addoption(
        "--real-files",
        action="store_true",
        default=False,
        help="Run tests with all real PBD/PBL files (slow)",
    )


def pytest_configure(config: Config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "pb6: PowerBuilder 6.0 tests")
    config.addinivalue_line("markers", "pb8: PowerBuilder 8.0 tests")
    config.addinivalue_line("markers", "pb12: PowerBuilder 12.0 tests")
    config.addinivalue_line("markers", "pb2022: PowerBuilder 2022 tests")


# ============================================================================
# LOGGING FIXTURES
# ============================================================================


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration for each test."""
    original_level = logging.root.level
    original_handlers = logging.root.handlers[:]

    yield

    # Restore logging state
    logging.root.handlers.clear()
    logging.root.handlers.extend(original_handlers)
    logging.root.setLevel(original_level)


@pytest.fixture
def test_logger():
    """Provide a test-specific logger."""
    logger = logging.getLogger("test")
    logger.setLevel(logging.DEBUG)

    # Add console handler if not present
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# ============================================================================
# FILE AND DIRECTORY FIXTURES
# ============================================================================


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory that's cleaned up after test."""
    temp_path = Path(tempfile.mkdtemp(prefix="powerrebuilder_test_"))
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def data_dir() -> Path:
    """Path to data directory with real PB files."""
    return DATA_DIR


# ============================================================================
# POWERBUILDER FILE FIXTURES
# ============================================================================


@pytest.fixture
def sample_pbd_file() -> Path:
    """Provide a sample PBD file for testing."""
    pbd_file = DATA_DIR / "pbd_files" / "dcm_billing.pbd"
    if not pbd_file.exists():
        pytest.skip(f"PBD file not found: {pbd_file}")
    return pbd_file


@pytest.fixture
def sample_pbl_file() -> Path:
    """Provide a sample PBL file for testing."""
    # Try to find a PBL file in the data directory
    pbl_files = list(DATA_DIR.glob("**/*.pbl"))
    if not pbl_files:
        pytest.skip("No PBL files found in data directory")
    return pbl_files[0]


@pytest.fixture
def pb6_files() -> List[Path]:
    """Provide PowerBuilder 6.0 test files."""
    pb6_dir = DATA_DIR / "pb_code_examples" / "PowerBuilder 6.0"
    if not pb6_dir.exists():
        pytest.skip("PowerBuilder 6.0 files not found")

    files = []
    files.extend(pb6_dir.glob("**/*.pbl"))
    files.extend(pb6_dir.glob("**/*.pbd"))
    return files[:5]  # Return first 5 files for testing


@pytest.fixture
def pb8_files() -> List[Path]:
    """Provide PowerBuilder 8.0 test files."""
    pb8_dir = DATA_DIR / "pb_code_examples" / "PowerBuilder 8.0"
    if not pb8_dir.exists():
        pytest.skip("PowerBuilder 8.0 files not found")

    files = []
    files.extend(pb8_dir.glob("**/*.pbl"))
    files.extend(pb8_dir.glob("**/*.pbd"))
    return files[:5]


@pytest.fixture
def pb12_files() -> List[Path]:
    """Provide PowerBuilder 12.0 test files."""
    pb12_dir = DATA_DIR / "pb_code_examples" / "PowerBuilder 12.0"
    if not pb12_dir.exists():
        pytest.skip("PowerBuilder 12.0 files not found")

    files = []
    files.extend(pb12_dir.glob("**/*.pbl"))
    files.extend(pb12_dir.glob("**/*.pbd"))
    return files[:5]


@pytest.fixture
def all_pbd_files() -> List[Path]:
    """Provide all PBD files from data directory."""
    pbd_dir = DATA_DIR / "pbd_files"
    if not pbd_dir.exists():
        pytest.skip("PBD files directory not found")

    files = list(pbd_dir.glob("*.pbd"))
    return files


# ============================================================================
# MOCK DATA FIXTURES
# ============================================================================


@pytest.fixture
def sample_pcode_bytes() -> bytes:
    """Sample P-code bytes for testing."""
    return bytes(
        [
            0x01,
            0x00,  # Version
            0x10,
            0x00,  # Function count
            0x20,
            0x00,
            0x00,
            0x00,  # Code offset
            0x30,
            0x00,
            0x00,
            0x00,  # Data offset
            # Sample opcodes
            0x01,  # PUSH
            0x02,  # POP
            0x10,  # LOAD
            0x20,  # STORE
            0x30,  # CALL
            0xFF,  # END
        ]
    )


@pytest.fixture
def sample_ast_dict() -> Dict[str, Any]:
    """Sample AST dictionary for testing."""
    return {
        "node_type": "window",
        "name": "w_test",
        "children": [
            {
                "node_type": "control",
                "name": "cb_save",
                "type": "commandbutton",
                "properties": {
                    "text": "Save",
                    "enabled": True,
                    "visible": True,
                },
            },
            {
                "node_type": "event",
                "name": "clicked",
                "handler": "MessageBox('Info', 'Button clicked')",
            },
        ],
    }


@pytest.fixture
def sample_pb_window_code() -> str:
    """Sample PowerBuilder window code."""
    return """
global type w_customer from window
end type

type cb_save from commandbutton within w_customer
end type

type dw_main from datawindow within w_customer
end type

global type w_customer from window
    integer width = 2000
    integer height = 1500
    string title = "Customer Window"
    cb_save cb_save
    dw_main dw_main
end type

on w_customer.create
    this.cb_save = create cb_save
    this.dw_main = create dw_main
end on

type cb_save from commandbutton within w_customer
    integer x = 100
    integer y = 100
    integer width = 400
    integer height = 100
    string text = "Save"
end type

event clicked;
    MessageBox("Save", "Saving customer data...")
    dw_main.Update()
end event

type dw_main from datawindow within w_customer
    integer x = 100
    integer y = 300
    integer width = 1800
    integer height = 1000
    string dataobject = "d_customer"
end type
"""


# ============================================================================
# PIPELINE FIXTURES
# ============================================================================


@pytest.fixture
def mock_coordinator_config() -> Dict[str, Any]:
    """Mock configuration for coordinators."""
    return {
        "parallel": False,
        "cache_enabled": False,
        "verbose": True,
        "validate": True,
        "max_workers": 1,
        "timeout": 30,
    }


@pytest.fixture
def pipeline_stages() -> List[str]:
    """List of pipeline stages."""
    return ["extract", "decompile", "parse", "model", "generate"]


# ============================================================================
# PERFORMANCE FIXTURES
# ============================================================================


@pytest.fixture
def cpu_profiler(request: FixtureRequest):
    """CPU profiler using pyinstrument."""
    if not request.config.getoption("--profile"):
        yield None
        return

    try:
        from pyinstrument import Profiler
    except ImportError:
        pytest.skip("pyinstrument not installed")

    profiler = Profiler()
    profiler.start()

    yield profiler

    profiler.stop()

    # Save profiling results
    reports_dir = TEST_ROOT / "reports" / "performance"
    reports_dir.mkdir(parents=True, exist_ok=True)

    test_name = request.node.name.replace("[", "_").replace("]", "_")
    html_file = reports_dir / f"profile_{test_name}.html"

    with open(html_file, "w") as f:
        f.write(profiler.output_html())


@pytest.fixture
def benchmark_timer():
    """Simple benchmark timer."""
    import time

    class Timer:
        def __init__(self):
            self.times = []

        def start(self):
            self.start_time = time.perf_counter()

        def stop(self):
            elapsed = time.perf_counter() - self.start_time
            self.times.append(elapsed)
            return elapsed

        def average(self):
            return sum(self.times) / len(self.times) if self.times else 0

        def report(self):
            if not self.times:
                return "No measurements"
            return (
                f"Times: {self.times}\n"
                f"Average: {self.average():.4f}s\n"
                f"Min: {min(self.times):.4f}s\n"
                f"Max: {max(self.times):.4f}s"
            )

    return Timer()


# ============================================================================
# ASSERTION HELPERS
# ============================================================================


@pytest.fixture
def assert_valid_ast():
    """Assertion helper for AST validation."""

    def _assert(ast_node):
        assert ast_node is not None
        assert hasattr(ast_node, "node_type")
        assert hasattr(ast_node, "children")
        assert isinstance(ast_node.children, list)

    return _assert


@pytest.fixture
def assert_valid_pbd():
    """Assertion helper for PBD validation."""

    def _assert(pbd_data):
        assert pbd_data is not None
        assert isinstance(pbd_data, bytes) or hasattr(pbd_data, "signature")
        if isinstance(pbd_data, bytes):
            assert len(pbd_data) > 0

    return _assert


# ============================================================================
# TEST DATA BUILDERS
# ============================================================================


@pytest.fixture
def create_test_pbd_file():
    """Factory for creating test PBD files."""

    def _create(path: Path, size: int = 1024):
        """Create a test PBD file with specified size."""
        # PBD signature
        data = b"PBD\x06"  # PBD version 6
        # Add some padding
        data += b"\x00" * (size - len(data))

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    return _create


@pytest.fixture
def create_test_ast():
    """Factory for creating test AST nodes."""

    def _create(node_type="window", name="test", children=None):
        """Create a test AST node."""
        from _core import ASTNode

        node = ASTNode(
            node_type=node_type, value=name, children=children or [], attributes={}
        )
        return node

    return _create


# ============================================================================
# CLEANUP
# ============================================================================


@pytest.fixture(autouse=True)
def cleanup_test_files(request: FixtureRequest):
    """Clean up test files after each test."""
    yield

    # Clean up any temporary test files
    temp_patterns = [
        "test_*.pbd",
        "test_*.pbl",
        "temp_*.txt",
        "output_*",
    ]

    for pattern in temp_patterns:
        for file in TEST_ROOT.glob(f"**/{pattern}"):
            if file.is_file():
                file.unlink(missing_ok=True)
            elif file.is_dir():
                shutil.rmtree(file, ignore_errors=True)
