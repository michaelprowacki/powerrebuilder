#!/usr/bin/env python3
"""Test P-code offset detection."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.decompile.pcode.decoder import PCodeDecoderV2
from src.decompile.pcode.detector import EnhancedPCodeDetector
from src.extract.utils.version import PowerBuilderVersion


def test_pcode_detection(file_path: Path) -> None:
    """Test P-code detection and decoding."""
    with open(file_path, "rb") as f:
        data = f.read()

    # Show first 256 bytes
    for i in range(0, min(256, len(data)), 16):
        " ".join(f"{b:02x}" for b in data[i : i + 16])
        "".join(chr(b) if 32 <= b < 127 else "." for b in data[i : i + 16])

    # Test P-code detection
    detector = EnhancedPCodeDetector()
    offset, length = detector.find_pcode_in_function(data)

    if offset >= 0:
        pcode_data = data[offset : offset + length]
        for i in range(0, min(128, len(pcode_data)), 16):
            " ".join(f"{b:02x}" for b in pcode_data[i : i + 16])
            "".join(chr(b) if 32 <= b < 127 else "." for b in pcode_data[i : i + 16])

        # Try to decode
        version = PowerBuilderVersion(10, 5, True)
        decoder = PCodeDecoderV2(version)

        try:
            instructions = decoder.decode_pcode(pcode_data[: min(64, len(pcode_data))])
            for _inst in instructions[:10]:  # Show first 10
                pass
        except Exception:
            pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

    test_pcode_detection(Path(sys.argv[1]))
