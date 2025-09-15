#!/usr/bin/env python3
"""Test parser success rate on all extracted DataWindow files."""

import sys
from collections import defaultdict
from pathlib import Path

from lark import Lark
from lark.exceptions import UnexpectedCharacters, UnexpectedToken

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_parser_success_rate():
    """Test parser on all extracted DataWindow files and report success rate."""

    print("Parser Success Rate Test")
    print("=" * 70)

    # Load the datawindow grammar
    grammar_path = (
        Path(__file__).parent.parent / "parse" / "grammar" / "datawindow.lark"
    )
    grammar_dir = grammar_path.parent

    with open(grammar_path) as f:
        grammar_content = f.read()

    # Create parser with import paths
    parser = Lark(
        grammar_content,
        start="datawindow_file",
        parser="lalr",
        import_paths=[str(grammar_dir)],
    )

    # Find all extracted DataWindow files
    extracted_dir = Path(__file__).parent.parent / "output" / "extracted" / "pbd_files"

    if not extracted_dir.exists():
        print("⚠️  No extracted files found. Please run extraction first.")
        return None

    # Collect all .dwo.srd files (DataWindow source files)
    dwo_files = list(extracted_dir.rglob("*.dwo.srd"))

    print(f"\nFound {len(dwo_files)} DataWindow source files")

    if not dwo_files:
        print("⚠️  No DataWindow files found.")
        return None

    # Test parsing each file
    success_count = 0
    failure_count = 0
    error_types = defaultdict(list)
    corruption_patterns = defaultdict(int)

    for i, dwo_file in enumerate(dwo_files):
        try:
            with open(dwo_file, encoding="utf-8", errors="replace") as f:
                content = f.read()

            # Try to parse
            tree = parser.parse(content)
            success_count += 1

            # Check for potential corruptions even in successful parses
            if "*" in content and (
                "*E" in content or '*"' in content or "* " in content
            ):
                corruption_patterns["parsed_with_corruption"] += 1

        except (UnexpectedToken, UnexpectedCharacters) as e:
            failure_count += 1
            error_msg = str(e)

            # Categorize errors
            if "*" in error_msg or "=*" in error_msg:
                error_types["corruption_asterisk"].append(dwo_file.name)
                corruption_patterns["asterisk_corruption"] += 1
            elif '~"' in error_msg:
                error_types["escaped_quotes"].append(dwo_file.name)
            elif "ARG" in error_msg and "Expected" in error_msg:
                error_types["arg_placement"].append(dwo_file.name)
            elif "LOGC" in error_msg:
                error_types["logc_clause"].append(dwo_file.name)
            else:
                error_types["other"].append(dwo_file.name)

        # Test: catch all exceptions to verify error handling
        except Exception:
            failure_count += 1
            error_types["unexpected"].append(dwo_file.name)

    # Report results
    total_files = success_count + failure_count
    success_rate = (success_count / total_files * 100) if total_files > 0 else 0

    print(f"\n{'=' * 70}")
    print("RESULTS SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total files tested: {total_files}")
    print(f"Successfully parsed: {success_count}")
    print(f"Failed to parse: {failure_count}")
    print(f"Success rate: {success_rate:.1f}%")

    if error_types:
        print(f"\n{'=' * 70}")
        print("ERROR BREAKDOWN")
        print(f"{'=' * 70}")
        for error_type, files in sorted(
            error_types.items(), key=lambda x: len(x[1]), reverse=True
        ):
            print(f"\n{error_type}: {len(files)} files")
            # Show first 3 examples
            for f in files[:3]:
                print(f"  - {f}")
            if len(files) > 3:
                print(f"  ... and {len(files) - 3} more")

    if corruption_patterns:
        print(f"\n{'=' * 70}")
        print("CORRUPTION ANALYSIS")
        print(f"{'=' * 70}")
        for pattern, count in corruption_patterns.items():
            print(f"{pattern}: {count} files")

    # Test specific improvements
    print(f"\n{'=' * 70}")
    print("IMPROVEMENT VALIDATION")
    print(f"{'=' * 70}")

    # Count files with specific features
    pbselect_count = 0
    compute_count = 0
    logc_count = 0
    where_count = 0

    for dwo_file in dwo_files[:50]:  # Check first 50 files
        try:
            with open(dwo_file, encoding="utf-8", errors="replace") as f:
                content = f.read()

            if "PBSELECT" in content:
                pbselect_count += 1
            if "COMPUTE" in content:
                compute_count += 1
            if "LOGC" in content:
                logc_count += 1
            if "WHERE" in content:
                where_count += 1
        except:
            pass

    print(f"Files with PBSELECT: {pbselect_count}")
    print(f"Files with COMPUTE: {compute_count}")
    print(f"Files with LOGC: {logc_count}")
    print(f"Files with WHERE: {where_count}")

    return success_rate


if __name__ == "__main__":
    rate = test_parser_success_rate()
    print(f"\nFinal success rate: {rate:.1f}%")
