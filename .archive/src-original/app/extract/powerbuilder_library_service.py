"""Extract Application - Extract Library Workflow.

This workflow orchestrates the extraction of PowerBuilder libraries.
It's the only place that coordinates I/O with domain logic.
"""

from dataclasses import dataclass
from typing import List, Tuple
from enum import Enum

from src_new.domain.extract import extract_pbl, extract_pbd
from src_new.domain.extract.shared import ExtractionError
from .ports import IFileReader, IObjectWriter


# ============================================================================
# DTOs - Inline with workflow
# ============================================================================


@dataclass
class ExtractLibraryDTO:
    """Input DTO for library extraction workflow."""

    library_path: str
    output_dir: str
    validate_only: bool = False
    preserve_structure: bool = True


@dataclass
class ExtractResult:
    """Output from extraction workflow."""

    success: bool
    library_path: str
    objects_extracted: int
    errors: List[ExtractionError]
    format: str  # 'PBL' or 'PBD'
    metadata: dict


# ============================================================================
# Events - Returned from workflow
# ============================================================================


class ExtractEventType(Enum):
    """Types of extraction events."""

    LIBRARY_VALIDATED = "library_validated"
    EXTRACTION_STARTED = "extraction_started"
    EXTRACTION_COMPLETED = "extraction_completed"
    EXTRACTION_FAILED = "extraction_failed"
    OBJECT_EXTRACTED = "object_extracted"


@dataclass
class ExtractEvent:
    """Event from extraction workflow."""

    type: ExtractEventType
    library_path: str
    data: dict


# ============================================================================
# Workflow
# ============================================================================


async def run(
    dto: ExtractLibraryDTO,
    file_reader: IFileReader,
    object_writer: IObjectWriter,
) -> Tuple[ExtractResult, List[ExtractEvent]]:
    """Extract library workflow.

    This is the main workflow that orchestrates extraction.
    It coordinates between domain functions and I/O ports.

    Args:
        dto: Input parameters for extraction
        file_reader: Port for reading files
        object_writer: Port for writing extracted objects

    Returns:
        Tuple of (result, events) where events can be published
    """
    events = []

    # Read file through port
    if not await file_reader.file_exists(dto.library_path):
        return ExtractResult(
            success=False,
            library_path=dto.library_path,
            objects_extracted=0,
            errors=[
                ExtractionError(
                    entry_name="<file>", message=f"File not found: {dto.library_path}"
                )
            ],
            format="unknown",
            metadata={},
        ), events

    try:
        data = await file_reader.read_binary(dto.library_path)
    except Exception as e:
        return ExtractResult(
            success=False,
            library_path=dto.library_path,
            objects_extracted=0,
            errors=[
                ExtractionError(
                    entry_name="<file>", message=f"Failed to read file: {str(e)}"
                )
            ],
            format="unknown",
            metadata={},
        ), events

    # Determine format and validate
    is_pbl = extract_pbl.validate_pbl_format(data)
    is_pbd = extract_pbd.validate_pbd_format(data)

    if not is_pbl and not is_pbd:
        events.append(
            ExtractEvent(
                type=ExtractEventType.EXTRACTION_FAILED,
                library_path=dto.library_path,
                data={"reason": "Invalid library format"},
            )
        )
        return ExtractResult(
            success=False,
            library_path=dto.library_path,
            objects_extracted=0,
            errors=[
                ExtractionError(
                    entry_name="<format>", message="Not a valid PBL or PBD file"
                )
            ],
            format="unknown",
            metadata={},
        ), events

    format_type = "PBL" if is_pbl else "PBD"

    events.append(
        ExtractEvent(
            type=ExtractEventType.LIBRARY_VALIDATED,
            library_path=dto.library_path,
            data={"format": format_type},
        )
    )

    # Stop here if validate only
    if dto.validate_only:
        metadata = (
            extract_pbl.get_library_info(data)
            if is_pbl
            else {"format": "PBD", "valid": True}
        )
        return ExtractResult(
            success=True,
            library_path=dto.library_path,
            objects_extracted=0,
            errors=[],
            format=format_type,
            metadata=metadata,
        ), events

    # Extract objects using appropriate domain function
    events.append(
        ExtractEvent(
            type=ExtractEventType.EXTRACTION_STARTED,
            library_path=dto.library_path,
            data={"format": format_type},
        )
    )

    if is_pbl:
        entries, errors = extract_pbl.extract_objects(data)
    else:
        entries, errors = extract_pbd.extract_hdr_objects(data)

    # Write extracted objects through port
    if entries and not dto.validate_only:
        try:
            await object_writer.write_entries(dto.output_dir, entries)

            # Write metadata
            metadata = {
                "library_path": dto.library_path,
                "format": format_type,
                "objects_extracted": len(entries),
                "errors_encountered": len(errors),
                "preserve_structure": dto.preserve_structure,
            }
            await object_writer.write_metadata(dto.output_dir, metadata)

        except Exception as e:
            errors.append(
                ExtractionError(
                    entry_name="<write>", message=f"Failed to write objects: {str(e)}"
                )
            )

    # Generate object extracted events
    for entry in entries[:10]:  # Limit events for performance
        events.append(
            ExtractEvent(
                type=ExtractEventType.OBJECT_EXTRACTED,
                library_path=dto.library_path,
                data={"name": entry.name, "type": entry.type.value, "size": entry.size},
            )
        )

    # Final event
    if errors:
        events.append(
            ExtractEvent(
                type=ExtractEventType.EXTRACTION_COMPLETED,
                library_path=dto.library_path,
                data={
                    "objects": len(entries),
                    "errors": len(errors),
                    "partial_success": True,
                },
            )
        )
    else:
        events.append(
            ExtractEvent(
                type=ExtractEventType.EXTRACTION_COMPLETED,
                library_path=dto.library_path,
                data={"objects": len(entries), "success": True},
            )
        )

    return ExtractResult(
        success=len(entries) > 0,
        library_path=dto.library_path,
        objects_extracted=len(entries),
        errors=errors,
        format=format_type,
        metadata={"entries": len(entries), "errors": len(errors)},
    ), events


async def run_batch(
    libraries: List[str],
    output_dir: str,
    file_reader: IFileReader,
    object_writer: IObjectWriter,
) -> Tuple[List[ExtractResult], List[ExtractEvent]]:
    """Batch extraction workflow.

    Extract multiple libraries in sequence.
    """
    results = []
    all_events = []

    for library_path in libraries:
        dto = ExtractLibraryDTO(library_path=library_path, output_dir=output_dir)
        result, events = await run(dto, file_reader, object_writer)
        results.append(result)
        all_events.extend(events)

    return results, all_events
