#!/usr/bin/env python3
"""
Comprehensive P-code decoding pipeline debugger.
Analyzes the root cause of repetitive return statements in decompiled code.
"""

import os
import sys

sys.path.insert(0, os.path.abspath("."))

import logging
from pathlib import Path

from src.common.utils.datawindow import DataWindowUtils
from src.decompile.analyzers.parser import ObjectParser
from src.decompile.pcode.decoder import PCodeDecoder

# Import the actual decompiler components
from src.decompile.pcode.detector import PCodeDetector
from src.decompile.pcode.detector_enhanced import EnhancedPCodeDetector
from src.decompile.pcode.opcodes.definitions import OPCODES

# Set up logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class PCodePipelineDebugger:
    """Debug the P-code decoding pipeline step by step."""

    def __init__(self, file_path: str) -> None:
        self.file_path = Path(file_path)
        self.raw_data = None
        self.pcode_sections = []
        self.decoded_instructions = []

    def load_file(self) -> bytes:
        """Load the .fun file and return raw binary data."""
        print(f"\n=== STEP 1: Loading file {self.file_path} ===")

        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        with open(self.file_path, "rb") as f:
            self.raw_data = f.read()

        print(f"File size: {len(self.raw_data)} bytes")
        print(f"First 64 bytes (hex): {self.raw_data[:64].hex()}")
        print(f"First 64 bytes (ascii): {self.raw_data[:64]}")

        # Check for P-code header patterns
        header_patterns = [
            b"HA$PBExportHeader",
            b"$PBExportComments",
            b"\x03\x00",  # Common P-code start
            b"\x6e\x40",  # Another common pattern
        ]

        for pattern in header_patterns:
            pos = self.raw_data.find(pattern)
            if pos >= 0:
                print(f"Found pattern {pattern} at offset {pos}")

        return self.raw_data

    def analyze_file_structure(self) -> None:
        """Analyze the overall structure of the .fun file."""
        print("\n=== STEP 2: Analyzing file structure ===")

        # Look for section boundaries
        section_markers = []

        # Check for repeated patterns that might indicate sections
        for i in range(0, min(1000, len(self.raw_data) - 4), 4):
            chunk = self.raw_data[i : i + 4]
            if chunk == b"\x00\x00\x00\x00":
                section_markers.append(i)

        print(f"Found {len(section_markers)} potential section boundaries (null bytes)")

        # Look for P-code instruction patterns
        pcode_patterns = []
        for i in range(len(self.raw_data) - 1):
            byte = self.raw_data[i]
            # Look for common P-code opcodes
            if byte in [0x03, 0x04, 0x05, 0x06, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]:
                pcode_patterns.append((i, byte))

        print(f"Found {len(pcode_patterns)} potential P-code instruction bytes")
        if pcode_patterns:
            print(f"First 10 P-code patterns: {pcode_patterns[:10]}")

    def test_pcode_detection(self) -> None:
        """Test both P-code detection implementations."""
        print("\n=== STEP 3: Testing P-code detection ===")

        # Test original detector
        print("\n--- Testing Original PCodeDetector ---")
        try:
            detector = PCodeDetector()
            original_sections = detector.detect_pcode_sections(self.raw_data)
            print(f"Original detector found {len(original_sections)} sections")

            for i, section in enumerate(original_sections[:5]):  # Show first 5
                print(
                    f"Section {i}: offset={section.get('offset', 'N/A')}, "
                    f"size={section.get('size', 'N/A')}, "
                    f"type={section.get('type', 'N/A')}"
                )

        except Exception as e:
            print(f"Original detector failed: {e}")
            original_sections = []

        # Test enhanced detector
        print("\n--- Testing Enhanced PCodeDetector ---")
        try:
            enhanced_detector = EnhancedPCodeDetector()
            enhanced_sections = enhanced_detector.detect_pcode_sections(self.raw_data)
            print(f"Enhanced detector found {len(enhanced_sections)} sections")

            for i, section in enumerate(enhanced_sections[:5]):  # Show first 5
                print(
                    f"Section {i}: offset={section.get('offset', 'N/A')}, "
                    f"size={section.get('size', 'N/A')}, "
                    f"type={section.get('type', 'N/A')}"
                )

        except Exception as e:
            print(f"Enhanced detector failed: {e}")
            enhanced_sections = []

        # Store best result
        if enhanced_sections:
            self.pcode_sections = enhanced_sections
        elif original_sections:
            self.pcode_sections = original_sections
        else:
            print("WARNING: No P-code sections detected!")

    def test_object_parser(self) -> None:
        """Test the object parser."""
        print("\n=== STEP 4: Testing object parser ===")

        try:
            parser = ObjectParser()
            parsed_data = parser.parse_object_data(self.raw_data)
            print(f"Object parser result type: {type(parsed_data)}")

            if isinstance(parsed_data, dict):
                print(f"Object parser keys: {list(parsed_data.keys())}")

                # Look for P-code related data
                if "pcode" in parsed_data:
                    pcode_data = parsed_data["pcode"]
                    print(f"P-code data type: {type(pcode_data)}")
                    if isinstance(pcode_data, bytes):
                        print(f"P-code data length: {len(pcode_data)} bytes")
                        print(f"P-code first 32 bytes: {pcode_data[:32].hex()}")

        except Exception as e:
            print(f"Object parser failed: {e}")
            import traceback

            traceback.print_exc()

    def test_pcode_decoding(self) -> None:
        """Test P-code decoding on detected sections."""
        print("\n=== STEP 5: Testing P-code decoding ===")

        if not self.pcode_sections:
            print("No P-code sections to decode!")
            return

        decoder = PCodeDecoder()

        for i, section in enumerate(self.pcode_sections[:3]):  # Test first 3 sections
            print(f"\n--- Decoding section {i} ---")

            try:
                # Extract section data
                offset = section.get("offset", 0)
                size = section.get("size", 100)  # Default size if not specified

                if offset + size > len(self.raw_data):
                    size = len(self.raw_data) - offset

                section_data = self.raw_data[offset : offset + size]
                print(f"Section data length: {len(section_data)} bytes")
                print(f"Section data (hex): {section_data[:32].hex()}")

                # Decode the section
                instructions = decoder.decode_pcode(section_data)
                print(f"Decoded {len(instructions)} instructions")

                # Show first 10 instructions
                for j, instr in enumerate(instructions[:10]):
                    print(f"  {j}: {instr}")

                # Check for repetitive patterns
                if len(instructions) > 5:
                    instruction_types = [
                        instr.get("opcode", "unknown") for instr in instructions
                    ]
                    unique_types = set(instruction_types)
                    print(f"Unique instruction types: {unique_types}")

                    # Count repetitions
                    type_counts = {}
                    for instr_type in instruction_types:
                        type_counts[instr_type] = type_counts.get(instr_type, 0) + 1

                    print(f"Instruction type counts: {type_counts}")

                    # Check for excessive repetition
                    total_instructions = len(instructions)
                    for instr_type, count in type_counts.items():
                        if (
                            count > total_instructions * 0.5
                        ):  # More than 50% of instructions
                            print(
                                f"WARNING: Excessive repetition of {instr_type}: {count}/{total_instructions} ({count / total_instructions * 100:.1f}%)"
                            )

                self.decoded_instructions.extend(instructions)

            except Exception as e:
                print(f"Failed to decode section {i}: {e}")
                import traceback

                traceback.print_exc()

    def analyze_opcode_mapping(self) -> None:
        """Analyze the opcode mapping for potential issues."""
        print("\n=== STEP 6: Analyzing opcode mapping ===")

        # Check what opcodes are being used
        if not self.decoded_instructions:
            print("No decoded instructions to analyze!")
            return

        opcodes_used = {}
        for instr in self.decoded_instructions:
            opcode = instr.get("opcode", "unknown")
            opcodes_used[opcode] = opcodes_used.get(opcode, 0) + 1

        print(f"Opcodes used: {opcodes_used}")

        # Check if these opcodes are properly mapped
        print("\nOpcode mapping analysis:")
        for opcode, count in opcodes_used.items():
            if opcode in OPCODES:
                mapping = OPCODES[opcode]
                print(f"  {opcode} ({count} times): {mapping}")
            else:
                print(f"  {opcode} ({count} times): NOT MAPPED!")

        # Look for the specific issue with return statements
        if "return" in opcodes_used or "RETURN" in opcodes_used:
            return_count = opcodes_used.get("return", 0) + opcodes_used.get("RETURN", 0)
            total_count = len(self.decoded_instructions)
            print("\nRETURN STATEMENT ANALYSIS:")
            print(
                f"Return statements: {return_count}/{total_count} ({return_count / total_count * 100:.1f}%)"
            )

            if return_count > total_count * 0.5:
                print("ROOT CAUSE IDENTIFIED: Excessive return statements detected!")

    def analyze_raw_bytes(self, start_offset: int = 0, length: int = 200) -> None:
        """Analyze raw bytes to understand the data structure."""
        print("\n=== STEP 7: Raw byte analysis ===")

        if start_offset >= len(self.raw_data):
            print(f"Start offset {start_offset} exceeds file length!")
            return

        end_offset = min(start_offset + length, len(self.raw_data))
        data_slice = self.raw_data[start_offset:end_offset]

        print(f"Analyzing bytes {start_offset}-{end_offset}:")

        # Hex dump style output
        for i in range(0, len(data_slice), 16):
            hex_part = " ".join(f"{b:02x}" for b in data_slice[i : i + 16])
            ascii_part = "".join(
                chr(b) if 32 <= b < 127 else "." for b in data_slice[i : i + 16]
            )
            print(f"{start_offset + i:08x}: {hex_part:<48} {ascii_part}")

        # Look for patterns
        patterns = {}
        for i in range(len(data_slice) - 1):
            byte = data_slice[i]
            patterns[byte] = patterns.get(byte, 0) + 1

        print("\nByte frequency analysis:")
        sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
        for byte, count in sorted_patterns[:10]:
            print(
                f"  0x{byte:02x}: {count} times ({count / len(data_slice) * 100:.1f}%)"
            )

    def test_datawindow_utils(self) -> None:
        """Test DataWindow utilities for potential issues."""
        print("\n=== STEP 8: Testing DataWindow utilities ===")

        try:
            # Test if this is a DataWindow file
            is_datawindow = DataWindowUtils.is_datawindow_content(self.raw_data)
            print(f"Is DataWindow content: {is_datawindow}")

            if is_datawindow:
                print("This appears to be a DataWindow file, not a regular function!")
                print(
                    "This might explain why P-code decoding is producing unexpected results."
                )

                # Try to extract DataWindow-specific information
                dw_info = DataWindowUtils.extract_datawindow_info(self.raw_data)
                print(f"DataWindow info: {dw_info}")

        except Exception as e:
            print(f"DataWindow utils test failed: {e}")

    def run_full_debug(self) -> None:
        """Run the complete debug pipeline."""
        print("=== P-CODE PIPELINE DEBUGGER ===")
        print(f"Analyzing file: {self.file_path}")

        try:
            # Step 1: Load file
            self.load_file()

            # Step 2: Analyze structure
            self.analyze_file_structure()

            # Step 3: Test P-code detection
            self.test_pcode_detection()

            # Step 4: Test object parser
            self.test_object_parser()

            # Step 5: Test P-code decoding
            self.test_pcode_decoding()

            # Step 6: Analyze opcode mapping
            self.analyze_opcode_mapping()

            # Step 7: Raw byte analysis
            self.analyze_raw_bytes()

            # Step 8: Test DataWindow utilities
            self.test_datawindow_utils()

            print("\n=== DEBUG COMPLETE ===")

        except Exception as e:
            print(f"Debug failed: {e}")
            import traceback

            traceback.print_exc()


def main() -> None:
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python debug_pcode_pipeline.py <path_to_fun_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    debugger = PCodePipelineDebugger(file_path)
    debugger.run_full_debug()


if __name__ == "__main__":
    main()
