"""
Multi-Tiered P-code Detection System

A progressive detection algorithm that starts with the fastest methods
and escalates to more intensive analysis only when needed.

Tiers:
1. Ultra-Fast Heuristic (< 10ms) - Quick rejection of non-P-code files
2. Fast Pattern Matching (< 100ms) - Boyer-Moore search for common patterns
3. Comprehensive Scan (< 1s) - Full analysis with existing detector
4. Deep Analysis (< 5s) - Control flow and semantic validation

Author: PowerRebuilder Team
Date: 2025-08-09
"""

import time
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from collections import defaultdict

from .detector import PCodeSection, PCodeInfo
from .high_performance_detector import HighPerformancePCodeDetector
from .tiered_config import TieredConfig, AggressivenessLevel

logger = logging.getLogger(__name__)


@dataclass
class TierResult:
    """Result from a detection tier."""

    tier: int
    sections: List[PCodeSection]
    confidence: float
    time_taken: float
    should_escalate: bool
    reason: str


class TieredPCodeDetector:
    """
    Progressive P-code detection with multiple tiers of analysis.

    Each tier provides increasingly comprehensive detection at the cost
    of additional processing time. The detector automatically determines
    when to escalate to higher tiers based on file characteristics and
    detection confidence.
    """

    def __init__(self, config: Optional[TieredConfig] = None) -> None:
        """Initialize with configuration."""
        self.config = config or TieredConfig()
        self.hp_detector = HighPerformancePCodeDetector()
        self._tier_stats: dict[int, dict[str, Any]] = defaultdict(
            lambda: {"calls": 0, "time": 0.0}
        )

        # Common P-code signature patterns for Tier 2
        self.common_patterns = [
            b"\x1b\x00\x01\x00",  # Common function header
            b"\x2b\x00\x00\x00",  # RETURN instruction
            b"\x1a\x00",  # PUSH_VARIABLE
            b"\x39\x00",  # CALL_FUNCTION
            b"\x1f\x00",  # PUSH_CONSTANT
            b"\x4a\x00",  # JUMP_IF_FALSE
            b"\x4b\x00",  # JUMP
            b"\x17\x00",  # LOAD_VARIABLE
            b"\x18\x00",  # STORE_VARIABLE
            b"\x35\x00",  # BINARY_OP
        ]

    def detect_pcode(self, data: bytes, file_path: Optional[str] = None) -> PCodeInfo:
        """
        Main entry point for tiered P-code detection.

        Automatically selects appropriate starting tier based on file
        characteristics and progressively analyzes until sufficient
        confidence is achieved.
        """
        start_time = time.time()
        file_size = len(data)

        logger.info(
            f"Tiered P-code detection starting for {file_path or 'unknown'} "
            f"({file_size:,} bytes) with {self.config.aggressiveness.value} mode"
        )

        # Determine starting tier based on file characteristics
        starting_tier = self._select_starting_tier(data, file_path)

        # Progressive detection through tiers
        all_sections: list[PCodeSection] = []
        total_time = 0.0
        tier_results = []

        for tier in range(starting_tier, 5):
            if tier > self.config.max_tier:
                logger.info(
                    f"Stopping at tier {tier - 1} (max_tier={self.config.max_tier})"
                )
                break

            # Check timeout
            if total_time > self.config.timeout:
                logger.warning(
                    f"Timeout reached after {total_time:.3f}s at tier {tier}"
                )
                break

            # Execute tier detection
            tier_result = self._execute_tier(tier, data, file_path, all_sections)
            tier_results.append(tier_result)

            # Update cumulative results
            all_sections.extend(tier_result.sections)
            total_time += tier_result.time_taken

            # Log tier result
            logger.info(
                f"Tier {tier} completed in {tier_result.time_taken:.3f}s: "
                f"found {len(tier_result.sections)} sections, "
                f"confidence={tier_result.confidence:.2f}, "
                f"escalate={tier_result.should_escalate} ({tier_result.reason})"
            )

            # Check if we should continue to next tier
            if not tier_result.should_escalate:
                break

        # Deduplicate and sort final sections
        final_sections = self._deduplicate_sections(all_sections)

        # Create final result
        max_confidence = max((r.confidence for r in tier_results), default=0.0)
        confidence_str = (
            "high"
            if max_confidence > 0.8
            else "medium"
            if max_confidence > 0.5
            else "low"
            if max_confidence > 0.0
            else "none"
        )

        result = PCodeInfo(
            sections=final_sections,
            confidence=confidence_str,
            detection_time=time.time() - start_time,
            tiers_used=[r.tier for r in tier_results],
            file_size=file_size,
        )

        logger.info(
            f"Tiered detection complete: {len(final_sections)} sections found "
            f"in {result.detection_time:.3f}s using tiers {result.tiers_used}"
        )

        return result

    def _select_starting_tier(self, data: bytes, file_path: Optional[str]) -> int:
        """
        Intelligently select starting tier based on file characteristics.

        Returns tier number (1-4).
        """
        file_size = len(data)

        # Check file extension
        if file_path:
            ext = file_path.lower().split(".")[-1] if "." in file_path else ""
            if ext in ["txt", "md", "xml", "json", "csv"]:
                return 1  # Start with fastest for likely text files
            elif ext in ["fun", "sru", "pbw"]:
                return 2  # Skip heuristic for known P-code files

        # Check for PowerBuilder export header
        if (
            data[:20].startswith(b"$PBExportHeader$")
            or b"HA$PBExportHeader$" in data[:100]
        ):
            return 2  # Skip heuristic for export format

        # Check file size
        if file_size < 1024:  # < 1KB
            return 1  # Very small files start with heuristic
        elif file_size > 10 * 1024 * 1024:  # > 10MB
            return 1  # Very large files need quick rejection
        else:
            return 2  # Medium files can start with pattern matching

    def _execute_tier(
        self,
        tier: int,
        data: bytes,
        file_path: Optional[str],
        existing_sections: List[PCodeSection],
    ) -> TierResult:
        """Execute specific tier detection."""
        tier_start = time.time()

        if tier == 1:
            result = self._tier1_ultra_fast(data, file_path)
        elif tier == 2:
            result = self._tier2_fast_pattern(data, existing_sections)
        elif tier == 3:
            result = self._tier3_comprehensive(data, existing_sections)
        elif tier == 4:
            result = self._tier4_deep_analysis(data, existing_sections)
        else:
            raise ValueError(f"Invalid tier: {tier}")

        # Update statistics
        time_taken = time.time() - tier_start
        self._tier_stats[tier]["calls"] += 1
        self._tier_stats[tier]["time"] += time_taken

        result.time_taken = time_taken
        return result

    def _tier1_ultra_fast(self, data: bytes, file_path: Optional[str]) -> TierResult:
        """
        Tier 1: Ultra-fast heuristic detection (< 10ms).

        Quick checks for obvious non-P-code files.
        """
        # Strategic offset sampling
        sample_offsets = [0x0, 0x200, 0x400, 0x600]
        has_binary_pattern = False

        for offset in sample_offsets:
            if offset + 8 <= len(data):
                chunk = data[offset : offset + 8]
                # Check for binary patterns (non-printable bytes)
                if any(b < 0x20 or b > 0x7E for b in chunk):
                    has_binary_pattern = True
                    break

        # Binary entropy check on first 4KB
        sample_size = min(4096, len(data))
        sample = data[:sample_size]

        # Simple entropy calculation
        byte_counts: dict[int, int] = defaultdict(int)
        for b in sample:
            byte_counts[b] += 1

        import math

        entropy = sum(
            -(count / sample_size) * math.log2(count / sample_size)
            for count in byte_counts.values()
            if count > 0
        )

        # Check for PowerBuilder markers
        has_pb_markers = (
            b"PowerBuilder" in data[:1024]
            or b"$PBExportHeader$" in data[:1024]
            or b"HA$PBExportHeader$" in data[:1024]
        )

        # Decision logic
        confidence = 0.0
        should_escalate = False
        reason = "No P-code indicators"

        if not has_binary_pattern and entropy < 4.0:
            # Likely text file
            confidence = 0.1
            should_escalate = False
            reason = "Text file characteristics"
        elif has_pb_markers:
            # Likely has P-code
            confidence = 0.8
            should_escalate = True
            reason = "PowerBuilder markers found"
        elif has_binary_pattern and 4.0 <= entropy <= 7.0:
            # Could be P-code
            confidence = 0.5
            should_escalate = True
            reason = "Binary pattern with moderate entropy"
        elif entropy > 7.5:
            # Likely compressed/encrypted
            confidence = 0.1
            should_escalate = False
            reason = "High entropy (compressed/encrypted)"

        # Apply configuration
        if confidence < self.config.tier1_confidence_threshold:
            should_escalate = False

        return TierResult(
            tier=1,
            sections=[],
            confidence=confidence,
            time_taken=0.0,
            should_escalate=should_escalate,
            reason=reason,
        )

    def _tier2_fast_pattern(
        self, data: bytes, existing_sections: List[PCodeSection]
    ) -> TierResult:
        """
        Tier 2: Fast pattern matching (< 100ms).

        Boyer-Moore search for common P-code patterns.
        """
        file_size = len(data)

        # Adaptive sampling based on file size
        if file_size < 100 * 1024:  # < 100KB
            sample_interval = 512  # Sample every 512 bytes
        elif file_size < 1024 * 1024:  # < 1MB
            sample_interval = 2048  # Sample every 2KB
        else:
            sample_interval = 4096  # Sample every 4KB

        # Pattern matching with confidence scoring
        pattern_hits: dict[bytes, int] = defaultdict(int)
        total_samples = 0

        for offset in range(0, file_size - 64, sample_interval):
            chunk = data[offset : offset + 64]
            total_samples += 1

            # Check each pattern
            for pattern in self.common_patterns:
                if pattern in chunk:
                    pattern_hits[pattern] += 1

        # Calculate confidence based on pattern density
        if total_samples > 0:
            pattern_density = sum(pattern_hits.values()) / total_samples
            confidence = min(pattern_density * 2, 1.0)  # Scale to 0-1
        else:
            confidence = 0.0

        # Find approximate sections if patterns found
        sections = []
        if confidence > 0.3:
            # Quick section detection at pattern locations
            for offset in range(0, file_size - 1024, 1024):
                chunk = data[offset : offset + 1024]
                for pattern in self.common_patterns[:3]:  # Check top 3 patterns
                    if pattern in chunk:
                        # Found potential section start
                        section = PCodeSection(
                            offset=offset,
                            length=min(1024, file_size - offset),
                            confidence=confidence,
                            pattern_matches=1,
                        )
                        sections.append(section)
                        break

        # Decision logic
        should_escalate = (
            confidence >= self.config.tier2_confidence_threshold and len(sections) > 0
        )

        reason = (
            f"Pattern density: {pattern_density:.2f}"
            if total_samples > 0
            else "No samples taken"
        )

        return TierResult(
            tier=2,
            sections=sections[: self.config.tier2_max_sections],  # Limit sections
            confidence=confidence,
            time_taken=0.0,
            should_escalate=should_escalate,
            reason=reason,
        )

    def _tier3_comprehensive(
        self, data: bytes, existing_sections: List[PCodeSection]
    ) -> TierResult:
        """
        Tier 3: Comprehensive scan (< 1s).

        Full analysis using high-performance detector.
        """
        # Use existing high-performance detector
        raw_sections = self.hp_detector.detect_pcode_sections_fast(data)
        # Convert tuples to PCodeSection objects
        sections = [
            PCodeSection(offset=offset, length=length, confidence=confidence)
            for offset, length, confidence in raw_sections
        ]

        # Calculate confidence based on section quality
        if sections:
            avg_confidence = sum(s.confidence for s in sections) / len(sections)
            total_coverage = sum(s.length for s in sections) / len(data)
            confidence = (avg_confidence + min(total_coverage * 10, 1.0)) / 2
        else:
            confidence = 0.0

        # Decision logic for escalation to Tier 4
        should_escalate = False
        reason = f"Found {len(sections)} sections"

        if self.config.aggressiveness in [
            AggressivenessLevel.THOROUGH,
            AggressivenessLevel.EXHAUSTIVE,
        ]:
            if len(sections) > 5 and confidence < 0.8:
                should_escalate = True
                reason = "Multiple sections with low confidence"
            elif len(data) > 1024 * 1024 and len(sections) > 10:
                should_escalate = True
                reason = "Large file with many sections"

        return TierResult(
            tier=3,
            sections=sections,
            confidence=confidence,
            time_taken=0.0,
            should_escalate=should_escalate,
            reason=reason,
        )

    def _tier4_deep_analysis(
        self, data: bytes, existing_sections: List[PCodeSection]
    ) -> TierResult:
        """
        Tier 4: Deep analysis (< 5s).

        Control flow analysis, fragment recovery, and semantic validation.
        """
        enhanced_sections = list(existing_sections)

        # 1. Control flow analysis
        jump_targets = set()
        for section in existing_sections:
            try:
                section_data = data[section.offset : section.offset + section.length]
                # Look for JUMP instructions (0x4B)
                for i in range(0, len(section_data) - 4, 2):
                    if section_data[i] == 0x4B:
                        # Extract jump target
                        target = int.from_bytes(section_data[i + 2 : i + 4], "little")
                        if 0 <= target < len(data):
                            jump_targets.add(target)
            except Exception as e:
                # Failed to analyze jump targets in section, continue
                logger.debug("Failed to analyze jump targets in section %d: %s", idx, e)

        # 2. Fragment recovery between sections
        if len(existing_sections) > 1:
            sorted_sections = sorted(existing_sections, key=lambda s: s.offset)
            for i in range(len(sorted_sections) - 1):
                gap_start = sorted_sections[i].offset + sorted_sections[i].length
                gap_end = sorted_sections[i + 1].offset

                if 100 < gap_end - gap_start < 10000:  # Reasonable gap size
                    # Check if gap contains jump targets
                    gap_has_target = any(gap_start <= t < gap_end for t in jump_targets)
                    if gap_has_target:
                        # Potential P-code fragment
                        fragment = PCodeSection(
                            offset=gap_start,
                            length=gap_end - gap_start,
                            confidence=0.6,
                            metadata={"source": "fragment_recovery"},
                        )
                        enhanced_sections.append(fragment)

        # 3. Semantic validation of sections
        validated_sections = []
        for section in enhanced_sections:
            try:
                section_data = data[section.offset : section.offset + section.length]

                # Check instruction density
                valid_opcodes = sum(1 for b in section_data[::2] if 0x10 <= b <= 0x60)
                instruction_density = (
                    valid_opcodes / (len(section_data) // 2)
                    if len(section_data) > 1
                    else 0
                )

                # Check for RETURN at end
                has_return = (
                    section_data[-4:-2] == b"\x2b\x00"
                    if len(section_data) >= 4
                    else False
                )

                # Adjust confidence based on validation
                new_confidence = section.confidence
                if instruction_density > 0.7:
                    new_confidence = min(new_confidence + 0.1, 1.0)
                if has_return:
                    new_confidence = min(new_confidence + 0.1, 1.0)

                validated_section = PCodeSection(
                    offset=section.offset,
                    length=section.length,
                    confidence=new_confidence,
                    metadata={
                        **section.metadata,
                        "instruction_density": instruction_density,
                        "has_return": has_return,
                    },
                )
                validated_sections.append(validated_section)

            except:
                # Keep original section if validation fails
                validated_sections.append(section)

        # Final confidence calculation
        if validated_sections:
            confidence = sum(s.confidence for s in validated_sections) / len(
                validated_sections
            )
        else:
            confidence = 0.0

        return TierResult(
            tier=4,
            sections=validated_sections,
            confidence=confidence,
            time_taken=0.0,
            should_escalate=False,  # Tier 4 is final
            reason=f"Deep analysis complete: {len(validated_sections)} validated sections",
        )

    def _deduplicate_sections(self, sections: List[PCodeSection]) -> List[PCodeSection]:
        """Remove duplicate and overlapping sections."""
        if not sections:
            return []

        # Sort by offset
        sorted_sections = sorted(sections, key=lambda s: (s.offset, -s.confidence))

        # Merge overlapping sections
        merged: list[PCodeSection] = []
        for section in sorted_sections:
            if not merged:
                merged.append(section)
                continue

            last = merged[-1]
            if section.offset < last.offset + last.length:
                # Overlap detected
                if section.confidence > last.confidence:
                    # Replace with higher confidence
                    merged[-1] = section
                elif section.offset + section.length > last.offset + last.length:
                    # Extend the section
                    merged[-1] = PCodeSection(
                        offset=last.offset,
                        length=section.offset + section.length - last.offset,
                        confidence=max(last.confidence, section.confidence),
                        metadata={**last.metadata, **section.metadata},
                    )
            else:
                merged.append(section)

        return merged

    def get_statistics(self) -> Dict[str, Any]:
        """Get detection statistics."""
        return {
            "tier_stats": dict(self._tier_stats),
            "config": {
                "aggressiveness": self.config.aggressiveness.value,
                "max_tier": self.config.max_tier,
                "timeout": self.config.timeout,
            },
        }
