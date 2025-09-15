#!/usr/bin/env python3
"""Consolidated test script for advanced decompilation.

This script combines the functionality from:
- test_advanced_decompile.py (verbose logging, single file)
- test_advanced_decompile_concise.py (concise logging, single file)
- test_advanced_decompile_simple.py (directory decompilation)

Usage:
    # Test single file with verbose logging
    python test_advanced_decompile_consolidated.py path/to/file.fun --verbose

    # Test single file with concise logging
    python test_advanced_decompile_consolidated.py path/to/file.fun

    # Test directory
    python test_advanced_decompile_consolidated.py path/to/directory --directory

    # Show limited output
    python test_advanced_decompile_consolidated.py path/to/file.fun --limit 50
"""

import argparse
import logging
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.decompile.coordinator import ExtractedFileDecompiler, decompile_directory


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration.

    Args:
        verbose: If True, use DEBUG level; otherwise INFO
    """
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        if verbose
        else "%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Reduce verbosity from some modules when not verbose
    if not verbose:
        logging.getLogger("decompile.analysis.pcode_detector_enhanced").setLevel(
            logging.WARNING
        )
        logging.getLogger("decompile.core.pcode_decoder").setLevel(logging.WARNING)
        logging.getLogger("decompile.extractors").setLevel(logging.WARNING)


def test_single_fun_file(
    fun_file_path: str, output_dir: Path, max_lines: int | None = None
) -> None:
    """Test decompilation of a single .fun file.

    Args:
        fun_file_path: Path to the .fun file to decompile
        output_dir: Directory to write output files
        max_lines: Maximum number of lines to show (None for all)
    """
    # Create decompiler instance
    decompiler = ExtractedFileDecompiler(output_dir)

    # Test the file
    logging.info(f"Testing decompilation of: {fun_file_path}")

    try:
        result = decompiler.decompile_file(fun_file_path)

        if result:
            # Show result
            if max_lines and max_lines > 0:
                lines = result.split("\n")
                if len(lines) > max_lines:
                    # Show first 50 and last 20 lines for concise view
                    first_lines = int(max_lines * 0.7)
                    last_lines = max_lines - first_lines

                    print("\n=== Decompilation Result (truncated) ===")
                    print("\n".join(lines[:first_lines]))
                    print(f"\n... ({len(lines) - max_lines} lines omitted) ...\n")
                    print("\n".join(lines[-last_lines:]))
                else:
                    print("\n=== Decompilation Result ===")
                    print(result)
            else:
                print("\n=== Decompilation Result ===")
                print(result)

            # Save to file
            output_file = output_dir / f"{Path(fun_file_path).stem}_decompiled.pb"
            output_file.write_text(result)
            logging.info(f"Saved decompiled output to: {output_file}")

        else:
            logging.error("Decompilation failed - no result returned")

    except FileNotFoundError:
        logging.error(f"File not found: {fun_file_path}")
    # Test: catch all exceptions to verify error handling
    except Exception as e:
        logging.error(f"Decompilation failed: {e}", exc_info=True)


def test_directory_decompilation(input_dir: str, output_dir: Path) -> None:
    """Test decompilation of a directory.

    Args:
        input_dir: Directory containing files to decompile
        output_dir: Directory to write output files
    """
    logging.info(f"Decompiling directory: {input_dir}")

    # If input directory doesn't exist, try to find an extracted directory
    if not Path(input_dir).exists():
        base_dir = Path("data/output/current/extracted")
        if base_dir.exists():
            for pbd_dir in base_dir.iterdir():
                if pbd_dir.is_dir():
                    inner_dirs = list(pbd_dir.iterdir())
                    if inner_dirs:
                        input_dir = str(inner_dirs[0])
                        logging.info(f"Using extracted directory: {input_dir}")
                        break

    # Run decompilation
    try:
        decompile_directory(input_dir, str(output_dir))
        logging.info(f"Directory decompilation complete. Output in: {output_dir}")
    except Exception as e:
        logging.error(f"Directory decompilation failed: {e}", exc_info=True)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test advanced decompilation of PowerBuilder files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "input_path",
        nargs="?",
        default="data/output/current/extracted/dcm_login.pbd/dcm_login.pbd/w_dcm_login.fun",
        help="Path to .fun file or directory to decompile",
    )

    parser.add_argument(
        "--directory",
        "-d",
        action="store_true",
        help="Treat input as directory and decompile all files",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose (DEBUG level) logging",
    )

    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=None,
        help="Limit output to N lines (shows first 70%% and last 30%%)",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="output/test_advanced_decompile",
        help="Output directory for results",
    )

    args = parser.parse_args()

    # Set up logging
    setup_logging(args.verbose)

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run appropriate test
    if args.directory:
        test_directory_decompilation(args.input_path, output_dir)
    else:
        # For single file, use limit if not verbose
        max_lines = args.limit
        if max_lines is None and not args.verbose:
            max_lines = 100  # Default limit for non-verbose mode

        test_single_fun_file(args.input_path, output_dir, max_lines)


if __name__ == "__main__":
    main()
