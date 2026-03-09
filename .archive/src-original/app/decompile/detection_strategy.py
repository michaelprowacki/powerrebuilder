"""Decompile App - Detection Strategy.

Workflow layer for P-code detection strategies.
Coordinates different detection approaches using pure domain functions.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from src_new.domain.decompile.pcode_spec import (
    is_valid_pcode_structure,
    decode_instruction_stream,
    validate_instruction_structure,
    identify_pcode_version,
    PCodeVersion,
)
from src_new.domain.extract.pbd_format import parse_complete_pbd, BlockType


# ============================================================================
# STRATEGY TYPES
# ============================================================================


class DetectionStrategy(str, Enum):
    """Detection strategy options."""

    FAST = "fast"  # Quick structural check
    SPECIFICATION = "specification"  # Specification-based (most robust)
    AUTOMATIC = "automatic"  # Choose based on file
    HEURISTIC = "heuristic"  # Pattern-based (less reliable)


class Confidence(str, Enum):
    """Confidence levels for detection."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CERTAIN = "certain"


@dataclass(frozen=True)
class DetectionResult:
    """Result of P-code detection."""

    is_pcode: bool
    confidence: Confidence
    version: Optional[PCodeVersion]
    instructions_found: int
    time_taken: float
    strategy_used: DetectionStrategy
    issues: List[str] = field(default_factory=list)


# ============================================================================
# DETECTION STRATEGIES
# ============================================================================


def detect_with_strategy(
    data: bytes, strategy: DetectionStrategy = DetectionStrategy.AUTOMATIC
) -> DetectionResult:
    """Detect P-code using specified strategy.

    Workflow function that coordinates domain functions.
    """
    start_time = time.time()

    # Choose strategy based on file characteristics
    if strategy == DetectionStrategy.AUTOMATIC:
        strategy = choose_strategy(data)

    # Execute chosen strategy
    if strategy == DetectionStrategy.FAST:
        result = fast_detection(data)
    elif strategy == DetectionStrategy.SPECIFICATION:
        result = specification_based_detection(data)
    elif strategy == DetectionStrategy.HEURISTIC:
        result = heuristic_detection(data)
    else:
        result = specification_based_detection(data)  # Default to most robust

    # Add timing information
    return DetectionResult(
        is_pcode=result.is_pcode,
        confidence=result.confidence,
        version=result.version,
        instructions_found=result.instructions_found,
        time_taken=time.time() - start_time,
        strategy_used=strategy,
        issues=result.issues,
    )


def choose_strategy(data: bytes) -> DetectionStrategy:
    """Choose detection strategy based on file characteristics.

    Prefers specification-based for reliability.
    """
    # Check for PBD/PBL structure markers
    if data[:4] in [b"HDR*", b"ENT*", b"DAT*"]:
        return DetectionStrategy.SPECIFICATION  # Use spec-based for PBD files

    if data[:3] == b"PBL":
        return DetectionStrategy.SPECIFICATION  # Use spec-based for PBL files

    # For raw P-code, use fast structural check
    return DetectionStrategy.FAST


def fast_detection(data: bytes) -> DetectionResult:
    """Fast structural detection.

    Quick check using structural validation.
    """
    # Quick structural check
    is_pcode = is_valid_pcode_structure(data[: min(4096, len(data))])

    if not is_pcode:
        return DetectionResult(
            is_pcode=False,
            confidence=Confidence.HIGH,
            version=None,
            instructions_found=0,
            time_taken=0,
            strategy_used=DetectionStrategy.FAST,
            issues=["Not valid P-code structure"],
        )

    # Decode a sample to get instruction count
    sample = data[: min(1024, len(data))]
    stream = decode_instruction_stream(sample)

    # Check version
    version = identify_pcode_version(data)

    # Confidence based on structure
    confidence = Confidence.HIGH if stream.instructions else Confidence.LOW

    return DetectionResult(
        is_pcode=True,
        confidence=confidence,
        version=version,
        instructions_found=len(stream.instructions),
        time_taken=0,
        strategy_used=DetectionStrategy.FAST,
        issues=[],
    )


def specification_based_detection(data: bytes) -> DetectionResult:
    """Most robust detection using PBD specification.

    Deterministic detection based on file format spec.
    """
    # Try to parse as PBD structure
    pbd = parse_complete_pbd(data)

    if pbd:
        # Found valid PBD structure
        # Check DAT sections for P-code
        p_code_found = False
        total_instructions = 0
        issues = []

        for block in pbd.data_blocks:
            if block.block_type == BlockType.DAT:
                # Check if DAT section contains valid P-code
                if is_valid_pcode_structure(block.data):
                    p_code_found = True
                    stream = decode_instruction_stream(block.data)
                    total_instructions += len(stream.instructions)

        if p_code_found:
            return DetectionResult(
                is_pcode=True,
                confidence=Confidence.CERTAIN,  # Deterministic
                version=identify_pcode_version(data),
                instructions_found=total_instructions,
                time_taken=0,
                strategy_used=DetectionStrategy.SPECIFICATION,
                issues=[],
            )
        else:
            return DetectionResult(
                is_pcode=False,
                confidence=Confidence.CERTAIN,
                version=None,
                instructions_found=0,
                time_taken=0,
                strategy_used=DetectionStrategy.SPECIFICATION,
                issues=["PBD found but no valid P-code in DAT sections"],
            )

    # Not a PBD file - try as raw P-code
    if is_valid_pcode_structure(data):
        stream = decode_instruction_stream(data)
        is_valid, validation_issues = validate_instruction_structure(stream)

        return DetectionResult(
            is_pcode=is_valid,
            confidence=Confidence.HIGH if is_valid else Confidence.LOW,
            version=identify_pcode_version(data),
            instructions_found=len(stream.instructions),
            time_taken=0,
            strategy_used=DetectionStrategy.SPECIFICATION,
            issues=validation_issues,
        )

    return DetectionResult(
        is_pcode=False,
        confidence=Confidence.CERTAIN,
        version=None,
        instructions_found=0,
        time_taken=0,
        strategy_used=DetectionStrategy.SPECIFICATION,
        issues=["Not valid PBD structure or P-code stream"],
    )


def heuristic_detection(data: bytes) -> DetectionResult:
    """Heuristic pattern-based detection.

    Less reliable but works on damaged files.
    """
    # Look for common P-code patterns
    patterns_found = 0
    common_opcodes = [0x00, 0x01, 0x02, 0x03, 0x04, 0x10, 0x11, 0x20, 0x21, 0x30]

    sample = data[: min(4096, len(data))]
    for byte in sample:
        if byte in common_opcodes:
            patterns_found += 1

    pattern_density = patterns_found / len(sample) if sample else 0

    # Heuristic thresholds
    if pattern_density > 0.3:
        is_pcode = True
        confidence = Confidence.MEDIUM
    elif pattern_density > 0.1:
        is_pcode = True
        confidence = Confidence.LOW
    else:
        is_pcode = False
        confidence = Confidence.LOW

    # Try to decode if we think it's P-code
    instructions_found = 0
    if is_pcode:
        stream = decode_instruction_stream(sample)
        instructions_found = len(stream.instructions)

    return DetectionResult(
        is_pcode=is_pcode,
        confidence=confidence,
        version=identify_pcode_version(data) if is_pcode else None,
        instructions_found=instructions_found,
        time_taken=0,
        strategy_used=DetectionStrategy.HEURISTIC,
        issues=[f"Pattern density: {pattern_density:.2f}"],
    )


# ============================================================================
# PARALLEL DETECTION SUPPORT
# ============================================================================


@dataclass(frozen=True)
class ParallelDetectionRequest:
    """Request for parallel detection."""

    file_id: str
    data: bytes
    strategy: DetectionStrategy


@dataclass(frozen=True)
class ParallelDetectionResult:
    """Result from parallel detection."""

    file_id: str
    result: DetectionResult


def detect_multiple(
    requests: List[ParallelDetectionRequest],
) -> List[ParallelDetectionResult]:
    """Detect P-code in multiple files.

    This is where parallel processing would be coordinated.
    For now, sequential processing.
    """
    results = []

    for request in requests:
        detection_result = detect_with_strategy(request.data, request.strategy)

        results.append(
            ParallelDetectionResult(file_id=request.file_id, result=detection_result)
        )

    return results
