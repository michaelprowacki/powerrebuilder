"""Lark Parser Adapter.

Adapter layer for Lark parsing library.
This is HOW we parse, not WHAT PowerBuilder is.
Converts between Lark's representation and our domain types.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from pathlib import Path

from lark import Lark, Tree, Token, Transformer
from lark.exceptions import LarkError, ParseError as LarkParseError

from src_new.shared.result import Result, Success, Error


# ============================================================================
# LARK-SPECIFIC TYPES (Implementation details)
# ============================================================================


@dataclass(frozen=True)
class LarkConfig:
    """Lark parser configuration."""

    parser: str = "lalr"  # lalr, earley, cyk
    lexer: str = "contextual"  # contextual, basic
    propagate_positions: bool = True
    maybe_placeholders: bool = False
    cache: bool = True
    g_regex_flags: int = 0
    use_bytes: bool = False
    import_paths: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class LarkGrammar:
    """Lark grammar definition."""

    grammar_text: str
    start_symbol: Optional[str] = None
    terminals: Dict[str, str] = field(default_factory=dict)
    rules: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class LarkTree:
    """Wrapper around Lark's Tree."""

    tree: Tree
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LarkToken:
    """Wrapper around Lark's Token."""

    token: Token
    type: str
    value: str
    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None


# ============================================================================
# PARSER ADAPTER
# ============================================================================


class LarkParserAdapter:
    """Adapter for Lark parser.

    Encapsulates all Lark-specific implementation details.
    """

    def __init__(self, grammar: LarkGrammar, config: Optional[LarkConfig] = None):
        """Initialize parser with grammar."""
        self.grammar = grammar
        self.config = config or LarkConfig()
        self.parser = self._create_parser()

    def _create_parser(self) -> Lark:
        """Create Lark parser instance."""
        return Lark(
            self.grammar.grammar_text,
            parser=self.config.parser,
            lexer=self.config.lexer,
            propagate_positions=self.config.propagate_positions,
            maybe_placeholders=self.config.maybe_placeholders,
            cache=self.config.cache,
            g_regex_flags=self.config.g_regex_flags,
            use_bytes=self.config.use_bytes,
            import_paths=self.config.import_paths,
            start=self.grammar.start_symbol,
        )

    def parse(self, source: str) -> Result[LarkTree, str]:
        """Parse source code into Lark tree."""
        try:
            tree = self.parser.parse(source)
            return Success(LarkTree(tree=tree, source=source))
        except LarkParseError as e:
            return Error(f"Parse error: {e}")
        except LarkError as e:
            return Error(f"Lark error: {e}")

    def transform(self, tree: LarkTree, transformer: Transformer) -> Result[Any, str]:
        """Apply transformer to tree."""
        try:
            result = transformer.transform(tree.tree)
            return Success(result)
        except Exception as e:
            return Error(f"Transform error: {e}")


# ============================================================================
# GRAMMAR LOADING
# ============================================================================


def load_lark_grammar(grammar_path: Path) -> Result[LarkGrammar, str]:
    """Load Lark grammar from file."""
    if not grammar_path.exists():
        return Error(f"Grammar file not found: {grammar_path}")

    try:
        grammar_text = grammar_path.read_text()

        # Parse grammar to extract metadata
        rules = {}
        terminals = {}
        start = None

        for line in grammar_text.split("\n"):
            line = line.strip()
            if not line or line.startswith("//"):
                continue

            # Detect start rule
            if line.startswith("?start:"):
                start = line.split(":")[1].strip()
            # Detect terminals (uppercase)
            elif line[0].isupper() and ":" in line:
                name, pattern = line.split(":", 1)
                terminals[name.strip()] = pattern.strip()
            # Detect rules (lowercase)
            elif line and line[0].islower() and ":" in line:
                name, definition = line.split(":", 1)
                rules[name.strip()] = definition.strip()

        return Success(
            LarkGrammar(
                grammar_text=grammar_text,
                start_symbol=start,
                terminals=terminals,
                rules=rules,
            )
        )
    except Exception as e:
        return Error(f"Failed to load grammar: {e}")


# ============================================================================
# TREE CONVERSION
# ============================================================================


def lark_tree_to_dict(tree: Union[Tree, Token]) -> Dict[str, Any]:
    """Convert Lark tree to dictionary representation."""
    if isinstance(tree, Token):
        return {
            "type": "token",
            "token_type": tree.type,
            "value": tree.value,
            "line": getattr(tree, "line", None),
            "column": getattr(tree, "column", None),
        }

    # It's a Tree
    return {
        "type": "tree",
        "data": tree.data,
        "children": [lark_tree_to_dict(child) for child in tree.children],
        "meta": {
            "line": tree.meta.line if hasattr(tree, "meta") else None,
            "column": tree.meta.column if hasattr(tree, "meta") else None,
            "end_line": tree.meta.end_line if hasattr(tree, "meta") else None,
            "end_column": tree.meta.end_column if hasattr(tree, "meta") else None,
        }
        if hasattr(tree, "meta")
        else None,
    }


def dict_to_lark_tree(data: Dict[str, Any]) -> Union[Tree, Token]:
    """Convert dictionary back to Lark tree."""
    if data["type"] == "token":
        return Token(
            data["token_type"],
            data["value"],
            line=data.get("line"),
            column=data.get("column"),
        )

    # It's a tree
    children = [dict_to_lark_tree(child) for child in data.get("children", [])]
    tree = Tree(data["data"], children)

    # Add metadata if present
    if data.get("meta"):
        meta = data["meta"]
        tree.meta = type(
            "Meta",
            (),
            {
                "line": meta.get("line"),
                "column": meta.get("column"),
                "end_line": meta.get("end_line"),
                "end_column": meta.get("end_column"),
            },
        )()

    return tree


# ============================================================================
# POWERBUILDER TRANSFORMER
# ============================================================================


class PowerBuilderTransformer(Transformer):
    """Lark transformer for PowerBuilder syntax.

    Transforms Lark parse tree into domain objects.
    """

    def __init__(self):
        """Initialize transformer."""
        super().__init__()

    # Window transformation
    def window_declaration(self, items):
        """Transform window declaration."""
        return {
            "type": "window",
            "name": items[0].value if items else "unnamed",
            "title": items[1].value if len(items) > 1 else "",
            "controls": items[2:] if len(items) > 2 else [],
        }

    # Function transformation
    def function_declaration(self, items):
        """Transform function declaration."""
        return {
            "type": "function",
            "name": items[0].value if items else "unnamed",
            "parameters": items[1] if len(items) > 1 else [],
            "return_type": items[2] if len(items) > 2 else None,
            "body": items[3] if len(items) > 3 else [],
        }

    # DataWindow transformation
    def datawindow_declaration(self, items):
        """Transform DataWindow declaration."""
        return {
            "type": "datawindow",
            "name": items[0].value if items else "unnamed",
            "sql": items[1] if len(items) > 1 else None,
            "columns": items[2:] if len(items) > 2 else [],
        }

    # Event transformation
    def event_declaration(self, items):
        """Transform event declaration."""
        return {
            "type": "event",
            "name": items[0].value if items else "unnamed",
            "parameters": items[1] if len(items) > 1 else [],
            "body": items[2] if len(items) > 2 else [],
        }

    # Control transformation
    def control_declaration(self, items):
        """Transform control declaration."""
        control_type = items[0].value if items else "unknown"
        return {
            "type": "control",
            "control_type": control_type,
            "name": items[1].value if len(items) > 1 else "unnamed",
            "properties": items[2] if len(items) > 2 else {},
        }

    # Expression transformation
    def expression(self, items):
        """Transform expression."""
        if len(items) == 1:
            return items[0]
        elif len(items) == 3:
            # Binary expression
            return {
                "type": "binary_expr",
                "left": items[0],
                "operator": items[1].value,
                "right": items[2],
            }
        return items

    # Statement transformation
    def statement(self, items):
        """Transform statement."""
        if not items:
            return {"type": "empty_statement"}
        return items[0]

    # Identifier
    def identifier(self, items):
        """Transform identifier."""
        return items[0].value

    # Literal values
    def string_literal(self, items):
        """Transform string literal."""
        return {"type": "string", "value": items[0].value.strip('"')}

    def number_literal(self, items):
        """Transform number literal."""
        return {"type": "number", "value": float(items[0].value)}

    def boolean_literal(self, items):
        """Transform boolean literal."""
        return {"type": "boolean", "value": items[0].value.lower() == "true"}


# ============================================================================
# ERROR RECOVERY
# ============================================================================


class ErrorRecoveryTransformer(Transformer):
    """Transformer with error recovery."""

    def __init__(self):
        """Initialize with error tracking."""
        super().__init__()
        self.errors = []

    def __default__(self, data, children, meta):
        """Default handler for unmatched rules."""
        self.errors.append(
            {
                "rule": data,
                "location": meta if meta else None,
                "message": f"Unhandled rule: {data}",
            }
        )
        return {"type": "error", "rule": data, "children": children}


# ============================================================================
# VISITOR PATTERN
# ============================================================================


class PowerBuilderVisitor:
    """Visitor for Lark parse trees.

    Alternative to transformer for more control.
    """

    def visit(self, tree: Union[Tree, Token]) -> Any:
        """Visit tree node."""
        if isinstance(tree, Token):
            return self.visit_token(tree)

        # Call method based on tree.data
        method_name = f"visit_{tree.data}"
        if hasattr(self, method_name):
            return getattr(self, method_name)(tree)
        else:
            return self.visit_default(tree)

    def visit_token(self, token: Token) -> Any:
        """Visit token."""
        return token.value

    def visit_default(self, tree: Tree) -> Any:
        """Default visitor for unhandled nodes."""
        # Visit children
        results = []
        for child in tree.children:
            results.append(self.visit(child))
        return results

    def visit_children(self, tree: Tree) -> List[Any]:
        """Helper to visit all children."""
        return [self.visit(child) for child in tree.children]
