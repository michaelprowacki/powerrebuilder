#!/usr/bin/env python3
"""Test the fixed SQL grammar for reduce/reduce conflicts."""

import sys
from pathlib import Path

from lark import Lark
from lark.exceptions import GrammarError


def test_grammar(grammar_file: str, name: str):
    """Test loading a grammar file."""
    print(f"\nTesting {name}...")

    try:
        with open(grammar_file) as f:
            grammar_content = f.read()

        # Try to create parser with LALR algorithm (what the project uses)
        parser = Lark(grammar_content, parser="lalr", start="start")
        print(f"✓ {name} loaded successfully! No conflicts detected.")
        return True

    except GrammarError as e:
        error_msg = str(e)
        if "Reduce/Reduce collision" in error_msg:
            # Count the conflicts
            conflict_count = error_msg.count("Reduce/Reduce collision")
            print(f"✗ {name} has {conflict_count} reduce/reduce conflicts")
        else:
            print(f"✗ {name} has grammar errors: {error_msg[:200]}...")
        return False
    # Test: catch all exceptions to verify error handling
    except Exception as e:
        print(f"✗ {name} failed to load: {type(e).__name__}: {e}")
        return False


def main():
    """Test both grammars."""
    grammar_dir = Path("parse/grammar")

    # Test original grammar
    original_ok = test_grammar(grammar_dir / "sql.lark", "Original SQL grammar")

    # Test fixed grammar
    fixed_ok = test_grammar(grammar_dir / "sql_fixed.lark", "Fixed SQL grammar")

    print("\n" + "=" * 60)
    if fixed_ok and not original_ok:
        print("✓ SUCCESS: Fixed grammar resolves the conflicts!")
        return 0
    if fixed_ok and original_ok:
        print("⚠ Both grammars work - original may have been fixed already")
        return 0
    print("✗ FAILED: Fixed grammar still has issues")
    return 1


if __name__ == "__main__":
    sys.exit(main())
