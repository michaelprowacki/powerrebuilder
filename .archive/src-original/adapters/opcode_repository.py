"""Decompile Infrastructure - Opcode Repository.

Loads and provides opcode information from external data.
This is the adapter layer that loads opcode meanings.
"""

import json
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Optional, Protocol
from enum import Enum


# ============================================================================
# OPCODE DATA TYPES (for enrichment)
# ============================================================================


class OpcodeCategory(str, Enum):
    """Semantic categories for opcodes."""

    CONTROL_FLOW = "control_flow"
    STACK = "stack"
    ARITHMETIC = "arithmetic"
    COMPARISON = "comparison"
    MEMORY = "memory"
    DATABASE = "database"
    OBJECT = "object"
    STRING = "string"
    ARRAY = "array"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class OpcodeInfo:
    """Information about an opcode from external data."""

    code: int
    name: str
    category: OpcodeCategory
    stack_effect: str  # e.g., "2 -> 1"
    description: Optional[str] = None
    arg_format: Optional[str] = None  # e.g., "uint16,uint8"


# ============================================================================
# REPOSITORY INTERFACE
# ============================================================================


class IOpcodeRepository(Protocol):
    """Interface for opcode information repository."""

    def get_opcode_info(self, code: int) -> Optional[OpcodeInfo]:
        """Get information about an opcode."""
        ...

    def has_opcode(self, code: int) -> bool:
        """Check if opcode exists in repository."""
        ...


# ============================================================================
# JSON-BASED REPOSITORY
# ============================================================================


class JsonOpcodeRepository:
    """Repository that loads opcodes from JSON file."""

    def __init__(self, json_path: Path):
        """Initialize with path to opcode JSON file."""
        self.json_path = json_path
        self.opcodes: Dict[int, OpcodeInfo] = {}
        self._load_opcodes()

    def _load_opcodes(self) -> None:
        """Load opcodes from JSON file."""
        try:
            with open(self.json_path, "r") as f:
                data = json.load(f)

            # Parse opcodes from the reference format
            for hex_code, opcode_data in data.get("opcodes", {}).items():
                # Convert hex string to int
                code = int(hex_code, 16) if hex_code.startswith("0x") else int(hex_code)

                # Map category
                category_map = {
                    "sm": OpcodeCategory.SYSTEM,
                    "control": OpcodeCategory.CONTROL_FLOW,
                    "stack": OpcodeCategory.STACK,
                    "arithmetic": OpcodeCategory.ARITHMETIC,
                    "comparison": OpcodeCategory.COMPARISON,
                    "memory": OpcodeCategory.MEMORY,
                    "database": OpcodeCategory.DATABASE,
                    "object": OpcodeCategory.OBJECT,
                    "string": OpcodeCategory.STRING,
                    "array": OpcodeCategory.ARRAY,
                }

                category_str = opcode_data.get("category", "unknown")
                category = category_map.get(category_str, OpcodeCategory.UNKNOWN)

                # Create OpcodeInfo
                info = OpcodeInfo(
                    code=code,
                    name=opcode_data.get("name", f"UNKNOWN_{code:02X}"),
                    category=category,
                    stack_effect=opcode_data.get("stack_effect", "? -> ?"),
                    description=opcode_data.get("description"),
                    arg_format=self._extract_arg_format(opcode_data),
                )

                self.opcodes[code] = info

        except FileNotFoundError:
            # No opcode file - will return unknowns
            pass
        except json.JSONDecodeError as e:
            # Invalid JSON - log but continue
            print(f"Warning: Invalid opcode JSON: {e}")

    def _extract_arg_format(self, opcode_data: dict) -> Optional[str]:
        """Extract argument format from opcode data."""
        # Check implementations for arg info
        implementations = opcode_data.get("implementations", {})
        for impl_name, impl_data in implementations.items():
            arg_count = impl_data.get("arg_count", 0)
            if arg_count > 0:
                # Infer format from length and arg count
                length = opcode_data.get("length", 1)
                if length == 2 and arg_count == 1:
                    return "uint8"
                elif length == 3 and arg_count == 1:
                    return "uint16"
                elif length == 5 and arg_count == 1:
                    return "uint32"
                elif length == 4 and arg_count == 2:
                    return "uint8,uint16"
        return None

    def get_opcode_info(self, code: int) -> Optional[OpcodeInfo]:
        """Get information about an opcode."""
        if code in self.opcodes:
            return self.opcodes[code]

        # Return unknown opcode info
        return OpcodeInfo(
            code=code,
            name=f"UNKNOWN_{code:02X}",
            category=OpcodeCategory.UNKNOWN,
            stack_effect="? -> ?",
            description=f"Unknown opcode 0x{code:02X}",
        )

    def has_opcode(self, code: int) -> bool:
        """Check if opcode exists in repository."""
        return code in self.opcodes


# ============================================================================
# IN-MEMORY REPOSITORY (for testing)
# ============================================================================


class InMemoryOpcodeRepository:
    """Simple in-memory repository for testing."""

    def __init__(self, opcodes: Dict[int, OpcodeInfo] = None):
        """Initialize with optional opcode dictionary."""
        self.opcodes = opcodes or self._get_basic_opcodes()

    def _get_basic_opcodes(self) -> Dict[int, OpcodeInfo]:
        """Get basic opcodes for testing."""
        return {
            0x00: OpcodeInfo(0x00, "RETURN", OpcodeCategory.CONTROL_FLOW, "0 -> 0"),
            0x01: OpcodeInfo(
                0x01, "STORE_RETURN", OpcodeCategory.CONTROL_FLOW, "1 -> 0"
            ),
            0x02: OpcodeInfo(0x02, "JUMPTRUE", OpcodeCategory.CONTROL_FLOW, "1 -> 0"),
            0x03: OpcodeInfo(0x03, "JUMPFALSE", OpcodeCategory.CONTROL_FLOW, "1 -> 0"),
            0x04: OpcodeInfo(0x04, "JUMP", OpcodeCategory.CONTROL_FLOW, "0 -> 0"),
            0x10: OpcodeInfo(0x10, "DUP", OpcodeCategory.STACK, "1 -> 2"),
            0x11: OpcodeInfo(0x11, "POP", OpcodeCategory.STACK, "1 -> 0"),
            0x20: OpcodeInfo(0x20, "LOAD_LOCAL", OpcodeCategory.MEMORY, "0 -> 1"),
            0x21: OpcodeInfo(0x21, "STORE_LOCAL", OpcodeCategory.MEMORY, "1 -> 0"),
            0x30: OpcodeInfo(0x30, "ADD", OpcodeCategory.ARITHMETIC, "2 -> 1"),
            0x31: OpcodeInfo(0x31, "SUBTRACT", OpcodeCategory.ARITHMETIC, "2 -> 1"),
        }

    def get_opcode_info(self, code: int) -> Optional[OpcodeInfo]:
        """Get information about an opcode."""
        return self.opcodes.get(code)

    def has_opcode(self, code: int) -> bool:
        """Check if opcode exists in repository."""
        return code in self.opcodes
