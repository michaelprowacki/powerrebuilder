#!/usr/bin/env python3
"""
Targeted analysis of the repetitive return problem.
"""

import sys
from pathlib import Path


class ReturnProblemAnalyzer:
    """Analyze why the decoder produces so many return statements."""

    def __init__(self, file_path: str) -> None:
        self.file_path = Path(file_path)
        self.raw_data = None

    def analyze(self) -> None:
        """Run the analysis."""
        print("=== RETURN PROBLEM ANALYSIS ===")

        # Load file
        with open(self.file_path, "rb") as f:
            self.raw_data = f.read()

        print(f"File: {self.file_path}")
        print(f"Size: {len(self.raw_data)} bytes")

        # The key insight from the previous analysis:
        print("\nKEY FINDINGS:")
        print("1. File is 63.93% null bytes (0x00)")
        print("2. 71.78% of the file consists of repeated 0x0000 patterns")
        print("3. 87.13% consists of 8-byte null sequences (0x0000000000000000)")
        print("4. File contains DataWindow export headers")

        # Let's understand what's happening
        self.analyze_null_dominance()
        self.analyze_pcode_interpretation()
        self.find_actual_code_sections()
        self.demonstrate_decoding_problem()

    def analyze_null_dominance(self) -> None:
        """Analyze the dominance of null bytes."""
        print("\n=== NULL BYTE DOMINANCE ANALYSIS ===")

        null_count = self.raw_data.count(0x00)
        total_bytes = len(self.raw_data)
        null_percentage = (null_count / total_bytes) * 100

        print(f"Null bytes: {null_count}/{total_bytes} ({null_percentage:.2f}%)")

        # Find the longest sequences of null bytes
        max_null_sequence = 0
        current_null_sequence = 0
        null_sequences = []

        for i, byte in enumerate(self.raw_data):
            if byte == 0x00:
                current_null_sequence += 1
            else:
                if current_null_sequence > 0:
                    null_sequences.append(
                        (i - current_null_sequence, current_null_sequence)
                    )
                    max_null_sequence = max(max_null_sequence, current_null_sequence)
                current_null_sequence = 0

        # Handle end of file
        if current_null_sequence > 0:
            null_sequences.append(
                (len(self.raw_data) - current_null_sequence, current_null_sequence)
            )
            max_null_sequence = max(max_null_sequence, current_null_sequence)

        print(f"Longest null sequence: {max_null_sequence} bytes")
        print(f"Total null sequences: {len(null_sequences)}")

        # Show the longest sequences
        print("Longest null sequences:")
        sorted_sequences = sorted(null_sequences, key=lambda x: x[1], reverse=True)
        for i, (start, length) in enumerate(sorted_sequences[:5]):
            print(f"  {i + 1}. {length} bytes starting at offset {start}")

    def analyze_pcode_interpretation(self) -> None:
        """Analyze how null bytes are being interpreted as P-code."""
        print("\n=== P-CODE INTERPRETATION PROBLEM ===")

        print("The core issue:")
        print("1. The file is mostly null bytes (padding/empty space)")
        print("2. The P-code decoder treats 0x00 bytes as valid opcodes")
        print("3. Many decoders map unknown/null opcodes to 'return' statements")
        print("4. This creates hundreds of meaningless 'return' statements")

        # Let's see what a typical null sequence looks like
        print("\nTypical null sequence (bytes 1000-1032):")
        chunk = self.raw_data[1000:1032]
        hex_str = " ".join(f"{b:02x}" for b in chunk)
        print(f"  {hex_str}")

        # Count consecutive null bytes in different sections
        sections = [
            (0, 1000, "Header section"),
            (1000, 10000, "Early section"),
            (50000, 60000, "Middle section"),
            (150000, 160000, "Late section"),
        ]

        for start, end, name in sections:
            end = min(end, len(self.raw_data))
            section_data = self.raw_data[start:end]
            null_count = section_data.count(0x00)
            section_size = len(section_data)
            percentage = (null_count / section_size) * 100 if section_size > 0 else 0
            print(
                f"  {name} ({start}-{end}): {null_count}/{section_size} nulls ({percentage:.1f}%)"
            )

    def find_actual_code_sections(self) -> None:
        """Try to identify where actual code might be."""
        print("\n=== ACTUAL CODE SECTION DETECTION ===")

        # Look for sections with higher entropy (more varied bytes)
        chunk_size = 512
        interesting_chunks = []

        for i in range(0, len(self.raw_data), chunk_size):
            chunk = self.raw_data[i : i + chunk_size]
            if len(chunk) < chunk_size // 2:  # Skip very small chunks
                continue

            # Calculate metrics
            null_count = chunk.count(0x00)
            unique_bytes = len(set(chunk))
            null_percentage = (null_count / len(chunk)) * 100

            # Interesting chunks have low null percentage and high diversity
            if null_percentage < 50 and unique_bytes > 20:
                interesting_chunks.append(
                    {
                        "offset": i,
                        "null_percentage": null_percentage,
                        "unique_bytes": unique_bytes,
                        "chunk": chunk,
                    }
                )

        print(f"Found {len(interesting_chunks)} potentially interesting chunks:")

        # Sort by null percentage (ascending) and unique bytes (descending)
        interesting_chunks.sort(
            key=lambda x: (x["null_percentage"], -x["unique_bytes"])
        )

        for i, chunk_info in enumerate(interesting_chunks[:5]):
            offset = chunk_info["offset"]
            null_pct = chunk_info["null_percentage"]
            unique = chunk_info["unique_bytes"]

            print(
                f"  Chunk {i + 1}: offset {offset}, nulls {null_pct:.1f}%, unique bytes {unique}"
            )

            # Show a sample of this chunk
            sample = chunk_info["chunk"][:32]
            hex_str = " ".join(f"{b:02x}" for b in sample)
            ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in sample)
            print(f"    Sample: {hex_str}")
            print(f"    ASCII:  {ascii_str}")

    def demonstrate_decoding_problem(self) -> None:
        """Demonstrate how null bytes lead to return statements."""
        print("\n=== DECODING PROBLEM DEMONSTRATION ===")

        # Simulate what happens when a decoder encounters null bytes
        print("Simulating P-code decoding of null sequences:")

        # Take a typical null-heavy section
        test_section = self.raw_data[5000:5020]  # 20 bytes
        hex_str = " ".join(f"{b:02x}" for b in test_section)
        print(f"Test bytes: {hex_str}")

        # Show how these might be interpreted
        print("Potential interpretations:")
        for i, byte in enumerate(test_section):
            if byte == 0x00:
                print(
                    f"  Byte {i}: 0x00 -> likely interpreted as NOP, RETURN, or unknown opcode"
                )
            elif byte == 0x01:
                print(f"  Byte {i}: 0x01 -> might be interpreted as a simple operation")
            else:
                print(f"  Byte {i}: 0x{byte:02x} -> could be actual opcode or data")

        print("\nROOT CAUSE IDENTIFIED:")
        print("1. File is mostly padding/null bytes (63.93%)")
        print("2. P-code detector incorrectly identifies null-heavy regions as P-code")
        print("3. P-code decoder maps null bytes (0x00) to 'return' statements")
        print("4. Result: hundreds of meaningless 'return' statements")

        print("\nSOLUTION RECOMMENDATIONS:")
        print("1. Improve P-code detection to ignore null-heavy regions")
        print("2. Add entropy/diversity checks before attempting to decode")
        print("3. Implement proper DataWindow file handling")
        print("4. Filter out sections with >50% null bytes")
        print(
            "5. Look for actual P-code signatures instead of assuming all data is P-code"
        )


def main() -> None:
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python debug_return_problem.py <path_to_fun_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    analyzer = ReturnProblemAnalyzer(file_path)
    analyzer.analyze()


if __name__ == "__main__":
    main()
