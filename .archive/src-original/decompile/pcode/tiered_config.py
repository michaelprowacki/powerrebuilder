"""
Configuration for Multi-Tiered P-code Detection System

Provides different aggressiveness levels and tuning parameters
for the tiered detection algorithm.

Author: PowerRebuilder Team
Date: 2025-08-09
"""

from enum import Enum
from dataclasses import dataclass


class AggressivenessLevel(Enum):
    """Detection aggressiveness levels."""

    FAST = "fast"  # Prioritize speed, may miss some P-code
    BALANCED = "balanced"  # Default, good balance of speed and accuracy
    THOROUGH = "thorough"  # More comprehensive, slower
    EXHAUSTIVE = "exhaustive"  # Maximum detection, slowest


@dataclass
class TieredConfig:
    """
    Configuration for tiered P-code detection.

    Different aggressiveness levels provide different trade-offs
    between detection speed and comprehensiveness.
    """

    # General settings
    aggressiveness: AggressivenessLevel = AggressivenessLevel.BALANCED
    max_tier: int = 4  # Maximum tier to use (1-4)
    timeout: float = 10.0  # Total timeout in seconds

    # Tier 1: Ultra-fast heuristic
    tier1_confidence_threshold: float = 0.3  # Min confidence to escalate
    tier1_sample_size: int = 4096  # Bytes to sample for entropy

    # Tier 2: Fast pattern matching
    tier2_confidence_threshold: float = 0.5  # Min confidence to escalate
    tier2_max_sections: int = 20  # Max sections to return from tier 2
    tier2_pattern_count: int = 10  # Number of patterns to check

    # Tier 3: Comprehensive scan
    tier3_early_termination: bool = True  # Stop if high confidence achieved
    tier3_confidence_threshold: float = 0.8  # Confidence for early termination
    tier3_max_sections: int = 100  # Max sections before forcing tier 4

    # Tier 4: Deep analysis
    tier4_fragment_min_gap: int = 100  # Min gap size for fragment recovery
    tier4_fragment_max_gap: int = 10000  # Max gap size for fragment recovery
    tier4_min_instruction_density: float = 0.5  # Min valid instruction ratio

    @classmethod
    def fast(cls) -> "TieredConfig":
        """Fast configuration - prioritize speed."""
        return cls(
            aggressiveness=AggressivenessLevel.FAST,
            max_tier=3,  # Skip deep analysis
            timeout=2.0,
            tier1_confidence_threshold=0.4,
            tier2_confidence_threshold=0.6,
            tier2_max_sections=10,
            tier3_early_termination=True,
            tier3_confidence_threshold=0.7,
            tier3_max_sections=50,
        )

    @classmethod
    def balanced(cls) -> "TieredConfig":
        """Balanced configuration - default."""
        return cls()  # Use defaults

    @classmethod
    def thorough(cls) -> "TieredConfig":
        """Thorough configuration - more comprehensive."""
        return cls(
            aggressiveness=AggressivenessLevel.THOROUGH,
            max_tier=4,
            timeout=20.0,
            tier1_confidence_threshold=0.2,
            tier2_confidence_threshold=0.4,
            tier2_max_sections=30,
            tier3_early_termination=False,
            tier3_max_sections=200,
            tier4_min_instruction_density=0.4,
        )

    @classmethod
    def exhaustive(cls) -> "TieredConfig":
        """Exhaustive configuration - maximum detection."""
        return cls(
            aggressiveness=AggressivenessLevel.EXHAUSTIVE,
            max_tier=4,
            timeout=60.0,
            tier1_confidence_threshold=0.1,
            tier2_confidence_threshold=0.3,
            tier2_max_sections=50,
            tier3_early_termination=False,
            tier3_max_sections=500,
            tier4_fragment_min_gap=50,
            tier4_fragment_max_gap=50000,
            tier4_min_instruction_density=0.3,
        )

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.max_tier < 1 or self.max_tier > 4:
            raise ValueError(f"max_tier must be between 1 and 4, got {self.max_tier}")

        if self.timeout <= 0:
            raise ValueError(f"timeout must be positive, got {self.timeout}")

        # Ensure thresholds are in valid range
        for attr in [
            "tier1_confidence_threshold",
            "tier2_confidence_threshold",
            "tier3_confidence_threshold",
            "tier4_min_instruction_density",
        ]:
            value = getattr(self, attr)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{attr} must be between 0.0 and 1.0, got {value}")
