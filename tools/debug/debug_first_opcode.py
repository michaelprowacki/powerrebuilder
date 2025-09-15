#!/usr/bin/env python3
"""Debug tool to examine the first bytes of P-code files and decode them."""

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.decompile.opcodes import OPCODE_TABLE


def debug_first_bytes(pcode_file: str) -> None:
    """Debug the first bytes of a P-code file."""
    with open(pcode_file, "rb") as f:
        data = f.read(100)  # First 100 bytes

    # Show raw bytes

    # Look for patterns
    freq = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1

    for _byte, _count in sorted(freq.items(), key=lambda x: -x[1])[:10]:
        pass

    # Try to interpret as opcodes
    opcodes = OPCODE_TABLE

    pc = 0
    decoded = []
    while pc < min(len(data), 50):  # First 50 bytes
        opcode = data[pc]

        if opcode in opcodes:
            op_info = opcodes[opcode]
            decoded.append(
                f"  {pc:04x}: 0x{opcode:02x} {op_info.get('mnemonic', 'UNKNOWN')}",
            )
            pc += 1

            # Skip operands if we know the size
            if "size" in op_info:
                pc += op_info["size"] - 1
        else:
            decoded.append(f"  {pc:04x}: 0x{opcode:02x} *** UNKNOWN ***")
            pc += 1

    # Look for string patterns (often UTF-16 in PowerBuilder)
    try:
        # Try to decode as UTF-16 LE
        text = data.decode("utf-16-le", errors="ignore")
        printable = "".join(c if c.isprintable() else "." for c in text)
        if any(c.isalpha() for c in printable):
            pass
    except Exception as e:
        logger.debug("Exception caught: %s", e)

    # Look for ASCII strings
    ascii_str = ""
    for b in data:
        if 32 <= b <= 126:  # Printable ASCII
            ascii_str += chr(b)
        else:
            if len(ascii_str) > 3:  # String of at least 4 chars
                pass
            ascii_str = ""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

    debug_first_bytes(sys.argv[1])
