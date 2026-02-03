"""PowerBuilder Decompiled Domain Types.

Pure data types representing decompiled PowerBuilder constructs.
These are the WHAT - no operations, just data models.
Events are colocated with their aggregates following Scott Wlaschin's FDM principles.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ============================================================================
# DECOMPILED OBJECT TYPES
# ============================================================================


@dataclass(frozen=True)
class DecompiledFunction:
    """A decompiled PowerBuilder function."""

    name: str
    return_type: Optional[str]
    parameters: List["Parameter"]
    local_variables: List["LocalVariable"]
    body: "StatementBlock"
    is_global: bool = False
    is_static: bool = False
    access_modifier: str = "public"
    throws: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DecompiledWindow:
    """A decompiled PowerBuilder window."""

    name: str
    title: str
    controls: List["DecompiledControl"]
    events: List["DecompiledEvent"]
    functions: List[DecompiledFunction]
    instance_variables: List["InstanceVariable"]
    properties: Dict[str, Any] = field(default_factory=dict)
    menu: Optional[str] = None
    parent_window: Optional[str] = None


@dataclass(frozen=True)
class DecompiledDataWindow:
    """A decompiled PowerBuilder DataWindow."""

    name: str
    data_source: "DataSource"
    columns: List["DataWindowColumn"]
    computed_fields: List["ComputedField"]
    groups: List["DataWindowGroup"]
    sort_criteria: List["SortCriterion"]
    filters: List["FilterExpression"]
    presentation_style: str = "grid"
    processing: str = "0"  # 0=Form, 1=Tabular, etc.


@dataclass(frozen=True)
class DecompiledUserObject:
    """A decompiled PowerBuilder user object."""

    name: str
    base_class: Optional[str]
    functions: List[DecompiledFunction]
    events: List["DecompiledEvent"]
    instance_variables: List["InstanceVariable"]
    properties: Dict[str, Any] = field(default_factory=dict)
    is_visual: bool = False
    is_standard: bool = False
    is_custom: bool = True


@dataclass(frozen=True)
class DecompiledMenu:
    """A decompiled PowerBuilder menu."""

    name: str
    items: List["MenuItem"]
    toolbar_items: List["ToolbarItem"]
    properties: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# CONTROL FLOW TYPES
# ============================================================================


@dataclass(frozen=True)
class BasicBlock:
    """A basic block in control flow graph."""

    id: int
    statements: List["Statement"]
    predecessors: List[int] = field(default_factory=list)
    successors: List[int] = field(default_factory=list)
    is_entry: bool = False
    is_exit: bool = False
    loop_header: bool = False
    loop_depth: int = 0


@dataclass(frozen=True)
class ControlFlowGraph:
    """Control flow graph for a function."""

    entry_block: int
    exit_blocks: List[int]
    blocks: Dict[int, BasicBlock]
    edges: List["ControlFlowEdge"]
    dominators: Dict[int, int] = field(default_factory=dict)
    loops: List["Loop"] = field(default_factory=list)


@dataclass(frozen=True)
class ControlFlowEdge:
    """An edge in control flow graph."""

    source: int
    target: int
    edge_type: str  # "conditional", "unconditional", "exception"
    condition: Optional["Expression"] = None


@dataclass(frozen=True)
class Loop:
    """A loop in control flow."""

    header: int
    back_edges: List[ControlFlowEdge]
    body_blocks: List[int]
    loop_type: str  # "for", "while", "do-while"
    nesting_level: int = 0


# ============================================================================
# STATEMENT TYPES
# ============================================================================


@dataclass(frozen=True)
class Statement:
    """Base statement type."""

    line_number: Optional[int] = None
    source_text: Optional[str] = None


@dataclass(frozen=True)
class StatementBlock(Statement):
    """A block of statements."""

    statements: List[Statement]


@dataclass(frozen=True)
class AssignmentStatement(Statement):
    """Assignment statement."""

    target: "Expression"
    value: "Expression"


@dataclass(frozen=True)
class IfStatement(Statement):
    """If-then-else statement."""

    condition: "Expression"
    then_branch: Statement
    else_branch: Optional[Statement] = None


@dataclass(frozen=True)
class WhileStatement(Statement):
    """While loop statement."""

    condition: "Expression"
    body: Statement


@dataclass(frozen=True)
class ForStatement(Statement):
    """For loop statement."""

    variable: str
    start_value: "Expression"
    end_value: "Expression"
    step: Optional["Expression"] = None
    body: Statement


@dataclass(frozen=True)
class ReturnStatement(Statement):
    """Return statement."""

    value: Optional["Expression"] = None


@dataclass(frozen=True)
class CallStatement(Statement):
    """Function/method call statement."""

    target: Optional["Expression"]  # None for global functions
    function_name: str
    arguments: List["Expression"]


@dataclass(frozen=True)
class TryStatement(Statement):
    """Try-catch statement."""

    try_block: Statement
    catch_blocks: List["CatchBlock"]
    finally_block: Optional[Statement] = None


@dataclass(frozen=True)
class CatchBlock:
    """Catch block in try statement."""

    exception_type: str
    variable: Optional[str]
    body: Statement


# ============================================================================
# EXPRESSION TYPES
# ============================================================================


@dataclass(frozen=True)
class Expression:
    """Base expression type."""

    expression_type: Optional[str] = None  # Inferred type


@dataclass(frozen=True)
class BinaryExpression(Expression):
    """Binary expression (a op b)."""

    left: Expression
    operator: str  # "+", "-", "*", "/", "=", "<", ">", "AND", "OR", etc.
    right: Expression


@dataclass(frozen=True)
class UnaryExpression(Expression):
    """Unary expression (op a)."""

    operator: str  # "-", "NOT", "++", "--"
    operand: Expression


@dataclass(frozen=True)
class LiteralExpression(Expression):
    """Literal value."""

    value: Any
    literal_type: str  # "string", "integer", "decimal", "boolean", "null"


@dataclass(frozen=True)
class VariableExpression(Expression):
    """Variable reference."""

    name: str
    scope: str = "local"  # "local", "instance", "global", "shared"


@dataclass(frozen=True)
class MemberExpression(Expression):
    """Member access (a.b)."""

    object: Expression
    member: str


@dataclass(frozen=True)
class IndexExpression(Expression):
    """Array/list index (a[i])."""

    object: Expression
    index: Expression


@dataclass(frozen=True)
class CallExpression(Expression):
    """Function call expression."""

    target: Optional[Expression]  # None for global functions
    function_name: str
    arguments: List[Expression]


@dataclass(frozen=True)
class NewExpression(Expression):
    """Object creation (CREATE)."""

    class_name: str
    arguments: List[Expression] = field(default_factory=list)


@dataclass(frozen=True)
class CastExpression(Expression):
    """Type cast expression."""

    expression: Expression
    target_type: str


# ============================================================================
# SUPPORTING TYPES
# ============================================================================


@dataclass(frozen=True)
class Parameter:
    """Function parameter."""

    name: str
    data_type: str
    pass_by: str = "value"  # "value", "reference"
    default_value: Optional[Expression] = None


@dataclass(frozen=True)
class LocalVariable:
    """Local variable declaration."""

    name: str
    data_type: str
    initial_value: Optional[Expression] = None
    is_constant: bool = False


@dataclass(frozen=True)
class InstanceVariable:
    """Instance variable."""

    name: str
    data_type: str
    access_modifier: str = "private"
    initial_value: Optional[Expression] = None
    is_static: bool = False
    is_constant: bool = False


@dataclass(frozen=True)
class DecompiledEvent:
    """A decompiled event handler."""

    name: str
    parameters: List[Parameter]
    body: StatementBlock
    is_extended: bool = False  # Extends parent event
    is_override: bool = False  # Overrides parent event


@dataclass(frozen=True)
class DecompiledControl:
    """A decompiled window control."""

    name: str
    control_type: str  # "commandbutton", "singlelineedit", etc.
    properties: Dict[str, Any]
    events: List[DecompiledEvent]
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    tab_order: int = 0


@dataclass(frozen=True)
class MenuItem:
    """A menu item."""

    name: str
    text: str
    shortcut: Optional[str] = None
    enabled: bool = True
    checked: bool = False
    children: List["MenuItem"] = field(default_factory=list)
    click_event: Optional[DecompiledEvent] = None


@dataclass(frozen=True)
class ToolbarItem:
    """A toolbar item."""

    name: str
    text: str
    tooltip: str
    icon: Optional[str] = None
    enabled: bool = True
    visible: bool = True
    click_event: Optional[DecompiledEvent] = None


# ============================================================================
# DATAWINDOW TYPES
# ============================================================================


@dataclass(frozen=True)
class DataSource:
    """DataWindow data source."""

    source_type: str  # "sql", "stored_procedure", "external"
    sql_statement: Optional[str] = None
    stored_procedure: Optional[str] = None
    arguments: List[Parameter] = field(default_factory=list)


@dataclass(frozen=True)
class DataWindowColumn:
    """DataWindow column."""

    name: str
    data_type: str
    db_column: str
    display_format: Optional[str] = None
    edit_mask: Optional[str] = None
    validation: Optional[str] = None
    initial_value: Optional[str] = None


@dataclass(frozen=True)
class ComputedField:
    """DataWindow computed field."""

    name: str
    expression: str
    data_type: str
    display_format: Optional[str] = None


@dataclass(frozen=True)
class DataWindowGroup:
    """DataWindow grouping."""

    level: int
    columns: List[str]
    sort_order: str = "ascending"
    new_page: bool = False


@dataclass(frozen=True)
class SortCriterion:
    """DataWindow sort criterion."""

    column: str
    order: str = "ascending"


@dataclass(frozen=True)
class FilterExpression:
    """DataWindow filter."""

    expression: str
    apply_on_retrieve: bool = True


# ============================================================================
# SYMBOL TABLE
# ============================================================================


@dataclass(frozen=True)
class Symbol:
    """Symbol table entry."""

    name: str
    symbol_type: str  # "variable", "function", "class", "constant"
    data_type: Optional[str]
    scope: str  # "local", "instance", "global", "shared"
    declaration_line: Optional[int] = None
    references: List[int] = field(default_factory=list)  # Line numbers


@dataclass(frozen=True)
class SymbolTable:
    """Symbol table for scope management."""

    symbols: Dict[str, Symbol]
    parent: Optional["SymbolTable"] = None
    scope_name: str = "global"


# ============================================================================
# DOMAIN EVENTS (Colocated with Decompiled aggregate)
# ============================================================================


@dataclass(frozen=True)
class FunctionDecompiled:
    """Event: Function was decompiled from P-code."""

    function: DecompiledFunction
    p_code_size: int
    instruction_count: int
    decompilation_time: float
    timestamp: datetime


@dataclass(frozen=True)
class WindowDecompiled:
    """Event: Window was decompiled."""

    window: DecompiledWindow
    control_count: int
    event_count: int
    timestamp: datetime


@dataclass(frozen=True)
class DataWindowDecompiled:
    """Event: DataWindow was decompiled."""

    datawindow: DecompiledDataWindow
    column_count: int
    has_sql: bool
    timestamp: datetime


@dataclass(frozen=True)
class ControlFlowAnalyzed:
    """Event: Control flow was analyzed."""

    function_name: str
    cfg: ControlFlowGraph
    block_count: int
    edge_count: int
    cyclomatic_complexity: int
    timestamp: datetime


@dataclass(frozen=True)
class ExpressionReconstructed:
    """Event: Expression was reconstructed from P-code."""

    expression: Expression
    p_code_offset: int
    stack_depth: int
    timestamp: datetime


@dataclass(frozen=True)
class DecompilationFailed:
    """Event: Decompilation failed."""

    object_name: str
    object_type: str
    error_message: str
    p_code_offset: Optional[int]
    timestamp: datetime
