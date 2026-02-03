"""PowerBuilder Opcode Definitions - Single source of truth.

This module consolidates ALL opcode definitions from multiple files into one.
No more duplication - this is the only opcodes file.
"""

from typing import Dict, Optional

# ============================================================================
# OPCODE DEFINITIONS
# ============================================================================

OPCODES: Dict[int, str] = {
    # Control flow
    0x00: "RETURN",
    0x01: "STORE_RETURN_VAL",
    0x02: "JUMPTRUE",
    0x03: "JUMPFALSE",
    0x04: "JUMP",
    0x12: "HALT",
    # Database operations
    0x05: "DBSTART",
    0x06: "DBCOMMIT",
    0x07: "DBROLLBACK",
    0x08: "DBSTOP",
    0x09: "DBCLOSE",
    0x0A: "DBOPEN",
    0x0B: "DBDELETE",
    0x0C: "DBUPDATE",
    0x0D: "DBEXECUTE",
    0x0E: "DBFETCH",
    0x0F: "DBINSERT",
    0x10: "DBSELECT",
    0x15: "DBEXECUTEDYN",
    0x16: "DBPREPARE",
    0x17: "DBOPENDYN",
    0x18: "DBEXECDYNPROC",
    0x19: "DBDESCRIBE",
    0x1A: "DBSELECTBLOB",
    0x1B: "DBUPDATEBLOB",
    0x1C: "DBSELECTCLOB",
    0x1D: "DBUPDATECLOB",
    # Stack operations - Variables
    0x1E: "PUSH_LOCAL_VAR",
    0x1F: "PUSH_SHARED_VAR",
    0x20: "PUSH_CONST_REF",
    0x21: "PUSH_THIS",
    0x22: "PUSH_PARENT",
    0x23: "PUSH_PRIMARY",
    0x2D: "PUSH_GLOBAL_VAR",
    0x2F: "PUSH_SHARED_VAR2",
    0x30: "PUSH_LOCAL_ARGREF",
    0x31: "PUSH_SHARED_GLOBREF",
    # Stack operations - Constants
    0x32: "PUSH_CONST_INT",
    0x33: "PUSH_CONST_UINT",
    0x34: "PUSH_CONST_LONG",
    0x35: "PUSH_CONST_ULONG",
    0x36: "PUSH_CONST_DEC",
    0x37: "PUSH_CONST_FLOAT",
    0x38: "PUSH_CONST_DOUBLE",
    0x39: "PUSH_CONST_TIME",
    0x3A: "PUSH_CONST_DATE",
    0x3B: "PUSH_CONST_STRING",
    0x3C: "PUSH_CONST_BOOL",
    0x3D: "PUSH_CONST_ENUM",
    # Logical operations
    0x24: "AND",
    0x25: "OR",
    0x26: "NOT",
    # Object operations
    0x11: "DESTROY",
    0x13: "EVENTCALL",
    0x14: "LVALUE_EXPR",
    0x27: "DOT",
    0x28: "INDEX",
    # Function calls
    0x29: "GLOBFUNCCALL",
    0x2A: "CALL_FUNCTION",
    0x2B: "DLLFUNCCALL",
    0x2C: "DOTFUNCCALL",
    # Array operations
    0x2E: "ARRAYLIST",
    0x7F: "ASSIGN_ARRAY",
    # Type conversions
    0x3E: "CNV_INT_TO_UINT",
    0x3F: "CNV_INT_TO_LONG",
    0x40: "CNV_INT_TO_ULONG",
    0x41: "CNV_INT_TO_DEC",
    0x42: "CNV_INT_TO_FLOAT",
    0x43: "CNV_INT_TO_DOUBLE",
    0x44: "CNV_UINT_TO_LONG",
    0x45: "CNV_UINT_TO_ULONG",
    0x46: "CNV_UINT_TO_DEC",
    0x47: "CNV_UINT_TO_FLOAT",
    0x48: "CNV_UINT_TO_DOUBLE",
    0x49: "CNV_LONG_TO_ULONG",
    0x4A: "CNV_LONG_TO_DEC",
    0x4B: "CNV_LONG_TO_FLOAT",
    0x4C: "CNV_LONG_TO_DOUBLE",
    0x4D: "CNV_ULONG_TO_DEC",
    0x4E: "CNV_ULONG_TO_FLOAT",
    0x4F: "CNV_ULONG_TO_DOUBLE",
    0x50: "CNV_DEC_TO_FLOAT",
    0x51: "CNV_DEC_TO_DOUBLE",
    0x52: "CNV_FLOAT_TO_DOUBLE",
    # Arithmetic operations - Addition
    0x53: "ADD_INT",
    0x54: "ADD_UINT",
    0x55: "ADD_LONG",
    0x56: "ADD_ULONG",
    0x57: "ADD_DEC",
    0x58: "ADD_FLOAT",
    0x59: "ADD_DOUBLE",
    0x7C: "ADD",
    # Arithmetic operations - Subtraction
    0x5A: "SUB_INT",
    0x5B: "SUB_UINT",
    0x5C: "SUB_LONG",
    0x5D: "SUB_ULONG",
    0x5E: "SUB",
    0x5F: "SUB_FLOAT",
    0x60: "SUB_DOUBLE",
    # Arithmetic operations - Multiplication
    0x61: "MULT_INT",
    0x62: "MULT_UINT",
    0x63: "MULT_LONG",
    0x64: "MULT_ULONG",
    0x65: "MULT_DEC",
    0x66: "MULT_FLOAT",
    0x67: "MULT_DOUBLE",
    # Arithmetic operations - Division
    0x68: "DIV_INT",
    0x69: "DIV_UINT",
    0x6A: "DIV_LONG",
    0x6B: "DIV_ULONG",
    0x6C: "DIV",
    0x6D: "DIV_FLOAT",
    0x6E: "DIV_DOUBLE",
    # Arithmetic operations - Power
    0x6F: "POWER_INT",
    0x70: "POWER_UINT",
    0x71: "POWER_LONG",
    0x72: "POWER_ULONG",
    0x73: "POWER_DEC",
    0x74: "POWER_FLOAT",
    0x75: "POWER_DOUBLE",
    # Arithmetic operations - Negation
    0x76: "NEGATE_INT",
    0x77: "NEGATE_UINT",
    0x78: "NEGATE_LONG",
    0x79: "NEGATE_ULONG",
    0x7A: "NEGATE_DEC",
    0x7B: "NEGATE_FLOAT",
    # String operations
    0x7D: "CAT_STRING",
    0x7E: "CAT_BINARY",
    # Assignment operations
    0x80: "ASSIGN_INT",
    0x81: "ASSIGN_UINT",
    0x82: "ASSIGN_LONG",
    0x83: "ASSIGN_ULONG",
    0x84: "ASSIGN_DEC",
    0x85: "ASSIGN_FLOAT",
    0x86: "ASSIGN_DOUBLE",
    0x87: "ASSIGN_STRING",
    0x88: "ASSIGN_BOOL",
    0x89: "ASSIGN_DATE",
    0x8A: "ASSIGN_TIME",
    0x8B: "ASSIGN_DATETIME",
    0x8C: "ASSIGN",
    # Comparison operations
    0x90: "EQ",
    0x91: "NE",
    0x92: "LT",
    0x93: "LE",
    0x94: "GT",
    0x95: "GE",
    # Extended opcodes (PowerBuilder 10+)
    0xA0: "TRY",
    0xA1: "CATCH",
    0xA2: "FINALLY",
    0xA3: "THROW",
    0xA4: "RETHROW",
    # Extended opcodes (PowerBuilder 11+)
    0xB0: "LAMBDA",
    0xB1: "CLOSURE",
    0xB2: "YIELD",
    0xB3: "ASYNC",
    0xB4: "AWAIT",
    # Extended opcodes (PowerBuilder 12+)
    0xC0: "NAMESPACE",
    0xC1: "USING",
    0xC2: "PARTIAL",
    0xC3: "EXTENSION",
    0xC4: "LINQ",
}


# ============================================================================
# OPCODE INFORMATION
# ============================================================================

# Opcode categories for easier classification
OPCODE_CATEGORIES = {
    "control_flow": [0x00, 0x01, 0x02, 0x03, 0x04, 0x12],
    "database": list(range(0x05, 0x1E)),
    "stack_push": list(range(0x1E, 0x3E)),
    "type_conversion": list(range(0x3E, 0x53)),
    "arithmetic": list(range(0x53, 0x7C)),
    "string": [0x7D, 0x7E],
    "assignment": list(range(0x7F, 0x8D)),
    "comparison": list(range(0x90, 0x96)),
    "exception": list(range(0xA0, 0xA5)),
    "advanced": list(range(0xB0, 0xC5)),
}

# Operand counts for each opcode (simplified)
OPCODE_OPERANDS = {
    # No operands
    "RETURN": 0,
    "HALT": 0,
    "AND": 0,
    "OR": 0,
    "NOT": 0,
    # Single operand
    "JUMP": 1,
    "JUMPTRUE": 1,
    "JUMPFALSE": 1,
    "PUSH_LOCAL_VAR": 1,
    "PUSH_GLOBAL_VAR": 1,
    "PUSH_CONST_INT": 1,
    "PUSH_CONST_STRING": 1,
    # Two operands
    "CALL_FUNCTION": 2,
    "GLOBFUNCCALL": 2,
    "DOTFUNCCALL": 2,
    # Variable operands
    "ARRAYLIST": -1,  # Variable count
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_opcode_name(opcode: int) -> Optional[str]:
    """Get the name of an opcode.

    Args:
        opcode: Opcode value

    Returns:
        Opcode name or None if unknown
    """
    return OPCODES.get(opcode)


def get_opcode_category(opcode: int) -> Optional[str]:
    """Get the category of an opcode.

    Args:
        opcode: Opcode value

    Returns:
        Category name or None
    """
    for category, opcodes in OPCODE_CATEGORIES.items():
        if opcode in opcodes:
            return category
    return None


def get_operand_count(opcode: int) -> int:
    """Get the expected operand count for an opcode.

    Args:
        opcode: Opcode value

    Returns:
        Operand count (-1 for variable)
    """
    opcode_name = get_opcode_name(opcode)
    if opcode_name:
        return OPCODE_OPERANDS.get(opcode_name, 0)
    return 0


def is_jump_opcode(opcode: int) -> bool:
    """Check if opcode is a jump instruction.

    Args:
        opcode: Opcode value

    Returns:
        True if jump instruction
    """
    opcode_name = get_opcode_name(opcode)
    return opcode_name and "JUMP" in opcode_name


def is_push_opcode(opcode: int) -> bool:
    """Check if opcode is a push instruction.

    Args:
        opcode: Opcode value

    Returns:
        True if push instruction
    """
    opcode_name = get_opcode_name(opcode)
    return opcode_name and opcode_name.startswith("PUSH")


def is_database_opcode(opcode: int) -> bool:
    """Check if opcode is a database operation.

    Args:
        opcode: Opcode value

    Returns:
        True if database operation
    """
    return get_opcode_category(opcode) == "database"
