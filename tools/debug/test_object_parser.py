#!/usr/bin/env python3
"""Test the PowerBuilder object parser on .fun files."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.decompile.analyzers.parser import ObjectParser
from src.decompile.pcode.decoder import PCodeDecoderV2
from src.extract.utils.version import PowerBuilderVersion


def test_parser() -> None:
    # Find a .fun file
    output_dir = Path("output")
    fun_files = list(output_dir.glob("**/*.fun"))[:3]  # Test first 3

    if not fun_files:
        return

    for fun_file in fun_files:
        with open(fun_file, "rb") as f:
            data = f.read()

        # Parse the object
        pb_object = ObjectParser.parse_object(data, fun_file.stem)

        if not pb_object:
            continue

        if pb_object.pcode_data:
            # Show first few bytes of P-code
            for i in range(0, min(32, len(pb_object.pcode_data)), 16):
                " ".join(f"{b:02x}" for b in pb_object.pcode_data[i : i + 16])

            # Try to decode
            version = PowerBuilderVersion(10, 5, True)
            decoder = PCodeDecoderV2(version)

            try:
                decoded = decoder.decode_pcode_section(
                    pb_object.pcode_data,
                    fun_file.stem,
                    None,
                )

                if decoded and decoded.instructions:
                    # Show first few instructions
                    for i, _inst in enumerate(decoded.instructions[:5]):
                        pass
                else:
                    pass
            except Exception:
                pass


if __name__ == "__main__":
    test_parser()
