#!/usr/bin/env python3
"""Analyze DAT header format to determine correct data length field size."""

import struct


def analyze_dat_header(data: bytes, offset: int) -> dict:
    """Analyze a DAT header at the given offset."""
    if offset + 12 > len(data):
        return {"error": "Not enough data for header"}

    # Check for DAT* signature
    signature = data[offset : offset + 4]
    if signature != b"DAT*":
        return {"error": f"Invalid signature: {signature}"}

    # Read next block offset (4 bytes)
    next_offset = struct.unpack("<I", data[offset + 4 : offset + 8])[0]

    # Try both interpretations of data length
    # Option 1: 2 bytes (unsigned short) as per reference implementation
    data_len_2byte = struct.unpack("<H", data[offset + 8 : offset + 10])[0]

    # Option 2: 4 bytes (unsigned int) as per our implementation
    data_len_4byte = struct.unpack("<I", data[offset + 8 : offset + 12])[0]

    # Check which makes more sense
    remaining_data = (
        len(data) - offset - 12
    )  # Data after 12-byte header (if 4-byte length)
    remaining_data_2b = (
        len(data) - offset - 10
    )  # Data after 10-byte header (if 2-byte length)

    # Get preview of data after header
    preview_2b = (
        data[offset + 10 : offset + 20].hex() if offset + 20 <= len(data) else "N/A"
    )
    preview_4b = (
        data[offset + 12 : offset + 22].hex() if offset + 22 <= len(data) else "N/A"
    )

    return {
        "offset": offset,
        "signature": signature.decode("ascii"),
        "next_offset": next_offset,
        "data_len_2byte": data_len_2byte,
        "data_len_4byte": data_len_4byte,
        "remaining_after_2b": remaining_data_2b,
        "remaining_after_4b": remaining_data,
        "preview_2b": preview_2b,
        "preview_4b": preview_4b,
        "makes_sense_2b": 0 < data_len_2byte <= remaining_data_2b,
        "makes_sense_4b": 0 < data_len_4byte <= remaining_data,
    }


def main() -> None:
    """Analyze DAT headers in test data."""

    # Example: The problematic value from logs
    problematic_value = 1146094070  # 0x445001f6
    print("Problematic value analysis:")
    print(f"  Decimal: {problematic_value}")
    print(f"  Hex: 0x{problematic_value:08x}")
    print(
        f"  As 4 bytes (little-endian): {problematic_value.to_bytes(4, 'little').hex()}"
    )

    # If interpreted as 2-byte length + 2 bytes of data
    length_part = problematic_value & 0xFFFF  # Lower 2 bytes
    data_part = (problematic_value >> 16) & 0xFFFF  # Upper 2 bytes
    print("  If split as 2+2 bytes:")
    print(f"    Length (2 bytes): {length_part} (0x{length_part:04x})")
    print(
        f"    Data start (2 bytes): {data_part} (0x{data_part:04x}) = '{chr(data_part & 0xFF)}{chr(data_part >> 8)}'"
    )
    print()

    # Test with known DAT header pattern
    # Simulate a DAT block: DAT* + next_offset + length + data
    test_cases = [
        # Case 1: 2-byte length (502 bytes of data)
        {
            "name": "2-byte length format",
            "data": b"DAT*"
            + struct.pack("<I", 0x0DA200)
            + struct.pack("<H", 502)
            + b"PD"
            + b"\x00" * 500,
        },
        # Case 2: 4-byte length (would give problematic value)
        {
            "name": "4-byte length format (problematic)",
            "data": b"DAT*"
            + struct.pack("<I", 0x0DA200)
            + struct.pack("<I", 0x445001F6)
            + b"\x00" * 100,
        },
    ]

    for test in test_cases:
        print(f"\nTest case: {test['name']}")
        result = analyze_dat_header(test["data"], 0)
        for key, value in result.items():
            print(f"  {key}: {value}")

    # Conclusion
    print("\nCONCLUSION:")
    print("The reference implementation uses 2-byte data length fields in DAT headers.")
    print("Our problematic value 0x445001f6 occurs when we incorrectly read 4 bytes")
    print("and include the first 2 bytes of actual data ('PD') as part of the length.")


if __name__ == "__main__":
    main()
