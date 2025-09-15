"""Tests for PBD/PBL fixture validation.

This module verifies that the PBD/PBL extraction pipeline can correctly parse
existing test fixtures, ensuring that changes to the extraction code don't
break compatibility with real PowerBuilder files.
"""

import logging
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from src.core.exceptions import PbdError
from src.extract.extract_coordinator import extract_with_recovery
from src.extract.pbd.constants import BLOCK_SIZE
from src.extract.pbd.node import extract_nods
from src.extract.pbd.structures import extract_pbl_header

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for extraction output."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Clean up after test
    shutil.rmtree(temp_dir)


@pytest.fixture
def pbd_fixtures_dir():
    """Get the path to the PBD fixtures directory."""
    # Path is relative to the test file
    fixtures_dir = Path(__file__).parent / "fixtures" / "pbd_files"
    if not fixtures_dir.exists():
        pytest.skip(f"PBD fixtures directory not found: {fixtures_dir}")
    return fixtures_dir


def test_fixture_dir_exists(pbd_fixtures_dir):
    """Verify that PBD fixtures directory exists and contains files."""
    assert pbd_fixtures_dir.exists(), (
        f"PBD fixtures directory not found: {pbd_fixtures_dir}"
    )

    pbd_files = list(pbd_fixtures_dir.glob("*.pbd"))
    assert len(pbd_files) > 0, f"No PBD files found in {pbd_fixtures_dir}"

    logger.info(f"Found {len(pbd_files)} PBD files in {pbd_fixtures_dir}")
    for pbd_file in pbd_files:
        logger.info(f"  - {pbd_file.name} ({pbd_file.stat().st_size / 1024:.1f} KB)")


def test_pbd_header_parsing(pbd_fixtures_dir):
    """Test that PBD headers can be correctly parsed from test fixtures."""
    pbd_files = list(pbd_fixtures_dir.glob("*.pbd"))

    for pbd_file in pbd_files:
        logger.info(f"Testing header parsing for {pbd_file.name}")
        try:
            with open(pbd_file, "rb") as f:
                header = extract_pbl_header(
                    f, BLOCK_SIZE, file_path_for_error_log=str(pbd_file)
                )

            # Verify header attributes
            assert header is not None, f"Failed to parse header for {pbd_file.name}"
            assert hasattr(header, "is_unicode"), (
                f"Header missing is_unicode attribute for {pbd_file.name}"
            )
            assert hasattr(header, "first_nod_offset"), (
                f"Header missing first_nod_offset attribute for {pbd_file.name}"
            )
            assert hasattr(header, "file_size"), (
                f"Header missing file_size attribute for {pbd_file.name}"
            )

            logger.info(
                f"Successfully parsed header for {pbd_file.name}: "
                f"unicode={header.is_unicode}, nod_offset={header.first_nod_offset}, "
                f"file_size={header.file_size}",
            )
        except PbdError as e:
            pytest.fail(f"Failed to parse header for {pbd_file.name}: {e}")
        # Test: catch all exceptions to verify error handling
        except Exception as e:
            pytest.fail(f"Unexpected error parsing header for {pbd_file.name}: {e}")


def test_pbd_node_parsing(pbd_fixtures_dir):
    """Test that PBD nodes can be correctly parsed from test fixtures."""
    pbd_files = list(pbd_fixtures_dir.glob("*.pbd"))

    for pbd_file in pbd_files:
        logger.info(f"Testing node parsing for {pbd_file.name}")
        try:
            with open(pbd_file, "rb") as f:
                header = extract_pbl_header(
                    f, BLOCK_SIZE, file_path_for_error_log=str(pbd_file)
                )

                # Keep file handle open for extract_nods
                nodes = extract_nods(
                    f,
                    header.is_unicode,
                    header.first_nod_offset,
                    BLOCK_SIZE,
                )

            # Verify nodes
            assert nodes is not None, f"Failed to parse nodes for {pbd_file.name}"
            assert len(nodes) > 0, f"No nodes found in {pbd_file.name}"

            # Check node attributes
            for i, node in enumerate(nodes):
                assert node is not None, f"Node {i} is None in {pbd_file.name}"
                assert hasattr(node, "entry_defs"), (
                    f"Node {i} missing entry_defs in {pbd_file.name}"
                )

            total_entries = sum(
                len(node.entry_defs)
                if hasattr(node, "entry_defs") and node.entry_defs
                else 0
                for node in nodes
            )

            logger.info(
                f"Successfully parsed {len(nodes)} nodes with {total_entries} entries "
                f"from {pbd_file.name}",
            )
        except PbdError as e:
            pytest.fail(f"Failed to parse nodes for {pbd_file.name}: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected error parsing nodes for {pbd_file.name}: {e}")


def test_pbd_extraction(pbd_fixtures_dir, temp_output_dir):
    """Test end-to-end PBD extraction for test fixtures."""
    pbd_files = list(pbd_fixtures_dir.glob("*.pbd"))

    for pbd_file in pbd_files:
        logger.info(f"Testing extraction for {pbd_file.name}")
        output_path = os.path.join(temp_output_dir, pbd_file.name)

        try:
            # Create the output directory
            os.makedirs(output_path, exist_ok=True)

            # Extract the PBD
            result = extract_with_recovery(
                str(pbd_file),
                temp_output_dir,
                show_progress=False,
            )

            # Verify extraction
            assert result is True, f"Extraction failed for {pbd_file.name}"

            # Check for extracted files
            extracted_dir = Path(temp_output_dir) / pbd_file.name
            assert extracted_dir.exists(), (
                f"Output directory not created for {pbd_file.name}"
            )

            extracted_files = list(extracted_dir.glob("**/*"))
            assert len(extracted_files) > 0, f"No files extracted from {pbd_file.name}"

            logger.info(
                f"Successfully extracted {len(extracted_files)} files from {pbd_file.name}",
            )
        except Exception as e:
            pytest.fail(f"Extraction failed for {pbd_file.name}: {e}")


if __name__ == "__main__":
    pytest.main(["-v", __file__])
