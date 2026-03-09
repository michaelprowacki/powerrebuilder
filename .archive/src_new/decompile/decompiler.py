"""Decompile Feature - P-code to PowerBuilder source decompilation.

This module handles decompilation of P-code bytecode to PowerBuilder source code.
Consolidates the decompilation logic into a clean, maintainable implementation.
"""

import logging
from pathlib import Path
from typing import List, Optional

from src_new._core import (
    PCodeInstruction,
)
from src_new._patterns import (
    BaseCoordinator,
    BaseTransformer,
    BinaryReader,
    FileHandler,
)
from .opcodes import get_opcode_name

logger = logging.getLogger(__name__)


# ============================================================================
# P-CODE DECODER
# ============================================================================


class PCodeDecoder:
    """Decoder for PowerBuilder P-code bytecode."""

    def __init__(self, version: str = "PB12.5"):
        """Initialize decoder.

        Args:
            version: PowerBuilder version
        """
        self.version = version
        self.reader = None

    def decode(self, bytecode: bytes) -> List[PCodeInstruction]:
        """Decode P-code bytecode to instructions.

        Args:
            bytecode: P-code bytes

        Returns:
            List of decoded instructions
        """
        instructions = []
        self.reader = BinaryReader(data=bytecode)

        while self.reader.remaining > 0:
            try:
                instruction = self._decode_instruction()
                if instruction:
                    instructions.append(instruction)
            except Exception as e:
                logger.debug(
                    f"Failed to decode instruction at {self.reader.offset}: {e}"
                )
                # Skip bad byte and continue
                self.reader.seek(1, whence=1)

        return instructions

    def _decode_instruction(self) -> Optional[PCodeInstruction]:
        """Decode a single instruction.

        Returns:
            Decoded instruction or None
        """
        offset = self.reader.offset

        # Read opcode
        opcode = self.reader.read_uint8()

        # Get opcode info
        opcode_name = get_opcode_name(opcode)
        if not opcode_name:
            logger.debug(f"Unknown opcode: 0x{opcode:02X}")
            return None

        # Decode operands based on opcode
        operands = self._decode_operands(opcode, opcode_name)

        return PCodeInstruction(
            opcode=opcode,
            operands=operands,
            offset=offset,
            size=self.reader.offset - offset,
        )

    def _decode_operands(self, opcode: int, opcode_name: str) -> List:
        """Decode instruction operands.

        Args:
            opcode: Opcode value
            opcode_name: Opcode name

        Returns:
            List of operands
        """
        operands = []

        # Operand decoding based on opcode type
        if "PUSH_CONST" in opcode_name:
            operands.append(self._decode_constant(opcode_name))

        elif "PUSH" in opcode_name or "STORE" in opcode_name:
            # Variable reference
            operands.append(self.reader.read_uint16())

        elif "JUMP" in opcode_name:
            # Jump offset
            operands.append(self.reader.read_int16())

        elif "CALL" in opcode_name:
            # Function call
            operands.append(self.reader.read_uint16())  # Function ID
            operands.append(self.reader.read_uint8())  # Arg count

        elif opcode_name in ["ADD", "SUB", "MULT", "DIV", "POWER"]:
            # Binary operation - no additional operands
            pass

        elif opcode_name in ["AND", "OR", "NOT"]:
            # Logical operation - no additional operands
            pass

        elif opcode_name.startswith("CNV_"):
            # Type conversion - no additional operands
            pass

        elif opcode_name.startswith("DB"):
            # Database operation
            if opcode_name in ["DBOPEN", "DBEXECUTE", "DBFETCH"]:
                operands.append(self.reader.read_uint16())  # Statement ID

        return operands

    def _decode_constant(self, opcode_name: str) -> any:
        """Decode constant value based on type.

        Args:
            opcode_name: Name indicating constant type

        Returns:
            Decoded constant value
        """
        if "INT" in opcode_name:
            if "UINT" in opcode_name:
                return self.reader.read_uint32()
            else:
                return self.reader.read_int32()

        elif "LONG" in opcode_name:
            if "ULONG" in opcode_name:
                return self.reader.read_uint64()
            else:
                return self.reader.read_int64()

        elif "FLOAT" in opcode_name:
            return self.reader.read_float()

        elif "DOUBLE" in opcode_name:
            return self.reader.read_double()

        elif "STRING" in opcode_name:
            # Read string length and data
            length = self.reader.read_uint16()
            return self.reader.read_string(length)

        elif "BOOL" in opcode_name:
            return self.reader.read_uint8() != 0

        else:
            # Default to uint32
            return self.reader.read_uint32()


# ============================================================================
# DECOMPILATION TRANSFORMER
# ============================================================================


class DecompilationTransformer(BaseTransformer[List[PCodeInstruction], str]):
    """Transform P-code instructions to PowerBuilder source."""

    def __init__(self):
        """Initialize transformer."""
        self.indent_level = 0
        self.output = []
        self.locals = []
        self.stack = []

    def transform(self, instructions: List[PCodeInstruction]) -> str:
        """Transform instructions to source code.

        Args:
            instructions: P-code instructions

        Returns:
            Decompiled source code
        """
        self.output = []
        self.stack = []

        for inst in instructions:
            self._process_instruction(inst)

        return "\n".join(self.output)

    def _process_instruction(self, inst: PCodeInstruction) -> None:
        """Process a single instruction.

        Args:
            inst: Instruction to process
        """
        opcode_name = get_opcode_name(inst.opcode)

        # Handle different instruction types
        if opcode_name == "RETURN":
            self._emit("return")

        elif opcode_name.startswith("PUSH_CONST"):
            self.stack.append(self._format_constant(inst.operands[0]))

        elif opcode_name.startswith("PUSH"):
            var_id = inst.operands[0] if inst.operands else 0
            self.stack.append(f"var_{var_id}")

        elif opcode_name in ["ADD", "SUB", "MULT", "DIV"]:
            self._process_binary_op(opcode_name.lower())

        elif opcode_name in ["AND", "OR"]:
            self._process_logical_op(opcode_name.lower())

        elif opcode_name == "NOT":
            if self.stack:
                val = self.stack.pop()
                self.stack.append(f"not {val}")

        elif opcode_name.startswith("ASSIGN"):
            self._process_assignment(inst)

        elif opcode_name.startswith("JUMP"):
            self._process_jump(opcode_name, inst)

        elif opcode_name.startswith("CALL"):
            self._process_call(inst)

        elif opcode_name.startswith("DB"):
            self._process_database_op(opcode_name, inst)

    def _process_binary_op(self, op: str) -> None:
        """Process binary operation.

        Args:
            op: Operation name
        """
        if len(self.stack) >= 2:
            right = self.stack.pop()
            left = self.stack.pop()

            # Map operation
            op_map = {
                "add": "+",
                "sub": "-",
                "mult": "*",
                "div": "/",
                "power": "^",
            }

            op_symbol = op_map.get(op, op)
            self.stack.append(f"({left} {op_symbol} {right})")

    def _process_logical_op(self, op: str) -> None:
        """Process logical operation.

        Args:
            op: Operation name
        """
        if len(self.stack) >= 2:
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(f"({left} {op} {right})")

    def _process_assignment(self, inst: PCodeInstruction) -> None:
        """Process assignment instruction.

        Args:
            inst: Assignment instruction
        """
        if self.stack:
            value = self.stack.pop()
            if inst.operands:
                var_id = inst.operands[0]
                self._emit(f"var_{var_id} = {value}")
            else:
                self._emit(f"result = {value}")

    def _process_jump(self, opcode_name: str, inst: PCodeInstruction) -> None:
        """Process jump instruction.

        Args:
            opcode_name: Jump opcode name
            inst: Jump instruction
        """
        if inst.operands:
            offset = inst.operands[0]

            if opcode_name == "JUMPTRUE":
                if self.stack:
                    condition = self.stack.pop()
                    self._emit(f"if {condition} then")
                    self.indent_level += 1

            elif opcode_name == "JUMPFALSE":
                if self.stack:
                    condition = self.stack.pop()
                    self._emit(f"if not {condition} then")
                    self.indent_level += 1

            elif opcode_name == "JUMP":
                if self.indent_level > 0:
                    self.indent_level -= 1
                    self._emit("end if")

    def _process_call(self, inst: PCodeInstruction) -> None:
        """Process function call.

        Args:
            inst: Call instruction
        """
        if inst.operands:
            func_id = inst.operands[0]
            arg_count = inst.operands[1] if len(inst.operands) > 1 else 0

            # Pop arguments from stack
            args = []
            for _ in range(arg_count):
                if self.stack:
                    args.insert(0, self.stack.pop())

            # Format call
            call_str = f"func_{func_id}({', '.join(args)})"
            self.stack.append(call_str)

    def _process_database_op(self, opcode_name: str, inst: PCodeInstruction) -> None:
        """Process database operation.

        Args:
            opcode_name: Database opcode name
            inst: Database instruction
        """
        db_ops = {
            "DBOPEN": "OPEN",
            "DBCLOSE": "CLOSE",
            "DBFETCH": "FETCH",
            "DBEXECUTE": "EXECUTE",
            "DBCOMMIT": "COMMIT",
            "DBROLLBACK": "ROLLBACK",
        }

        if opcode_name in db_ops:
            op = db_ops[opcode_name]
            if inst.operands:
                self._emit(f"{op} cursor_{inst.operands[0]}")
            else:
                self._emit(op)

    def _format_constant(self, value: any) -> str:
        """Format constant value.

        Args:
            value: Constant value

        Returns:
            Formatted string
        """
        if isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, bool):
            return "true" if value else "false"
        else:
            return str(value)

    def _emit(self, line: str) -> None:
        """Emit a line of code.

        Args:
            line: Line to emit
        """
        indent = "    " * self.indent_level
        self.output.append(f"{indent}{line}")


# ============================================================================
# DECOMPILE COORDINATOR
# ============================================================================


class DecompileCoordinator(BaseCoordinator):
    """Coordinator for decompilation stage.

    Decompiles P-code bytecode to PowerBuilder source code.
    """

    @property
    def stage_name(self) -> str:
        """Get stage name."""
        return "decompile"

    def discover_files(self) -> List[Path]:
        """Discover P-code files to process.

        Returns:
            List of P-code files
        """
        if self.input_path.is_file():
            # Single file
            if self.input_path.suffix.lower() == ".fun":
                return [self.input_path]
            else:
                raise ValueError(f"Not a P-code file: {self.input_path}")
        else:
            # Directory - find all P-code files
            return list(self.input_path.rglob("*.fun"))

    def process_file(self, input_file: Path, output_dir: Path) -> bool:
        """Process a single P-code file.

        Args:
            input_file: P-code file path
            output_dir: Output directory

        Returns:
            True if successful
        """
        try:
            self.logger.info(f"Decompiling: {input_file}")

            # Read P-code
            file_handler = FileHandler()
            bytecode = file_handler.read_binary(input_file)

            # Detect version
            version = self._detect_version(bytecode)
            self.logger.debug(f"Detected version: {version}")

            # Decode to instructions
            decoder = PCodeDecoder(version)
            instructions = decoder.decode(bytecode)
            self.logger.debug(f"Decoded {len(instructions)} instructions")

            # Transform to source code
            transformer = DecompilationTransformer()
            source = transformer.transform(instructions)

            # Determine output file
            output_file = output_dir / input_file.stem
            output_file = output_file.with_suffix(".sru")  # Default to user object

            # Write decompiled source
            file_handler.write_text(output_file, source)

            self.logger.info(f"Decompiled to: {output_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to decompile {input_file}: {e}")
            return False

    def _detect_version(self, bytecode: bytes) -> str:
        """Detect PowerBuilder version from bytecode.

        Args:
            bytecode: P-code bytes

        Returns:
            Version string
        """
        # Simple heuristic-based detection
        if len(bytecode) < 16:
            return "Unknown"

        # Check for version markers
        # Real implementation would use more sophisticated detection
        header = bytecode[:16]

        if b"PB12" in header or b"\x0c" in header[:4]:
            return "PB12.5"
        elif b"PB11" in header or b"\x0b" in header[:4]:
            return "PB11"
        elif b"PB10" in header or b"\x0a" in header[:4]:
            return "PB10"
        else:
            return "PB9"
