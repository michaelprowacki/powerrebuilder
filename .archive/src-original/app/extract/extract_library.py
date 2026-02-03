"""Extract Library Application Service.

Coordinates the extraction of PowerBuilder libraries.
This is the application layer that orchestrates domain operations.
"""

from dataclasses import dataclass
from typing import List, Tuple
from src_new.app.extract.read_pbd import extract_hdr_objects


@dataclass(frozen=True)
class ExtractLibraryDTO:
    """Data transfer object for extraction request."""

    library_path: str
    output_dir: str
    validate_only: bool = False


@dataclass(frozen=True)
class ExtractResult:
    """Result of extraction operation."""

    success: bool
    objects_extracted: int
    errors: List[str]
    format: str = "PBL"


@dataclass(frozen=True)
class ExtractionEvent:
    """Event emitted during extraction."""

    type: str
    data: dict


async def run(
    dto: ExtractLibraryDTO, filesystem
) -> Tuple[ExtractResult, List[ExtractionEvent]]:
    """Run the extraction workflow.

    This is the application service that coordinates:
    1. Reading the library file
    2. Extracting objects
    3. Writing extracted objects

    Args:
        dto: Extraction parameters
        filesystem: Filesystem adapter for I/O operations

    Returns:
        Tuple of extraction result and events
    """
    events = []

    try:
        # Read library file
        library_data = await filesystem.read_binary(dto.library_path)

        # Check format (simplified)
        if library_data[:3] == b"PBL":
            format = "PBL"
        elif library_data[:4] == b"HDR*":
            # PBD files start with HDR* header
            format = "PBD"
        else:
            return (
                ExtractResult(
                    success=False,
                    objects_extracted=0,
                    errors=["Invalid library format"],
                ),
                events,
            )

        if dto.validate_only:
            # Just validate, don't extract
            return (
                ExtractResult(
                    success=True, objects_extracted=0, errors=[], format=format
                ),
                events,
            )

        # Call real extraction for PBD files
        if format == "PBD":
            entries, extraction_errors = extract_hdr_objects(library_data)

            # Write extracted objects to disk
            objects_written = 0
            for entry in entries:
                try:
                    output_path = f"{dto.output_dir}/{entry.name}.pcode"
                    await filesystem.write_binary(output_path, entry.data)
                    objects_written += 1

                    events.append(
                        ExtractionEvent(
                            type="object_extracted",
                            data={"name": entry.name, "size": entry.size},
                        )
                    )
                except Exception as e:
                    extraction_errors.append(str(e))

            events.append(
                ExtractionEvent(
                    type="extraction_completed",
                    data={"library": dto.library_path, "objects": objects_written},
                )
            )

            return (
                ExtractResult(
                    success=True,
                    objects_extracted=objects_written,
                    errors=[
                        err.message if hasattr(err, "message") else str(err)
                        for err in extraction_errors
                    ],
                    format=format,
                ),
                events,
            )
        else:
            # PBL format not yet implemented
            events.append(
                ExtractionEvent(
                    type="extraction_completed",
                    data={"library": dto.library_path, "objects": 0},
                )
            )

            return (
                ExtractResult(
                    success=True,
                    objects_extracted=0,
                    errors=["PBL extraction not yet implemented"],
                    format=format,
                ),
                events,
            )

    except Exception as e:
        return (
            ExtractResult(success=False, objects_extracted=0, errors=[str(e)]),
            events,
        )
