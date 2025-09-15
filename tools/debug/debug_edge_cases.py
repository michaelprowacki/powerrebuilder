#!/usr/bin/env python3
"""Debug why edge cases aren't being fixed."""

import sys

sys.path.insert(0, ".")

from src.extract.utils.encoding import (
    _apply_pattern_specific_fixes,
    decode_powerbuilder_text,
)

test_cases = [
    'COLUMN(NAME="address.addess_id")',
    'COLUMN(NAME=" ddress.create_datetime")',
]

print("Debugging Edge Cases")
print("=" * 50)

for test in test_cases:
    print(f"\nTesting: {test}")
    print("-" * 40)

    # Try pattern-specific fixes directly
    fixed = _apply_pattern_specific_fixes(test)
    print(f"After pattern fixes: {fixed}")

    # Try full decode
    data = test.encode("latin1")
    result = decode_powerbuilder_text(data)
    print(f"After full decode: {result}")

    # Check if the patterns would match
    import re

    # Test specific patterns
    patterns_to_test = [
        (r"addess", 'Should match "addess"'),
        (r"(address\.)addess(_id)", 'Should match "address.addess_id"'),
        (r'(["\']\s*)ddress\.', 'Should match " ddress."'),
    ]

    for pattern, desc in patterns_to_test:
        if re.search(pattern, test, re.IGNORECASE):
            print(f"  ✓ Pattern matches: {desc}")
        else:
            print(f"  ✗ Pattern doesn't match: {desc}")
