#!/usr/bin/env python3
"""
Simple PBD extraction script that directly extracts files without complex dependencies.
"""

import struct
import logging
import sys
from pathlib import Path
from typing import Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimplePBDExtractor:
    """Simple PBD/PBL file extractor."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.entries = []

    def extract_all(self, output_dir: Path) -> int:
        """Extract all entries from PBD file.

        Returns:
            Number of files extracted
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.file_path, "rb") as f:
                data = f.read()

            # PowerBuilder library files have specific structure
            # Try to find entry headers
            extracted = 0

            # Look for HDR* markers which indicate entry headers
            offset = 0
            while offset < len(data) - 4:
                # Look for HDR* marker
                if data[offset : offset + 4] == b"HDR*":
                    logger.info(f"Found HDR* marker at offset {offset}")

                    # Try to extract entry
                    entry_data = self._extract_entry(data, offset)
                    if entry_data:
                        name, content = entry_data

                        # Save to file
                        output_file = output_dir / name
                        output_file.write_bytes(content)

                        logger.info(f"Extracted: {name} ({len(content)} bytes)")
                        extracted += 1

                    # Move to next potential entry
                    offset += 512  # PBD entries are typically aligned
                else:
                    offset += 1

            # Also try to extract based on ENT* markers (entry data)
            offset = 0
            while offset < len(data) - 4:
                if data[offset : offset + 4] == b"ENT*":
                    logger.info(f"Found ENT* marker at offset {offset}")

                    # Try to extract P-code
                    pcode_data = self._extract_pcode(data, offset)
                    if pcode_data:
                        name, content = pcode_data

                        # Save to file
                        output_file = output_dir / name
                        output_file.write_bytes(content)

                        logger.info(f"Extracted P-code: {name} ({len(content)} bytes)")
                        extracted += 1

                    offset += 512
                else:
                    offset += 1

            # If no HDR*/ENT* markers found, try alternative extraction
            if extracted == 0:
                logger.info(
                    "No HDR*/ENT* markers found, trying alternative extraction..."
                )
                extracted = self._extract_alternative(data, output_dir)

            return extracted

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return 0

    def _extract_entry(self, data: bytes, offset: int) -> Optional[Tuple[str, bytes]]:
        """Extract a single entry starting at offset."""
        try:
            # Skip HDR* marker
            offset += 4

            # Read entry size (next 4 bytes, little-endian)
            if offset + 4 > len(data):
                return None

            entry_size = struct.unpack("<I", data[offset : offset + 4])[0]
            offset += 4

            if entry_size == 0 or entry_size > len(data):
                return None

            # Read entry data
            entry_data = data[offset : offset + min(entry_size, len(data) - offset)]

            # Try to extract name from entry
            # PowerBuilder entries often have the name in the first part
            name_end = entry_data.find(b"\x00")
            if name_end > 0:
                name = entry_data[:name_end].decode("latin-1", errors="ignore")
                # Clean the name
                name = "".join(c for c in name if c.isalnum() or c in "._-")

                if name:
                    return f"{name}.fun", entry_data

            # Generate a default name
            return f"entry_{offset:08x}.fun", entry_data

        except Exception as e:
            logger.debug(f"Failed to extract entry at {offset}: {e}")
            return None

    def _extract_pcode(self, data: bytes, offset: int) -> Optional[Tuple[str, bytes]]:
        """Extract P-code data starting at offset."""
        try:
            # Similar to _extract_entry but for P-code sections
            # P-code entries have different structure

            # Skip ENT* marker
            offset += 4

            # Read until next marker or reasonable size
            end_offset = offset + 1024  # Start with 1KB chunk

            # Look for next marker
            for i in range(offset, min(offset + 65536, len(data) - 4)):
                if data[i : i + 4] in [b"HDR*", b"ENT*", b"NOD*", b"FRE*"]:
                    end_offset = i
                    break

            pcode_data = data[offset:end_offset]

            if len(pcode_data) > 0:
                # Generate name based on offset
                return f"pcode_{offset:08x}.fun", pcode_data

        except Exception as e:
            logger.debug(f"Failed to extract P-code at {offset}: {e}")

        return None

    def _extract_alternative(self, data: bytes, output_dir: Path) -> int:
        """Alternative extraction method for files without clear markers."""
        extracted = 0

        try:
            # Look for PowerBuilder object signatures
            # PowerBuilder compiled code often contains specific patterns

            # Method 1: Look for function signatures
            offset = 0
            while offset < len(data) - 100:
                # Look for common PowerBuilder bytecode patterns
                # 0x01 0x00 often starts a function
                if data[offset : offset + 2] == b"\x01\x00":
                    # Try to extract a chunk as potential P-code
                    chunk_size = min(4096, len(data) - offset)
                    chunk = data[offset : offset + chunk_size]

                    # Save as potential P-code file
                    output_file = output_dir / f"potential_pcode_{offset:08x}.fun"
                    output_file.write_bytes(chunk)

                    logger.info(f"Extracted potential P-code at offset {offset}")
                    extracted += 1

                    offset += chunk_size
                else:
                    offset += 1

                # Limit number of extractions to avoid too many false positives
                if extracted >= 50:
                    break

            # Method 2: Split file into chunks if nothing else worked
            if extracted == 0:
                chunk_size = 65536  # 64KB chunks
                for i in range(0, len(data), chunk_size):
                    chunk = data[i : i + chunk_size]
                    if len(chunk) > 0:
                        output_file = output_dir / f"chunk_{i:08x}.dat"
                        output_file.write_bytes(chunk)
                        extracted += 1

                logger.info(f"Extracted {extracted} chunks from file")

        except Exception as e:
            logger.error(f"Alternative extraction failed: {e}")

        return extracted


def main():
    """Main entry point."""
    if len(sys.argv) != 3:
        print("Usage: simple_extract.py <pbd_file> <output_dir>")
        sys.exit(1)

    pbd_file = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])

    if not pbd_file.exists():
        logger.error(f"File not found: {pbd_file}")
        sys.exit(1)

    logger.info(f"Extracting {pbd_file} to {output_dir}")

    extractor = SimplePBDExtractor(pbd_file)
    count = extractor.extract_all(output_dir)

    if count > 0:
        logger.info(f"Successfully extracted {count} files")
    else:
        logger.error("No files extracted")
        sys.exit(1)


if __name__ == "__main__":
    main()
