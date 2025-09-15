#!/usr/bin/env python3
"""Test real P-code extraction and decompilation."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.decompile.opcodes import OPCODE_TABLE
from src.decompile.pcode.detector import PCodeDetector
from src.extract.pbd.library import Library


def test_real_pcode() -> None:
    """Test with real P-code from PBD file."""
    pbd_file = "tests/fixtures/pbd_files/dcm_email.pbd"

    try:
        with Library(pbd_file) as lib:
            # List entries
            entries = lib.list_entries()

            # Find functions
            functions = [e for e in entries if e.lower().endswith(".fun")]

            if functions:
                # Extract first function
                func_name = functions[0]

                obj = lib[func_name]
                if obj and obj.data:
                    # Detect P-code
                    detector = PCodeDetector()
                    pcode_sections = detector.detect_pcode_sections(obj.data)

                    if pcode_sections:
                        # Analyze first section
                        start, end = pcode_sections[0]
                        pcode_data = obj.data[start:end]

                        # Show hex dump of first 100 bytes
                        for i in range(0, min(100, len(pcode_data)), 16):
                            " ".join(f"{b:02x}" for b in pcode_data[i : i + 16])
                            "".join(
                                chr(b) if 32 <= b <= 126 else "."
                                for b in pcode_data[i : i + 16]
                            )

                        # Simple opcode analysis
                        analyze_pcode(pcode_data)

                        # Save for further analysis
                        output_file = "output/test_real.pcode"
                        Path(output_file).parent.mkdir(exist_ok=True)
                        with open(output_file, "wb") as f:
                            f.write(pcode_data)

    except Exception:
        import traceback

        traceback.print_exc()


def analyze_pcode(pcode_data) -> None:
    """Analyze P-code with corrected opcodes."""
    opcodes = OPCODE_TABLE

    # Simple decode
    pc = 0
    instructions = []
    unknown_count = 0

    while pc < min(len(pcode_data), 200):  # First 200 bytes
        opcode = pcode_data[pc]

        if opcode in opcodes:
            op_info = opcodes[opcode]
            mnemonic = op_info.get("mnemonic", f"OP_{opcode:02X}")
            instructions.append((pc, opcode, mnemonic))
        else:
            instructions.append((pc, opcode, f"UNKNOWN_{opcode:02X}"))
            unknown_count += 1

        pc += 1

    # Show first 20 instructions
    for _addr, opcode, mnemonic in instructions[:20]:
        pass

    # Count known vs unknown

    # Frequency analysis
    freq = {}
    for _, opcode, _ in instructions:
        freq[opcode] = freq.get(opcode, 0) + 1

    for opcode, _count in sorted(freq.items(), key=lambda x: -x[1])[:10]:
        mnemonic = (
            opcodes[opcode].get("mnemonic", f"UNKNOWN_{opcode:02X}")
            if opcode in opcodes
            else f"UNKNOWN_{opcode:02X}"
        )


def main() -> None:
    """Main function."""
    test_real_pcode()


if __name__ == "__main__":
    main()
