#!/usr/bin/env python3
"""Verify our opcode definitions against expected basic operations."""

import sys
from pathlib import Path

import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def load_our_opcodes() -> None:
    """Load our opcode definitions."""
    opcode_file = project_root / "extract" / "pbd_core" / "opcodes.yaml"
    with open(opcode_file) as f:
        return yaml.safe_load(f)


def check_basic_opcodes() -> None:
    """Check if we have the essential opcodes defined."""
    opcodes = load_our_opcodes()

    # These are the absolute minimum opcodes needed
    expected = {
        "RETURN": (
            "Stack should be empty after this",
            ["RETURN", "RETURN_VAL", "STORE_RETURN_VAL"],
        ),
        "PUSH": (
            "Should push constant value",
            ["PUSH", "PUSH_INT", "PUSH_CONST", "CONST", "PUSHCONST", "LOADCONST"],
        ),
        "ADD": ("Should pop 2, push 1", ["ADD", "ADD_INT", "IADD", "ADDI"]),
        "LOAD": (
            "Should push variable/argument",
            ["LOAD", "LOAD_VAR", "LOADVAR", "GETVAR", "PUSHVAR"],
        ),
        "STORE": (
            "Should pop value to variable",
            ["STORE", "STORE_VAR", "STOREVAR", "SETVAR", "POPVAR"],
        ),
        "CALL": ("Should call function", ["CALL", "INVOKE", "CALLF", "CALLFUNCTION"]),
        "JUMP": (
            "Should jump to address",
            ["JUMP", "GOTO", "BR", "JUMPTRUE", "JUMPFALSE"],
        ),
    }

    # Build a map of mnemonic -> (opcode_value, info)
    found_opcodes = {}
    for opcode_val, op_info in opcodes.items():
        if isinstance(op_info, dict):
            mnemonic = op_info.get("mnemonic", "").upper()
            if mnemonic:
                found_opcodes[mnemonic] = (opcode_val, op_info)

    for _desc, variants in expected.values():
        found = False

        for variant in variants:
            if variant in found_opcodes:
                found = True
                found_opcodes[variant][0]
                break

        if found:
            pass
        else:
            pass

    # Count total opcodes

    # Show opcode value distribution
    ranges = {
        "0x00-0x1F": 0,
        "0x20-0x3F": 0,
        "0x40-0x5F": 0,
        "0x60-0x7F": 0,
        "0x80-0x9F": 0,
        "0xA0-0xBF": 0,
        "0xC0-0xDF": 0,
        "0xE0-0xFF": 0,
        "0x100+": 0,
    }

    for opcode_val in opcodes:
        if isinstance(opcode_val, int):
            val = opcode_val
        else:
            continue

        if val < 0x20:
            ranges["0x00-0x1F"] += 1
        elif val < 0x40:
            ranges["0x20-0x3F"] += 1
        elif val < 0x60:
            ranges["0x40-0x5F"] += 1
        elif val < 0x80:
            ranges["0x60-0x7F"] += 1
        elif val < 0xA0:
            ranges["0x80-0x9F"] += 1
        elif val < 0xC0:
            ranges["0xA0-0xBF"] += 1
        elif val < 0xE0:
            ranges["0xC0-0xDF"] += 1
        elif val < 0x100:
            ranges["0xE0-0xFF"] += 1
        else:
            ranges["0x100+"] += 1

    for count in ranges.values():
        if count > 0:
            pass


def check_reference_opcodes() -> None:
    """Check opcodes from reference implementations."""
    # From pbdviewer - these are confirmed opcodes
    pbdviewer_opcodes = {
        0x00: "HALT/RETURN",
        0x01: "PUSHCONST",
        0x02: "PUSHVAR",
        0x03: "POPVAR",
        0x04: "CALL",
        0x05: "RETURN",
        0x15: "ADD",
        0x16: "SUB",
        0x17: "MUL",
        0x18: "DIV",
    }

    for _opcode_val, _name in sorted(pbdviewer_opcodes.items()):
        pass

    # Check if our opcodes match
    our_opcodes = load_our_opcodes()

    for ref_val, expected_name in pbdviewer_opcodes.items():
        if ref_val in our_opcodes:
            our_info = our_opcodes[ref_val]
            if isinstance(our_info, dict):
                our_mnemonic = our_info.get("mnemonic", "UNNAMED")
                "✓" if any(
                    n in our_mnemonic.upper() for n in expected_name.upper().split("/")
                ) else "?"
            else:
                pass
        else:
            pass


def show_sample_opcodes() -> None:
    """Show a sample of our defined opcodes."""
    opcodes = load_our_opcodes()

    # Show first 20 opcodes
    count = 0
    for opcode_val, op_info in sorted(opcodes.items())[:20]:
        if isinstance(op_info, dict) and isinstance(opcode_val, int):
            op_info.get("mnemonic", "UNNAMED")
            op_info.get("description", "No description")
            count += 1
            if count >= 20:
                break


if __name__ == "__main__":
    check_basic_opcodes()
    check_reference_opcodes()
    show_sample_opcodes()
