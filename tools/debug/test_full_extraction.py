#!/usr/bin/env python3
"""Test full extraction process to understand P-code format issues."""

import struct


def create_test_pbd_data() -> None:
    """Create a minimal test PBD with known P-code data."""
    # This would create test data - for now, let's analyze real data


def analyze_extraction_issue() -> None:
    """Analyze why extracted P-code doesn't match expected format."""
    # The hex dump from the original message shows:
    # 00000000: 4841 2450 4245 7870 6f72 7448 6561 6465  HA$PBExportHeade
    # 00000010: 7224 665f 6765 745f 7573 6572 6e61 6d65  r$f_get_username
    # 00000020: 2e66 756e 0a24 5042 4578 706f 7274 436f  .fun.$PBExportCo
    # 00000030: 6d6d 656e 7473 240a 0300 6e40 0100 1000  mments$...n@....
    # 00000040: 0000 36e0 eb44 a9c8 134f 0800 0000 1000  ..6..D...O......

    raw_data = bytes.fromhex(
        "48412450424578706f7274486561646572"  # HA$PBExportHeader
        "24665f6765745f757365726e616d65"  # $f_get_username
        "2e66756e0a2450424578706f7274436f"  # .fun.$PBExportCo
        "6d6d656e7473240a"  # mments$.
        "03006e4001001000000036e0eb44a9c8134f0800000010",  # P-code data
    )

    # Find header boundaries
    header_end = raw_data.find(b"\n$PBExportComments$\n")
    if header_end < 0:
        first_nl = raw_data.find(b"\n")
        second_nl = raw_data.find(b"\n", first_nl + 1)
        header_end = second_nl
    else:
        header_end += len(b"$PBExportComments$\n") - 1

    pcode_data = raw_data[header_end + 1 :]

    # Show hex dump
    for i in range(0, len(pcode_data), 16):
        " ".join(f"{b:02x}" for b in pcode_data[i : i + 16])
        "".join(chr(b) if 32 <= b < 127 else "." for b in pcode_data[i : i + 16])

    # Try different interpretations

    # 1. As function structure (code_len, debug_len, unknown, data)
    if len(pcode_data) >= 6:
        code_len = struct.unpack("<H", pcode_data[0:2])[0]
        struct.unpack("<H", pcode_data[2:4])[0]
        struct.unpack("<H", pcode_data[4:6])[0]

        if code_len < 1000 and 6 + code_len <= len(pcode_data):
            pass

    # 2. As raw P-code
    opcodes = []
    i = 0
    while i < min(20, len(pcode_data)):
        opcode = pcode_data[i]
        opcodes.append(f"0x{opcode:02x}")
        i += 1

    # 3. Check for patterns
    # Check if it starts with known P-code patterns
    if pcode_data[:2] == b"\x00\x00" or pcode_data[0] == 0x03 or pcode_data[0] == 0x04:
        pass

    # 4. Check if this might be object metadata, not P-code


if __name__ == "__main__":
    analyze_extraction_issue()
