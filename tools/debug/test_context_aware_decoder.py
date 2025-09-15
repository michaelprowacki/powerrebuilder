#!/usr/bin/env python3
"""Test the context-aware PowerBuilder decoder."""

import sys

sys.path.insert(0, ".")

from src.extract.utils.encoding import decode_powerbuilder_text

# Test cases showing the power of context-aware matching
test_cases = [
    # Should match 'address' (add*ess -> address)
    ("add*ess", "address"),
    # Should match 'treatment' (trea*ment -> treatment)
    ("trea*ment", "treatment"),
    # Should match 'COLUMN' (COL*MN -> COLUMN)
    ("COL*MN", "COLUMN"),
    # Should match 'operator' (oper*tor -> operator)
    ("oper*tor", "operator"),
    # Should match 'billing' (bill*ng -> billing)
    ("bill*ng", "billing"),
    # Should match 'update' (upd*te -> update)
    ("upd*te", "update"),
    # Should match 'person_id' (person*id -> person_id)
    ("person*id", "person_id"),
    # Should match 'create_datetime' (create_date*ime -> create_datetime)
    ("create_date*ime", "create_datetime"),
    # Should match 'address_id' (address*id -> address_id)
    ("address*id", "address_id"),
    # Edge case: very short before/after
    ("a*dress", "address"),
    ("addres*", "address"),
    # Multiple possible matches - should pick best
    ("dat*", "date"),  # Could be 'data' or 'date'
    # Complex SQL patterns
    ('COLUMN(NAME="address.add*ess_id")', 'COLUMN(NAME="address.address_id")'),
]

print("Testing Context-Aware PowerBuilder Decoder")
print("=" * 50)

success_count = 0
for corrupted, expected in test_cases:
    # Encode and decode to simulate real usage
    data = corrupted.encode("latin1")
    result = decode_powerbuilder_text(data)

    status = "✓" if result == expected else "✗"
    if result == expected:
        success_count += 1

    print(
        f"\n{status} Test {len(test_cases) - test_cases.index((corrupted, expected))}/{len(test_cases)}:"
    )
    print(f"  Input:    {corrupted}")
    print(f"  Expected: {expected}")
    print(f"  Result:   {result}")

print(
    f"\nOverall Success Rate: {success_count}/{len(test_cases)} ({success_count / len(test_cases) * 100:.1f}%)"
)

# Test with real-world patterns
print("\n\nTesting Real-World Patterns:")
print("-" * 50)

real_patterns = [
    "SELECT person.pers*n_id, person.first_name FROM person",
    "UPDATE cli*ic SET status = 'active'",
    "WHERE trea*ment.treatment_id = 123",
    'TABLE(NAME="per*on_address")',
    'COLUMN(NAME="bil*ing.invoice_id")',
]

for pattern in real_patterns:
    data = pattern.encode("latin1")
    result = decode_powerbuilder_text(data)
    print(f"\nOriginal: {pattern}")
    print(f"Fixed:    {result}")

print("\n\nConclusion:")
print("The context-aware decoder intelligently matches patterns by:")
print("  1. Using both sides of the asterisk as context")
print("  2. Scoring matches based on length, case, and commonality")
print("  3. Preferring exact one-character replacements")
print("  4. No need to define every possible position of *")
