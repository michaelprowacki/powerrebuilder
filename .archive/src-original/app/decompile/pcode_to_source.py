"""P-code to Source Decompilation Workflow.

Application layer workflow for decompiling P-code to PowerScript source.
Uses Parse Don't Validate pattern with factory functions.
Coordinates domain functions to transform P-code into decompiled objects.
"""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime

from src_new.shared.result import Result, Success, Error
from src_new.domain.powerbuilder.pcode import (
    PCodeInstruction,
    PCodeModule,
    Opcode,
    StackOperation,
    BranchOperation,
    CallOperation,
)
from src_new.domain.powerbuilder.decompiled import (
    DecompiledFunction,
    DecompiledWindow,
    BasicBlock,
    ControlFlowGraph,
    ControlFlowEdge,
    Loop,
    Statement,
    StatementBlock,
    ReturnStatement,
    CallStatement,
    Expression,
    BinaryExpression,
    LiteralExpression,
    VariableExpression,
    Parameter,
    LocalVariable,
    Symbol,
    SymbolTable,
    FunctionDecompiled,
    DecompilationFailed,
)


# ============================================================================
# PARSE DON'T VALIDATE - FACTORY FUNCTIONS
# ============================================================================


class _DecompileToken:
    """Hidden token for Parse Don't Validate pattern."""

    pass


def create_decompiled_function(p_code: PCodeModule) -> Result[DecompiledFunction, str]:
    """Create a validated decompiled function from P-code.

    This is the main entry point following Parse Don't Validate.
    Returns a Result type for railway-oriented programming.
    """
    # Validate P-code structure
    if not p_code.instructions:
        return Error("Empty P-code module")

    # Build control flow graph
    cfg_result = _build_control_flow_graph(p_code)
    if isinstance(cfg_result, Error):
        return cfg_result
    cfg = cfg_result.value

    # Extract symbol table
    symbols_result = _extract_symbols(p_code)
    if isinstance(symbols_result, Error):
        return symbols_result
    symbols = symbols_result.value

    # Reconstruct statements from basic blocks
    statements_result = _reconstruct_statements(cfg, symbols)
    if isinstance(statements_result, Error):
        return statements_result
    body = statements_result.value

    # Extract function metadata
    metadata_result = _extract_function_metadata(p_code, symbols)
    if isinstance(metadata_result, Error):
        return metadata_result
    name, params, return_type, locals = metadata_result.value

    # Create validated function with hidden token
    return Success(
        _create_function_internal(
            name=name,
            return_type=return_type,
            parameters=params,
            local_variables=locals,
            body=body,
            token=_DecompileToken(),
        )
    )


def _create_function_internal(
    name: str,
    return_type: Optional[str],
    parameters: List[Parameter],
    local_variables: List[LocalVariable],
    body: StatementBlock,
    token: _DecompileToken,
) -> DecompiledFunction:
    """Internal factory - requires token."""
    if not isinstance(token, _DecompileToken):
        raise ValueError("Invalid token")

    return DecompiledFunction(
        name=name,
        return_type=return_type,
        parameters=parameters,
        local_variables=local_variables,
        body=body,
    )


# ============================================================================
# CONTROL FLOW ANALYSIS
# ============================================================================


def _build_control_flow_graph(p_code: PCodeModule) -> Result[ControlFlowGraph, str]:
    """Build control flow graph from P-code instructions."""
    blocks: Dict[int, BasicBlock] = {}
    edges: List[ControlFlowEdge] = []

    # Identify basic block boundaries
    leaders = _find_block_leaders(p_code.instructions)

    # Build basic blocks
    current_block_id = 0
    current_statements: List[Statement] = []

    for i, instr in enumerate(p_code.instructions):
        if i in leaders:
            # Start new block
            if current_statements:
                blocks[current_block_id] = BasicBlock(
                    id=current_block_id,
                    statements=current_statements,
                    is_entry=(current_block_id == 0),
                )
                current_block_id += 1
                current_statements = []

        # Convert instruction to statement
        stmt_result = _instruction_to_statement(instr)
        if isinstance(stmt_result, Success):
            current_statements.append(stmt_result.value)

    # Add final block
    if current_statements:
        blocks[current_block_id] = BasicBlock(
            id=current_block_id, statements=current_statements, is_exit=True
        )

    # Build edges based on control flow
    for block_id, block in blocks.items():
        if block.statements:
            last_stmt = block.statements[-1]
            edges.extend(_get_control_flow_edges(block_id, last_stmt, blocks))

    # Find loops
    loops = _detect_loops(blocks, edges)

    return Success(
        ControlFlowGraph(
            entry_block=0,
            exit_blocks=[b.id for b in blocks.values() if b.is_exit],
            blocks=blocks,
            edges=edges,
            loops=loops,
        )
    )


def _find_block_leaders(instructions: List[PCodeInstruction]) -> set:
    """Find basic block leaders (first instruction of each block)."""
    leaders = {0}  # First instruction is always a leader

    for i, instr in enumerate(instructions):
        if instr.opcode in [Opcode.JUMP, Opcode.JUMP_IF_TRUE, Opcode.JUMP_IF_FALSE]:
            # Target of jump is a leader
            if isinstance(instr.operation, BranchOperation):
                target = instr.operation.target_offset
                if 0 <= target < len(instructions):
                    leaders.add(target)
            # Instruction after branch is a leader
            if i + 1 < len(instructions):
                leaders.add(i + 1)

    return leaders


def _instruction_to_statement(instr: PCodeInstruction) -> Result[Statement, str]:
    """Convert P-code instruction to statement."""
    if instr.opcode == Opcode.RETURN:
        return Success(ReturnStatement())

    elif instr.opcode in [Opcode.PUSH_CONSTANT, Opcode.PUSH_VARIABLE]:
        # Stack operations will be combined into expressions
        return Success(Statement())  # Placeholder

    elif instr.opcode == Opcode.CALL:
        if isinstance(instr.operation, CallOperation):
            return Success(
                CallStatement(
                    target=None,
                    function_name=instr.operation.function_name,
                    arguments=[],  # Will be filled from stack
                )
            )

    # Default placeholder
    return Success(Statement())


def _get_control_flow_edges(
    block_id: int, last_stmt: Statement, blocks: Dict[int, BasicBlock]
) -> List[ControlFlowEdge]:
    """Get control flow edges from a block based on its last statement."""
    edges = []

    # Default fall-through to next block
    next_block = block_id + 1
    if next_block in blocks:
        edges.append(
            ControlFlowEdge(
                source=block_id, target=next_block, edge_type="unconditional"
            )
        )

    return edges


def _detect_loops(
    blocks: Dict[int, BasicBlock], edges: List[ControlFlowEdge]
) -> List[Loop]:
    """Detect loops in control flow graph."""
    loops = []

    # Find back edges (edges that go to earlier blocks)
    for edge in edges:
        if edge.target < edge.source:
            # This is a back edge - indicates a loop
            loops.append(
                Loop(
                    header=edge.target,
                    back_edges=[edge],
                    body_blocks=list(range(edge.target, edge.source + 1)),
                    loop_type="while",  # Will refine based on pattern
                )
            )

    return loops


# ============================================================================
# SYMBOL EXTRACTION
# ============================================================================


def _extract_symbols(p_code: PCodeModule) -> Result[SymbolTable, str]:
    """Extract symbol table from P-code."""
    symbols: Dict[str, Symbol] = {}

    # Extract from metadata if available
    if hasattr(p_code, "metadata") and p_code.metadata:
        for var_name, var_type in p_code.metadata.get("variables", {}).items():
            symbols[var_name] = Symbol(
                name=var_name,
                symbol_type="variable",
                data_type=var_type,
                scope="local",
                references=[],
            )

    # Scan instructions for symbol usage
    for i, instr in enumerate(p_code.instructions):
        if instr.opcode == Opcode.PUSH_VARIABLE:
            if isinstance(instr.operation, StackOperation):
                var_name = str(instr.operation.value)
                if var_name not in symbols:
                    symbols[var_name] = Symbol(
                        name=var_name,
                        symbol_type="variable",
                        data_type=None,  # Unknown type
                        scope="local",
                        references=[i],
                    )
                else:
                    symbols[var_name].references.append(i)

    return Success(SymbolTable(symbols=symbols))


# ============================================================================
# STATEMENT RECONSTRUCTION
# ============================================================================


def _reconstruct_statements(
    cfg: ControlFlowGraph, symbols: SymbolTable
) -> Result[StatementBlock, str]:
    """Reconstruct high-level statements from control flow graph."""
    statements = []

    # Process blocks in order (simplified for now)
    for block_id in sorted(cfg.blocks.keys()):
        block = cfg.blocks[block_id]
        statements.extend(block.statements)

    return Success(StatementBlock(statements=statements))


# ============================================================================
# METADATA EXTRACTION
# ============================================================================


def _extract_function_metadata(
    p_code: PCodeModule, symbols: SymbolTable
) -> Result[Tuple[str, List[Parameter], Optional[str], List[LocalVariable]], str]:
    """Extract function metadata from P-code and symbols."""
    # Extract function name (from module name or metadata)
    name = p_code.name if hasattr(p_code, "name") else "unnamed_function"

    # Extract parameters (simplified - would need more analysis)
    params: List[Parameter] = []

    # Extract return type (from metadata or analysis)
    return_type = None
    if hasattr(p_code, "metadata") and p_code.metadata:
        return_type = p_code.metadata.get("return_type")

    # Extract local variables from symbol table
    locals: List[LocalVariable] = []
    for symbol in symbols.symbols.values():
        if symbol.symbol_type == "variable" and symbol.scope == "local":
            locals.append(
                LocalVariable(
                    name=symbol.name,
                    data_type=symbol.data_type or "any",
                    initial_value=None,
                )
            )

    return Success((name, params, return_type, locals))


# ============================================================================
# WINDOW DECOMPILATION
# ============================================================================


def create_decompiled_window(
    p_code: PCodeModule, window_data: Dict[str, Any]
) -> Result[DecompiledWindow, str]:
    """Create a validated decompiled window.

    Parse Don't Validate entry point for windows.
    """
    # Validate window data
    if not window_data.get("name"):
        return Error("Window must have a name")

    # Extract controls
    controls = []
    for control_data in window_data.get("controls", []):
        control_result = _create_control(control_data)
        if isinstance(control_result, Error):
            return control_result
        controls.append(control_result.value)

    # Extract events
    events = []
    for event_data in window_data.get("events", []):
        event_result = _create_event(event_data, p_code)
        if isinstance(event_result, Error):
            return event_result
        events.append(event_result.value)

    # Extract functions
    functions = []
    for func_data in window_data.get("functions", []):
        func_result = create_decompiled_function(func_data)
        if isinstance(func_result, Error):
            return func_result
        functions.append(func_result.value)

    return Success(
        DecompiledWindow(
            name=window_data["name"],
            title=window_data.get("title", ""),
            controls=controls,
            events=events,
            functions=functions,
            instance_variables=[],
            properties=window_data.get("properties", {}),
        )
    )


def _create_control(control_data: Dict[str, Any]) -> Result[Any, str]:
    """Create a decompiled control."""
    # Simplified control creation
    from src_new.domain.powerbuilder.decompiled import DecompiledControl

    return Success(
        DecompiledControl(
            name=control_data.get("name", "unnamed"),
            control_type=control_data.get("type", "unknown"),
            properties=control_data.get("properties", {}),
            events=[],
        )
    )


def _create_event(event_data: Dict[str, Any], p_code: PCodeModule) -> Result[Any, str]:
    """Create a decompiled event."""
    from src_new.domain.powerbuilder.decompiled import DecompiledEvent

    # Decompile event body if P-code provided
    body = StatementBlock(statements=[])
    if p_code and p_code.instructions:
        statements_result = _reconstruct_statements(
            _build_control_flow_graph(p_code).value, _extract_symbols(p_code).value
        )
        if isinstance(statements_result, Success):
            body = statements_result.value

    return Success(
        DecompiledEvent(
            name=event_data.get("name", "unnamed"), parameters=[], body=body
        )
    )


# ============================================================================
# EXPRESSION RECONSTRUCTION
# ============================================================================


def reconstruct_expression(
    stack: List[Any], instruction: PCodeInstruction
) -> Result[Expression, str]:
    """Reconstruct expression from stack and instruction.

    Parse Don't Validate for expressions.
    """
    if instruction.opcode == Opcode.ADD:
        if len(stack) < 2:
            return Error("Not enough operands for ADD")
        right = stack.pop()
        left = stack.pop()
        return Success(BinaryExpression(left=left, operator="+", right=right))

    elif instruction.opcode == Opcode.PUSH_CONSTANT:
        if isinstance(instruction.operation, StackOperation):
            return Success(
                LiteralExpression(
                    value=instruction.operation.value,
                    literal_type=_infer_literal_type(instruction.operation.value),
                )
            )

    elif instruction.opcode == Opcode.PUSH_VARIABLE:
        if isinstance(instruction.operation, StackOperation):
            return Success(VariableExpression(name=str(instruction.operation.value)))

    return Error(f"Unknown instruction for expression: {instruction.opcode}")


def _infer_literal_type(value: Any) -> str:
    """Infer literal type from value."""
    if isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int):
        return "integer"
    elif isinstance(value, float):
        return "decimal"
    elif isinstance(value, str):
        return "string"
    elif value is None:
        return "null"
    return "unknown"


# ============================================================================
# EVENT GENERATION
# ============================================================================


def emit_function_decompiled(
    function: DecompiledFunction,
    p_code_size: int,
    instruction_count: int,
    decompilation_time: float,
) -> FunctionDecompiled:
    """Emit function decompiled event."""
    return FunctionDecompiled(
        function=function,
        p_code_size=p_code_size,
        instruction_count=instruction_count,
        decompilation_time=decompilation_time,
        timestamp=datetime.now(),
    )


def emit_decompilation_failed(
    object_name: str,
    object_type: str,
    error_message: str,
    p_code_offset: Optional[int] = None,
) -> DecompilationFailed:
    """Emit decompilation failed event."""
    return DecompilationFailed(
        object_name=object_name,
        object_type=object_type,
        error_message=error_message,
        p_code_offset=p_code_offset,
        timestamp=datetime.now(),
    )
