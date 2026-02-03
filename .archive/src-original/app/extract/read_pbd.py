"""Extract PBD Application Service.

Operations for extracting objects from PBD files (HDR* format).
This is the HOW - workflows that use domain types.
Following Scott Wlaschin's FDM principles.
"""

import struct
from typing import List, Tuple, Optional
from src_new.domain.powerbuilder.library import PBLHeader, PBLEntry, PBObjectType


# ============================================================================
# EXTRACTION ERRORS
# ============================================================================


class ExtractionError:
    """Error during extraction."""

    def __init__(self, entry_name: str, message: str, offset: Optional[int] = None):
        self.entry_name = entry_name
        self.message = message
        self.offset = offset

    def __str__(self) -> str:
        if self.offset:
            return f"Error extracting {self.entry_name} at offset {self.offset}: {self.message}"
        return f"Error extracting {self.entry_name}: {self.message}"


class InvalidLibraryFormat(Exception):
    """Invalid library format exception."""

    pass


# HDR* format markers
HDR_SIGNATURE = b"HDR*"
ENT_SIGNATURE = b"ENT*"
DAT_SIGNATURE = b"DAT*"
NOD_SIGNATURE = b"NOD*"
FRE_SIGNATURE = b"FRE*"


def parse_hdr_header(data: bytes) -> PBLHeader:
    """Parse HDR* format header (modern PBD format).

    Pure function: bytes -> PBLHeader
    """
    if len(data) < 16:
        raise InvalidLibraryFormat("Header too small for HDR* format")

    if data[:4] != HDR_SIGNATURE:
        raise InvalidLibraryFormat(f"Not HDR* format: {data[:4]}")

    # Parse HDR* header structure
    version = 0x0700  # Version 7.0 format

    # Find ENT* section for entry count
    ent_offset = data.find(ENT_SIGNATURE)
    if ent_offset == -1:
        entry_count = 0
    else:
        # Read entry count from ENT* section
        ent_data = data[ent_offset + 4 : ent_offset + 8]
        if len(ent_data) == 4:
            entry_count = struct.unpack("<I", ent_data)[0]
        else:
            entry_count = 0

    return PBLHeader(
        signature=HDR_SIGNATURE, version=version, entry_count=entry_count, format="PBD"
    )


def extract_hdr_objects(data: bytes) -> Tuple[List[PBLEntry], List[ExtractionError]]:
    """Extract objects from HDR* format PBD.

    Pure function that handles the modern PBD format.
    Returns extracted entries and any errors encountered.
    """
    try:
        header = parse_hdr_header(data)
    except InvalidLibraryFormat as e:
        return [], [ExtractionError(entry_name="<header>", message=str(e))]

    entries = []
    errors = []

    # Find ENT* section
    ent_offset = data.find(ENT_SIGNATURE)
    if ent_offset == -1:
        errors.append(
            ExtractionError(entry_name="<entries>", message="No ENT* section found")
        )
        return entries, errors

    # Find DAT* sections
    dat_offset = 0
    while True:
        dat_offset = data.find(DAT_SIGNATURE, dat_offset)
        if dat_offset == -1:
            break

        try:
            entry = extract_dat_entry(data, dat_offset)
            if entry:
                entries.append(entry)
        except Exception as e:
            errors.append(
                ExtractionError(
                    entry_name=f"DAT@{dat_offset}", message=str(e), offset=dat_offset
                )
            )

        dat_offset += 4  # Move past current DAT* marker

    return entries, errors


def extract_dat_entry(data: bytes, offset: int) -> Optional[PBLEntry]:
    """Extract a single entry from DAT* section.

    Pure function to parse DAT* section data.
    """
    if offset + 16 > len(data):
        return None

    # Skip DAT* marker
    pos = offset + 4

    # Read section length
    length_bytes = data[pos : pos + 4]
    if len(length_bytes) < 4:
        return None
    section_length = struct.unpack("<I", length_bytes)[0]
    pos += 4

    # Extract metadata and object data
    if pos + section_length > len(data):
        return None

    section_data = data[pos : pos + section_length]

    # Parse object metadata from section
    # This is simplified - real format is more complex
    name, object_type, object_data = parse_dat_metadata(section_data)

    if name and object_data:
        return PBLEntry(
            name=name,
            object_type=object_type,
            size=len(object_data),
            offset=offset,
            data=object_data,
        )

    return None


def parse_dat_metadata(
    section_data: bytes,
) -> Tuple[Optional[str], PBObjectType, bytes]:
    """Parse metadata from DAT* section data.

    Extracts object name, type, and actual data.
    """
    if len(section_data) < 100:
        return None, PBObjectType.GLOBAL, b""

    # Try to extract strings (UTF-16LE encoded)
    strings = extract_unicode_strings(section_data)

    # First string is usually the object name
    name = strings[0] if strings else None

    # Determine type from metadata patterns
    object_type = detect_object_type(section_data)

    # The actual object data (simplified extraction)
    # In reality, this would need to parse the complex structure
    object_data = section_data

    return name, object_type, object_data


def extract_unicode_strings(data: bytes) -> List[str]:
    """Extract UTF-16LE strings from binary data.

    Pure function to find and decode Unicode strings.
    """
    strings = []
    i = 0

    while i < len(data) - 1:
        # Look for potential UTF-16LE string start
        if data[i] != 0 and data[i + 1] == 0:
            # Found potential string start
            string_bytes = bytearray()
            j = i

            while j < len(data) - 1:
                low = data[j]
                high = data[j + 1]

                if low == 0 and high == 0:
                    # String terminator
                    break

                string_bytes.extend([low, high])
                j += 2

            if string_bytes:
                try:
                    decoded = string_bytes.decode("utf-16le")
                    if decoded.isprintable() and len(decoded) > 2:
                        strings.append(decoded)
                except UnicodeDecodeError:
                    pass

            i = j + 2
        else:
            i += 1

    return strings


def detect_object_type(data: bytes) -> PBObjectType:
    """Detect object type from DAT* section patterns.

    Uses heuristics to determine the type of object.
    """
    # Convert to lowercase for pattern matching
    data_lower = data.lower()

    # Check for type indicators
    if b"window" in data_lower:
        return PBObjectType.WINDOW
    elif b"datawindow" in data_lower:
        return PBObjectType.DATAWINDOW
    elif b"menu" in data_lower:
        return PBObjectType.MENU
    elif b"function" in data_lower:
        return PBObjectType.FUNCTION
    elif b"user_object" in data_lower or b"userobject" in data_lower:
        return PBObjectType.USEROBJECT
    elif b"application" in data_lower:
        return PBObjectType.APPLICATION
    elif b"structure" in data_lower:
        return PBObjectType.STRUCTURE
    else:
        return PBObjectType.GLOBAL


def parse_dat_metadata(
    section_data: bytes,
) -> Tuple[Optional[str], str, Optional[bytes]]:
    """Parse metadata from DAT* section data.

    Returns: (name, object_type, object_data)
    """
    if len(section_data) < 8:
        return None, "unknown", None

    # Skip header bytes and find start of UTF-16LE text
    # DAT* sections have metadata bytes before the actual name
    text_start = 0
    for i in range(min(16, len(section_data) - 4)):
        # Look for UTF-16LE pattern: printable ASCII followed by 0x00
        if (
            i + 3 < len(section_data)
            and section_data[i + 1] == 0
            and section_data[i + 3] == 0
            and 0x20 <= section_data[i] <= 0x7F
        ):  # Printable ASCII range
            text_start = i
            break

    # If no UTF-16LE pattern found, try to skip common header sizes
    if text_start == 0:
        # Common header sizes are 2, 4, or 6 bytes
        if len(section_data) > 6 and section_data[6:7] != b"\x00":
            text_start = 6
        elif len(section_data) > 4 and section_data[4:5] != b"\x00":
            text_start = 4
        elif len(section_data) > 2:
            text_start = 2

    # Extract name from the text portion
    name_data = section_data[text_start:]

    # Find end of name (double null for UTF-16 or single null)
    name_end = name_data.find(b"\x00\x00")
    if name_end == -1:
        name_end = name_data.find(b"\x00")
    if name_end == -1:
        name_end = min(256, len(name_data))

    name_bytes = name_data[
        : name_end
        + (
            2
            if name_end > 0 and name_data[name_end : name_end + 2] == b"\x00\x00"
            else 1
        )
    ]

    try:
        # Check if it's UTF-16LE (every other byte is 0x00 for ASCII chars)
        if len(name_bytes) > 1 and b"\x00" in name_bytes[1::2]:
            name = name_bytes.decode("utf-16-le", errors="ignore").strip("\x00").strip()
        else:
            name = name_bytes.decode("ascii", errors="ignore").strip("\x00").strip()

        # Clean up name - remove non-printable chars
        name = "".join(c for c in name if c.isprintable() or c in " _-.")

        if not name:
            name = f"object_{text_start:02x}_{hash(section_data) & 0xFFFFFF:06x}"
    except:
        name = f"object_{hash(name_bytes) & 0xFFFFFF:06x}"

    # Rest is object data (after name and some padding)
    data_start = text_start + len(name_bytes) + 2  # Skip name and padding
    object_data = (
        section_data[data_start:] if data_start < len(section_data) else section_data
    )

    # Determine type from data patterns
    object_type = "unknown"
    if b"datawindow" in object_data[:100].lower():
        object_type = PBObjectType.DATAWINDOW.value
    elif b"window" in object_data[:100].lower():
        object_type = PBObjectType.WINDOW.value
    elif b"function" in object_data[:100].lower():
        object_type = PBObjectType.FUNCTION.value

    return name, object_type, object_data


def validate_pbd_format(data: bytes) -> bool:
    """Validate if data is a valid PBD format (HDR*).

    Pure predicate function.
    """
    if len(data) < 4:
        return False

    return data[:4] == HDR_SIGNATURE


def is_modern_format(data: bytes) -> bool:
    """Check if file uses modern HDR* format.

    Pure predicate to distinguish old vs new formats.
    """
    return data[:4] == HDR_SIGNATURE if len(data) >= 4 else False
