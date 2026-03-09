"""P-code detection and analysis module.

This module provides multi-tiered P-code detection for PowerBuilder files,
with progressive analysis from fast heuristics to deep semantic analysis.
"""

from .detector import PCodeDetector, PCodeSection, PCodeInfo
from .high_performance_detector import HighPerformancePCodeDetector

# Import tiered detector if available
try:
    from .tiered_detector import TieredPCodeDetector, TierResult
    from .tiered_config import TieredConfig, AggressivenessLevel

    _tiered_available = True
except ImportError:
    _tiered_available = False
    TieredPCodeDetector = None  # type: ignore
    TierResult = None  # type: ignore
    TieredConfig = None  # type: ignore
    AggressivenessLevel = None  # type: ignore

# Default detector - use high performance detector
default_detector = HighPerformancePCodeDetector()


def detect_pcode(
    data: bytes, filename: str = "", use_tiered: bool = False
) -> PCodeInfo:
    """Detect P-code sections using the appropriate detector.

    Args:
        data: Raw binary data to analyze
        filename: Optional filename for optimization hints
        use_tiered: Whether to use tiered detection (if available)

    Returns:
        PCodeInfo object with detected sections
    """
    if use_tiered and _tiered_available:
        detector = TieredPCodeDetector()
        return detector.detect_pcode(data, filename)
    else:
        raw_sections = default_detector.detect_pcode_sections_fast(data)
        sections = [
            PCodeSection(offset=offset, length=length, confidence=confidence)
            for offset, length, confidence in raw_sections
        ]
        return PCodeInfo(
            sections=sections,
            pcode_offset=sections[0].offset if sections else -1,
            pcode_length=sum(s.length for s in sections),
            confidence="high" if sections else "none",
        )


__all__ = [
    "PCodeDetector",
    "PCodeSection",
    "PCodeInfo",
    "HighPerformancePCodeDetector",
    "detect_pcode",
]

# Add tiered detector exports if available
if _tiered_available:
    __all__.extend(
        [
            "TieredPCodeDetector",
            "TierResult",
            "TieredConfig",
            "AggressivenessLevel",
        ]
    )
