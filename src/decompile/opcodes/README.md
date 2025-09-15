# PowerBuilder Opcode Tables

This directory contains the consolidated PowerBuilder opcode definitions for all versions.

## Structure

- **opcodes.py** - Single comprehensive module containing:
  - All 583 PowerBuilder opcodes (0x00-0x246)
  - Version-specific filtering and ranges
  - Unknown opcode variants tracking
  - OpcodeManager class for version handling
  - Helper functions for opcode lookup
- **pb6_0_reference.txt** - Historical documentation of PB 6.0 opcodes (0x00-0xFF)

## Opcode Format

All opcodes use the format:
```python
opcode_value: (mnemonic, operand_byte_count, operand_hint)
```

Where:
- `opcode_value`: Integer opcode byte value (0x00-0x246)
- `mnemonic`: String name of the operation (e.g., "PUSH_CONST_INT")
- `operand_byte_count`: Number of operand bytes following the opcode
- `operand_hint`: Interpretation hint for operands (e.g., "uint16le", "var_index") or None

## Usage

```python
from decompile.opcodes import OpcodeManager, get_opcode_info, find_opcode_by_name
from extract.pbd_core.version_detector import PowerBuilderVersion

# Get opcode table for specific version
version = PowerBuilderVersion(10, 5, True)
opcode_table = OpcodeManager.get_opcode_table(version)

# Look up an opcode
opcode_info = get_opcode_info(0x32)  # ("PUSH_CONST_INT", 2, "uint16le")

# Find opcode by name
opcode = find_opcode_by_name("PUSH_CONST_INT")  # 0x32

# Get version-specific opcodes
pb6_opcodes = get_opcodes_for_version("pb6_0")  # 256 opcodes
pb8_opcodes = get_opcodes_for_version("pb8_0")  # 583 opcodes
```

## Version Support

The consolidated table handles all versions with appropriate filtering:

| Version | Opcode Range | Notes |
|---------|--------------|-------|
| PB 6.0  | 0x00-0xFF (256) | Basic opcodes only |
| PB 7.0  | 0x00-0xFF (256) | Same as 6.0 |
| PB 8.0  | 0x00-0x246 (583) | Added LongLong, Byte types |
| PB 9.0+ | 0x00-0x246 (583) | Same as 8.0 |
| PB 10.5 | 0x00-0x246 (583) | Same as 8.0 (Unicode at data level) |

## Unknown Opcodes

Some opcodes have variants that are not fully documented. These are tracked within
the main module and can be accessed via:
- `has_variants(opcode)` - Check if an opcode has variants
- `get_variant_info(opcode, variant)` - Get variant-specific information
