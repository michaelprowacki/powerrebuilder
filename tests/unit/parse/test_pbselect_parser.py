#!/usr/bin/env python3
"""Test script to validate PBSELECT parser improvements."""

import sys
from pathlib import Path

from lark import Lark
from lark.exceptions import UnexpectedCharacters, UnexpectedToken

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_pbselect_parsing():
    """Test parsing of PBSELECT statements in DataWindow files."""

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

    # Test case 1: Simple PBSELECT with version, table, column
    test_case1 = """// Test DataWindow
PBSELECT(VERSION(400)
    TABLE(NAME="treatment")
    TABLE(NAME="treatment_bill")
    COLUMN(NAME="treatment.person_id")
    COLUMN(NAME="treatment.treatment_id")
    COLUMN(NAME="treatment_bill.bill_id"))
"""

    # Test case 2: PBSELECT with JOIN
    test_case2 = """// Test with JOIN
PBSELECT(VERSION(400)
    TABLE(NAME="treatment")
    TABLE(NAME="treatment_bill")
    COLUMN(NAME="treatment.person_id")
    JOIN(LEFT="treatment_bill.treatment_id" OP="=" RIGHT="treatment.treatment_id"))
"""

    # Test case 3: PBSELECT with WHERE clause
    test_case3 = """// Test with WHERE
PBSELECT(VERSION(400)
    TABLE(NAME="treatment")
    COLUMN(NAME="treatment.person_id")
    WHERE(EXP1="treatment.person_id" OP="=" EXP2=" "))
"""

    # Test case 4: PBSELECT with WHERE and LOGIC
    test_case4 = """// Test with WHERE and LOGIC
PBSELECT(VERSION(400)
    TABLE(NAME="treatment")
    COLUMN(NAME="treatment.person_id")
    WHERE(EXP1="treatment.person_id" OP="=" EXP2=" " LOGIC="and")
    WHERE(EXP1="treatment.treatment_id" OP="=" EXP2=" "))
"""

    test_cases = [
        ("Simple PBSELECT", test_case1),
        ("PBSELECT with JOIN", test_case2),
        ("PBSELECT with WHERE", test_case3),
        ("PBSELECT with WHERE and LOGIC", test_case4),
    ]

    success_count = 0

    for name, test_code in test_cases:
        print(f"\nTesting: {name}")
        print("-" * 40)
        try:
            tree = parser.parse(test_code)
            print("✓ SUCCESS: Parsed successfully")
            success_count += 1
            # print(f"  Tree: {tree.pretty()[:100]}...")  # Show first 100 chars
        except (UnexpectedToken, UnexpectedCharacters) as e:
            print(f"✗ FAILED: {type(e).__name__}")
            print(f"  Error: {str(e)[:200]}...")
        # Test: catch all exceptions to verify error handling
        except Exception as e:
            print(f"✗ FAILED: Unexpected error - {type(e).__name__}")
            print(f"  Error: {str(e)[:200]}...")

    print(f"\n{'=' * 50}")
    print(f"Summary: {success_count}/{len(test_cases)} tests passed")
    print(f"Success rate: {success_count / len(test_cases) * 100:.1f}%")

    # Test on actual failing file
    print(f"\n{'=' * 50}")
    print("Testing on actual failing file...")

    failing_file = (
        Path(__file__).parent.parent
        / "output"
        / "extracted"
        / "pbd_files"
        / "dcm_detailobjects.pbd"
        / "dcm_detailobjects.pbd"
        / "d_get_treatmentbill_ds.dwo.srd"
    )

    if failing_file.exists():
        with open(failing_file) as f:
            content = f.read()

        try:
            tree = parser.parse(content)
            print("✓ SUCCESS: Actual file parsed successfully!")
        except Exception as e:
            print(f"✗ FAILED: {type(e).__name__}")
            print(f"  Error: {str(e)[:300]}...")
    else:
        print("  File not found")

    return success_count == len(test_cases)


if __name__ == "__main__":
    success = test_pbselect_parsing()
    sys.exit(0 if success else 1)
