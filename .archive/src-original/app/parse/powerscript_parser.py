"""Parse Domain - PowerScript Source Parsing.

Pure functions for parsing PowerScript (PowerBuilder's programming language) to AST.
Follows Scott Wlaschin's functional domain modeling with PowerBuilder terminology.

Domain-driven design:
- Uses PowerBuilder terminology (PowerScript, DataWindow, Window, Event)
- All functions return Result types for railway-oriented programming
- No I/O operations - pure transformations
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple, Optional, Union, Any

from src_new._core.result import Result, Success, Failure


# ============================================================================
# PARSE DOMAIN TYPES (Self-contained - no shared.py!)
# ============================================================================

class PowerScriptNodeType(str, Enum):
    """PowerScript AST node types."""
    # PowerBuilder Objects
    WINDOW = "WINDOW"           # Window object
    DATAWINDOW = "DATAWINDOW"   # DataWindow object
    USER_OBJECT = "USER_OBJECT" # User Object
    MENU = "MENU"               # Menu object
    APPLICATION = "APPLICATION" # Application object

    # PowerScript Elements
    FUNCTION = "FUNCTION"       # PowerScript function
    EVENT = "EVENT"            # PowerScript event handler
    PROPERTY = "PROPERTY"       # Object property
    INSTANCE_VAR = "INSTANCE_VARIABLE" # Instance variable

    # PowerScript Statements
    SCRIPT_BLOCK = "SCRIPT_BLOCK"
    IF_STATEMENT = "IF"
    CHOOSE_CASE = "CHOOSE_CASE" # PowerScript's switch statement
    DO_LOOP = "DO_LOOP"         # PowerScript DO...LOOP
    FOR_LOOP = "FOR"
    RETURN_STATEMENT = "RETURN"
    ASSIGNMENT = "ASSIGNMENT"
    TRY_CATCH = "TRY_CATCH"     # PowerScript exception handling

    # Expressions
    BINARY_OP = "BINARY_OP"
    UNARY_OP = "UNARY_OP"
    CALL = "CALL"
    IDENTIFIER = "IDENTIFIER"
    LITERAL = "LITERAL"

    # Types
    TYPE = "TYPE"
    ARRAY_TYPE = "ARRAY_TYPE"

    # DataWindow Elements (PowerBuilder's unique technology)
    DW_SQL = "DW_SQL"              # DataWindow SQL
    DW_COLUMN = "DW_COLUMN"        # DataWindow column
    DW_COMPUTE = "DW_COMPUTE"      # Computed field
    DW_BAND = "DW_BAND"            # DataWindow band (header, detail, footer)
    DW_CONTROL = "DW_CONTROL"      # DataWindow control


class PowerScriptTokenType(str, Enum):
    """PowerScript language tokens."""
    # PowerScript Keywords
    IF = "IF"
    THEN = "THEN"
    ELSE = "ELSE"
    ELSEIF = "ELSEIF"
    END_IF = "END IF"
    FUNCTION = "FUNCTION"
    SUBROUTINE = "SUBROUTINE"  # PowerScript subroutine
    EVENT = "EVENT"             # PowerScript event
    RETURN = "RETURN"
    FOR = "FOR"
    TO = "TO"
    NEXT = "NEXT"
    DO = "DO"
    LOOP = "LOOP"
    CHOOSE = "CHOOSE"          # PowerScript CHOOSE CASE
    CASE = "CASE"

    # Operators
    PLUS = "PLUS"
    MINUS = "MINUS"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    ASSIGN = "ASSIGN"
    EQUALS = "EQUALS"

    # Delimiters
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    SEMICOLON = "SEMICOLON"
    COMMA = "COMMA"

    # Literals
    NUMBER = "NUMBER"
    STRING = "STRING"
    IDENTIFIER = "IDENTIFIER"

    # Special
    EOF = "EOF"
    NEWLINE = "NEWLINE"


# ============================================================================
# PRIVATE AST TYPES (Scott Wlaschin's Parse Don't Validate)
# ============================================================================

def _make_powerscript_ast():
    """Create PowerScriptAST with private constructor.

    Following FDM: AST can only be created through parse functions,
    ensuring all ASTs are valid by construction.
    """
    _token = object()  # Unique token in closure

    @dataclass(frozen=True)
    class PowerScriptToken:
        """PowerScript lexical token - internal use only."""
        token_type: PowerScriptTokenType
        lexeme: str
        line: int
        column: int
        script_name: Optional[str] = None
        _token: object = field(default=None, repr=False, compare=False)

        def __post_init__(self):
            """Prevent direct construction."""
            if self._token is not _token:
                raise TypeError("Use tokenize functions to create tokens")

        @classmethod
        def _create(cls, **kwargs):
            """Internal factory."""
            return cls(**kwargs, _token=_token)

    @dataclass(frozen=True)
    class PowerScriptAST:
        """PowerScript AST node - can only be created through parsing."""
        node_type: PowerScriptNodeType
        name: str
        children: tuple = field(default_factory=tuple)
        properties: dict = field(default_factory=dict)
        _token: object = field(default=None, repr=False, compare=False)

        def __post_init__(self):
            """Prevent direct construction."""
            if self._token is not _token:
                raise TypeError(
                    "Cannot construct AST directly. "
                    "Use parse_powerscript() to create validated AST."
                )

        @classmethod
        def _create(cls, **kwargs):
            """Internal factory."""
            return cls(**kwargs, _token=_token)

        def get_child(self, index: int) -> Optional['PowerScriptAST']:
            """Get child node by index."""
            return self.children[index] if index < len(self.children) else None

        def find_children(self, node_type: PowerScriptNodeType) -> List['PowerScriptAST']:
            """Find all children of a specific type."""
            return [c for c in self.children if c.node_type == node_type]

    return PowerScriptToken, PowerScriptAST

# Create private types
_PowerScriptToken, _PowerScriptAST = _make_powerscript_ast()
del _make_powerscript_ast


@dataclass(frozen=True)
class PowerScriptParseError:
    """Error parsing PowerScript source code."""
    error_type: str  # 'SyntaxError', 'UnexpectedToken', 'InvalidEvent'
    message: str
    script_name: str
    line: int
    column: int
    token: Optional[str] = None


@dataclass(frozen=True)
class DataWindowParseError:
    """Error parsing DataWindow syntax."""
    error_type: str  # 'InvalidSQL', 'UnknownPresentationStyle', 'MalformedBand'
    message: str
    datawindow_name: str
    section: Optional[str] = None


def parse_powerscript(source: str, script_name: str = "unknown") -> Result[PowerScriptAST, PowerScriptParseError]:
    """Parse PowerScript source code to AST.

    Parses PowerBuilder's PowerScript language (Windows, DataWindows, Events, Functions).
    Pure function: PowerScript -> Result[AST, ParseError]
    """
    if not source or not source.strip():
        return Failure(PowerScriptParseError(
            error_type="EmptySource",
            message="Empty PowerScript source",
            script_name=script_name,
            line=1,
            column=1
        ))

    # Tokenize PowerScript
    tokens_result = tokenize_powerscript(source, script_name)
    if tokens_result.is_failure():
        return Failure(tokens_result.error())

    tokens = tokens_result.value()

    # Build AST from tokens
    ast_result = build_powerscript_ast(tokens, script_name)
    if ast_result.is_failure():
        return Failure(ast_result.error())

    return Success(ast_result.value())


def tokenize_powerscript(source: str, script_name: str) -> Result[List[PowerScriptToken], PowerScriptParseError]:
    """Tokenize PowerScript source code.

    Lexical analysis of PowerScript language.
    Pure function: PowerScript -> Result[Tokens, ParseError]
    """
    try:
        tokens = []
        lines = source.split('\n')

        for line_num, line in enumerate(lines, 1):
            line_tokens_result = tokenize_powerscript_line(line, line_num, script_name)
            if line_tokens_result.is_failure():
                return Failure(line_tokens_result.error())
            tokens.extend(line_tokens_result.value())

        # Add EOF token
        tokens.append(_PowerScriptToken._create(
            token_type=PowerScriptTokenType.EOF,
            lexeme="",
            line=len(lines) + 1,
            column=1,
            script_name=script_name
        ))

        return Success(tokens)
    except Exception as e:
        return Failure(PowerScriptParseError(
            error_type="TokenizationError",
            message=str(e),
            script_name=script_name,
            line=1,
            column=1
        ))


def tokenize_powerscript_line(line: str, line_num: int, script_name: str) -> Result[List[PowerScriptToken], PowerScriptParseError]:
    """Tokenize a single line of PowerScript.

    Handles PowerScript-specific syntax like tilde (~) for line continuation.
    """
    tokens = []
    column = 1
    i = 0

    try:
        while i < len(line):
            # Skip whitespace
            if line[i].isspace():
                i += 1
                column += 1
                continue

            # PowerScript comments (// or /*)
            if i < len(line) - 1 and line[i:i+2] == '//':
                # Rest of line is comment
                break

            # PowerScript string literals (single or double quotes)
            if line[i] in '"\'':
                quote = line[i]
                j = i + 1
                while j < len(line) and line[j] != quote:
                    j += 1
                if j < len(line):
                    lexeme = line[i:j+1]
                    tokens.append(PowerScriptToken(
                        token_type=PowerScriptTokenType.STRING,
                        lexeme=lexeme,
                    line=line_num,
                    column=column
                ))
                i = j + 1
                column += (j - i + 1)
            else:
                raise SyntaxError("Unterminated string", line_num, column)
            continue

        # Numbers
        if line[i].isdigit():
            j = i
            while j < len(line) and (line[j].isdigit() or line[j] == '.'):
                j += 1
            value = line[i:j]
            tokens.append(Token(
                type=TokenType.NUMBER,
                value=float(value) if '.' in value else int(value),
                line=line_num,
                column=column
            ))
            i = j
            column += (j - i)
            continue

        # Identifiers and keywords
        if line[i].isalpha() or line[i] == '_':
            j = i
            while j < len(line) and (line[j].isalnum() or line[j] == '_'):
                j += 1
            value = line[i:j]

            # Check if it's a keyword
            token_type = get_keyword_type(value.upper())
            if token_type:
                tokens.append(Token(
                    type=token_type,
                    value=value,
                    line=line_num,
                    column=column
                ))
            else:
                tokens.append(Token(
                    type=TokenType.IDENTIFIER,
                    value=value,
                    line=line_num,
                    column=column
                ))
            i = j
            column += (j - i)
            continue

        # Operators and delimiters
        if line[i] == '+':
            tokens.append(Token(TokenType.PLUS, '+', line_num, column))
        elif line[i] == '-':
            tokens.append(Token(TokenType.MINUS, '-', line_num, column))
        elif line[i] == '*':
            tokens.append(Token(TokenType.MULTIPLY, '*', line_num, column))
        elif line[i] == '/':
            tokens.append(Token(TokenType.DIVIDE, '/', line_num, column))
        elif line[i] == '=':
            tokens.append(Token(TokenType.ASSIGN, '=', line_num, column))
        elif line[i] == '(':
            tokens.append(Token(TokenType.LPAREN, '(', line_num, column))
        elif line[i] == ')':
            tokens.append(Token(TokenType.RPAREN, ')', line_num, column))
        elif line[i] == ';':
            tokens.append(Token(TokenType.SEMICOLON, ';', line_num, column))
        elif line[i] == ',':
            tokens.append(Token(TokenType.COMMA, ',', line_num, column))

        i += 1
        column += 1

    return tokens


def get_keyword_type(word: str) -> Optional[TokenType]:
    """Map keyword string to token type.

    Pure function: keyword -> TokenType or None
    """
    keywords = {
        'IF': TokenType.IF,
        'THEN': TokenType.THEN,
        'ELSE': TokenType.ELSE,
        'END': TokenType.END,
        'FUNCTION': TokenType.FUNCTION,
        'RETURN': TokenType.RETURN,
        'FOR': TokenType.FOR,
        'TO': TokenType.TO,
        'WHILE': TokenType.WHILE,
    }
    return keywords.get(word)


def build_ast(tokens: List[Token]) -> ASTNode:
    """Build AST from tokens.

    Pure function: tokens -> AST
    """
    parser = Parser(tokens)
    return parser.parse_module()


class Parser:
    """Recursive descent parser for PowerBuilder.

    Internal parser class with no I/O.
    """

    def __init__(self, tokens: List[Token]):
        """Initialize parser with tokens."""
        self.tokens = tokens
        self.current = 0

    def parse_module(self) -> ASTNode:
        """Parse top-level module."""
        children = []

        while not self.is_at_end():
            if self.peek().type == TokenType.FUNCTION:
                children.append(self.parse_function())
            elif self.peek().type == TokenType.IF:
                children.append(self.parse_if_statement())
            else:
                # Parse as statement
                stmt = self.parse_statement()
                if stmt:
                    children.append(stmt)

        return ASTNode(
            type=NodeType.MODULE,
            children=tuple(children),
            metadata={'line': 1, 'column': 1}
        )

    def parse_function(self) -> ASTNode:
        """Parse function definition."""
        self.consume(TokenType.FUNCTION)
        name = self.consume(TokenType.IDENTIFIER)

        # Parse parameters (simplified)
        params = []
        if self.check(TokenType.LPAREN):
            self.consume(TokenType.LPAREN)
            # Parse parameter list
            self.consume(TokenType.RPAREN)

        # Parse body
        body = self.parse_block()

        return ASTNode(
            type=NodeType.FUNCTION,
            value=name.value,
            children=(body,),
            metadata={'line': name.line, 'column': name.column}
        )

    def parse_if_statement(self) -> ASTNode:
        """Parse if statement."""
        if_token = self.consume(TokenType.IF)
        condition = self.parse_expression()
        self.consume(TokenType.THEN)
        then_branch = self.parse_block()

        else_branch = None
        if self.match(TokenType.ELSE):
            else_branch = self.parse_block()

        self.consume(TokenType.END)
        self.consume(TokenType.IF)

        children = [condition, then_branch]
        if else_branch:
            children.append(else_branch)

        return ASTNode(
            type=NodeType.IF_STATEMENT,
            children=tuple(children),
            metadata={'line': if_token.line, 'column': if_token.column}
        )

    def parse_block(self) -> ASTNode:
        """Parse block of statements."""
        statements = []

        while not self.is_at_end() and not self.check_any(TokenType.END, TokenType.ELSE):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)

        return ASTNode(
            type=NodeType.BLOCK,
            children=tuple(statements)
        )

    def parse_statement(self) -> Optional[ASTNode]:
        """Parse a single statement."""
        if self.check(TokenType.RETURN):
            return self.parse_return()
        elif self.check(TokenType.IDENTIFIER):
            # Could be assignment or call
            return self.parse_assignment_or_call()
        else:
            # Skip unknown tokens
            self.advance()
            return None

    def parse_return(self) -> ASTNode:
        """Parse return statement."""
        ret = self.consume(TokenType.RETURN)
        value = None

        if not self.is_at_end() and not self.check(TokenType.SEMICOLON):
            value = self.parse_expression()

        return ASTNode(
            type=NodeType.RETURN_STATEMENT,
            children=(value,) if value else (),
            metadata={'line': ret.line, 'column': ret.column}
        )

    def parse_assignment_or_call(self) -> ASTNode:
        """Parse assignment or function call."""
        identifier = self.consume(TokenType.IDENTIFIER)

        if self.match(TokenType.ASSIGN):
            # Assignment
            value = self.parse_expression()
            return ASTNode(
                type=NodeType.ASSIGNMENT,
                value=identifier.value,
                children=(value,),
                metadata={'line': identifier.line, 'column': identifier.column}
            )
        elif self.match(TokenType.LPAREN):
            # Function call
            args = []
            if not self.check(TokenType.RPAREN):
                args.append(self.parse_expression())
                while self.match(TokenType.COMMA):
                    args.append(self.parse_expression())
            self.consume(TokenType.RPAREN)

            return ASTNode(
                type=NodeType.CALL,
                value=identifier.value,
                children=tuple(args),
                metadata={'line': identifier.line, 'column': identifier.column}
            )
        else:
            # Just an identifier expression
            return ASTNode(
                type=NodeType.IDENTIFIER,
                value=identifier.value,
                metadata={'line': identifier.line, 'column': identifier.column}
            )

    def parse_expression(self) -> ASTNode:
        """Parse expression (simplified)."""
        return self.parse_term()

    def parse_term(self) -> ASTNode:
        """Parse term in expression."""
        left = self.parse_factor()

        while self.match_any(TokenType.PLUS, TokenType.MINUS):
            op = self.previous()
            right = self.parse_factor()
            left = ASTNode(
                type=NodeType.BINARY_OP,
                value=op.value,
                children=(left, right)
            )

        return left

    def parse_factor(self) -> ASTNode:
        """Parse factor in expression."""
        if self.match(TokenType.NUMBER):
            return ASTNode(
                type=NodeType.LITERAL,
                value=self.previous().value
            )
        elif self.match(TokenType.STRING):
            return ASTNode(
                type=NodeType.LITERAL,
                value=self.previous().value
            )
        elif self.match(TokenType.IDENTIFIER):
            return ASTNode(
                type=NodeType.IDENTIFIER,
                value=self.previous().value
            )
        elif self.match(TokenType.LPAREN):
            expr = self.parse_expression()
            self.consume(TokenType.RPAREN)
            return expr
        else:
            raise SyntaxError(
                f"Unexpected token: {self.peek().value}",
                self.peek().line,
                self.peek().column
            )

    # Helper methods
    def peek(self) -> Token:
        """Get current token without consuming."""
        return self.tokens[self.current] if not self.is_at_end() else self.tokens[-1]

    def previous(self) -> Token:
        """Get previous token."""
        return self.tokens[self.current - 1]

    def advance(self) -> Token:
        """Consume and return current token."""
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def is_at_end(self) -> bool:
        """Check if at end of tokens."""
        return self.current >= len(self.tokens) or (
            self.current < len(self.tokens) and self.tokens[self.current].type == TokenType.EOF
        )

    def check(self, token_type: TokenType) -> bool:
        """Check if current token is of given type."""
        return self.peek().type == token_type

    def check_any(self, *token_types: TokenType) -> bool:
        """Check if current token is any of given types."""
        return any(self.check(t) for t in token_types)

    def match(self, token_type: TokenType) -> bool:
        """Check and consume if match."""
        if self.check(token_type):
            self.advance()
            return True
        return False

    def match_any(self, *token_types: TokenType) -> bool:
        """Check and consume if any match."""
        for t in token_types:
            if self.match(t):
                return True
        return False

    def consume(self, token_type: TokenType) -> Token:
        """Consume token of expected type or raise error."""
        if self.check(token_type):
            return self.advance()
        raise SyntaxError(
            f"Expected {token_type}, got {self.peek().type}",
            self.peek().line,
            self.peek().column
        )


def validate_ast(ast: ASTNode) -> List[str]:
    """Validate AST and return warnings.

    Pure function to check for potential issues.
    """
    warnings = []

    # Check for empty functions
    functions = ast.find_children(NodeType.FUNCTION)
    for func in functions:
        if not func.children or all(c.type == NodeType.BLOCK and not c.children for c in func.children):
            warnings.append(f"Empty function: {func.value}")

    # Check for unreachable code
    for node in walk_ast(ast):
        if node.type == NodeType.BLOCK:
            found_return = False
            for i, child in enumerate(node.children):
                if found_return:
                    warnings.append("Unreachable code after return statement")
                    break
                if child.type == NodeType.RETURN_STATEMENT:
                    found_return = True

    return warnings


def walk_ast(node: ASTNode):
    """Walk AST nodes recursively.

    Generator that yields all nodes in the tree.
    """
    yield node
    for child in node.children:
        yield from walk_ast(child)
