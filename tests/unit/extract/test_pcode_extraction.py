#!/usr/bin/env python3
"""Test P-code extraction to see raw bytes."""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.extract.pbd.data_block import get_binary_from_data
from src.extract.pbd.library import Library


def test_extract_pcode() -> None:
    """Extract P-code and show hex dump."""
    pbd_path = Path("data/input/pbd_files/dcm_accounting.pbd")
    object_name = "of_get_linked_acc.fun"

    with Library(str(pbd_path)) as library:
        if object_name not in library.entries_map:
            return

        # Check entry first
        entry = library.entries_map[object_name]

        # Get the PBD object
        try:
            pbd_obj = library[object_name]
        except Exception:
            # Try manual extraction
            with open(pbd_path, "rb") as f:
                f.seek(entry.offset)
                data = f.read(entry.objectsize)
                binary_data = data

        else:
            # Get binary data
            binary_data = get_binary_from_data(pbd_obj)

        if binary_data:
            # Print hex dump
            for i in range(0, min(256, len(binary_data)), 16):
                " ".join(f"{b:02x}" for b in binary_data[i : i + 16])
                "".join(
                    chr(b) if 32 <= b < 127 else "." for b in binary_data[i : i + 16]
                )

            # Look for P-code markers

            # Check for known patterns
            for i in range(len(binary_data) - 4):
                # Look for potential P-code start
                if binary_data[i : i + 2] == b"\x00\x00" and binary_data[i + 2] != 0:
                    if i > 0:
                        # Show context
                        start = max(0, i - 16)
                        end = min(len(binary_data), i + 32)
                        for j in range(start, end, 16):
                            " ".join(f"{b:02x}" for b in binary_data[j : j + 16])


if __name__ == "__main__":
    test_extract_pcode()
