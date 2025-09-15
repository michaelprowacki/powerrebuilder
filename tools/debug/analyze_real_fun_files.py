#!/usr/bin/env python3
"""Analyze real .fun files from extraction to understand their format."""

import logging
import struct
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.decompile.pcode.decoder import PCodeDecoderV2
from src.extract.utils.version import PowerBuilderVersion


def analyze_fun_file(file_path: Path) -> None:
    """Comprehensive analysis of a .fun file."""
    with open(file_path, "rb") as f:
        data = f.read()

    # Step 1: Check for PowerBuilder export header
    has_header = data.startswith(b"HA$PBExportHeader$")

    pcode_start = 0
    if has_header:
        # Find header boundaries
        first_nl = data.find(b"\n")
        second_nl = data.find(b"\n", first_nl + 1)

        if first_nl > 0 and second_nl > 0:
            data[18:first_nl].decode("utf-8", errors="ignore")
            data[first_nl + 1 : second_nl].decode("utf-8", errors="ignore")
            pcode_start = second_nl + 1

    # Step 2: Get the data after header
    raw_data = data[pcode_start:]

    # Show first 128 bytes
    for i in range(0, min(128, len(raw_data)), 16):
        " ".join(f"{b:02x}" for b in raw_data[i : i + 16])
        "".join(chr(b) if 32 <= b < 127 else "." for b in raw_data[i : i + 16])

    # Step 3: Try to interpret as function structure
    if len(raw_data) >= 6:
        # Standard function format: code_len, debug_len, unknown
        code_len = struct.unpack("<H", raw_data[0:2])[0]
        debug_len = struct.unpack("<H", raw_data[2:4])[0]
        struct.unpack("<H", raw_data[4:6])[0]

        # Check if sizes are reasonable
        expected_size = 6 + code_len + (debug_len * 4)

        if code_len > 0 and code_len < len(raw_data) and expected_size <= len(raw_data):
            pcode = raw_data[6 : 6 + code_len]

            for i in range(0, min(64, len(pcode)), 16):
                " ".join(f"{b:02x}" for b in pcode[i : i + 16])

            # Try to decode first few instructions
            version = PowerBuilderVersion(10, 5, True)
            decoder = PCodeDecoderV2(version)

            try:
                instructions = decoder.decode_pcode(pcode[: min(32, len(pcode))])
                for _inst in instructions[:5]:
                    pass
            except Exception:
                logger.debug("Generic exception caught")
        else:
            pass

    # Step 4: Try alternative interpretations

    # Check if it might be raw P-code
    if len(raw_data) >= 10:
        # Look for opcode patterns
        potential_opcodes = []
        for i in range(10):
            if i < len(raw_data):
                potential_opcodes.append(f"0x{raw_data[i]:02x}")

    # Check for other patterns
    if raw_data[:4] == b"\x00\x00\x00\x00":
        pass
    if raw_data[:2] == b"PB":
        pass
    if raw_data[:3] == b"DAT":
        pass

    # Look for strings
    for i in range(len(raw_data) - 4):
        if all(32 <= raw_data[j] <= 126 for j in range(i, min(i + 4, len(raw_data)))):
            # Found printable string
            end = i
            while end < len(raw_data) and 32 <= raw_data[end] <= 126:
                end += 1
            if end - i >= 4:
                raw_data[i:end].decode("ascii", errors="ignore")
                i = end


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        sys.exit(1)

    analyze_fun_file(file_path)


if __name__ == "__main__":
    main()
