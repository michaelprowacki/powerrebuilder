"""Lark Parser Workflow.

Application layer workflow for parsing PowerBuilder source using Lark grammars.
Uses Parse Don't Validate pattern with factory functions.
Coordinates domain functions to transform source code into parse trees and ASTs.
"""

from typing import List, Optional, Dict, Any, Union
from pathlib import Path
import time

from lark import Tree, Token

from src_new.shared.result import Result, Success, Error
from src_new.adapters.parsing.lark_adapter import (
    LarkConfig,
    LarkGrammar,
    LarkTree,
    LarkParserAdapter,
    PowerBuilderTransformer,
    load_lark_grammar,
)
from src_new.adapters.parsing.ast_adapter import ASTNode


# ============================================================================
# PARSE DON'T VALIDATE - FACTORY FUNCTIONS
# ============================================================================


class _ParseToken:
    """Hidden token for Parse Don't Validate pattern."""

    pass


def create_parser(
    grammar_path: Path, config: Optional[LarkConfig] = None
) -> Result[LarkParserAdapter, str]:
    """Create a validated Lark parser from grammar file.

    Parse Don't Validate entry point.
    """
    # Load grammar using adapter
    grammar_result = load_lark_grammar(grammar_path)
    if isinstance(grammar_result, Error):
        return grammar_result

    grammar = grammar_result.value

    # Create parser configuration
    if config is None:
        config = LarkConfig()

    # Create parser adapter with validated grammar
    try:
        adapter = LarkParserAdapter(grammar, config)
        return Success(adapter)
    except Exception as e:
        return Error(f"Failed to create parser: {e}")


# ============================================================================
# PARSING WORKFLOW
# ============================================================================


def parse_powerbuilder_source(
    source: str, parser: LarkParserAdapter
) -> Result[LarkTree, str]:
    """Parse PowerBuilder source code.

    Main parsing workflow using validated parser.
    """
    if not source.strip():
        return Error("Empty source code")

    start_time = time.time()

    # Parse with adapter
    parse_result = parser.parse(source)
    if isinstance(parse_result, Error):
        return parse_result

    lark_tree = parse_result.value

    # Record parse time
    parse_time = time.time() - start_time

    return Success(lark_tree)


def convert_to_ast(
    lark_tree: LarkTree, transformer: Optional[PowerBuilderTransformer] = None
) -> Result[ASTNode, str]:
    """Convert Lark tree to AST using adapter."""
    if transformer is None:
        transformer = PowerBuilderTransformer()

    # Use adapter to transform
    parser_adapter = LarkParserAdapter(
        LarkGrammar(grammar_text="", start_symbol="program"), LarkConfig()
    )

    return parser_adapter.transform(lark_tree, transformer)


# ============================================================================
# AST TRANSFORMATION
# ============================================================================


def transform_to_powerbuilder_ast(lark_tree: LarkTree) -> Result[Dict[str, Any], str]:
    """Transform Lark tree to PowerBuilder AST.

    Uses the adapter's transformer.
    """
    transformer = PowerBuilderTransformer()

    # Create a temporary adapter to use its transform method
    adapter = LarkParserAdapter(
        lark_tree.metadata.get("grammar", LarkGrammar("", None))
    )

    result = adapter.transform(lark_tree, transformer)
    if isinstance(result, Error):
        return result

    # Convert to dictionary representation for serialization
    pb_ast = result.value

    # Map to domain PowerBuilder types
    return Success(_map_to_powerbuilder_domain(pb_ast))


def _map_to_powerbuilder_domain(ast_data: Any) -> Dict[str, Any]:
    """Map transformed AST to PowerBuilder domain types."""
    if isinstance(ast_data, dict):
        ast_type = ast_data.get("type", "unknown")

        # Map to appropriate PowerBuilder domain type
        if ast_type == "window":
            return {
                "type": "WindowNode",
                "name": ast_data.get("name", "unnamed"),
                "title": ast_data.get("title", ""),
                "controls": ast_data.get("controls", []),
            }
        elif ast_type == "function":
            return {
                "type": "FunctionNode",
                "name": ast_data.get("name", "unnamed"),
                "parameters": ast_data.get("parameters", []),
                "return_type": ast_data.get("return_type"),
                "body": ast_data.get("body", []),
            }
        elif ast_type == "datawindow":
            return {
                "type": "DataWindowNode",
                "name": ast_data.get("name", "unnamed"),
                "sql": ast_data.get("sql"),
                "columns": ast_data.get("columns", []),
            }
        # Add more mappings as needed

    return ast_data


# ============================================================================
# GRAMMAR LOADING
# ============================================================================


def load_powerbuilder_grammar_from_path() -> Result[LarkGrammar, str]:
    """Load PowerBuilder grammar from default file locations.

    Wrapper around adapter's load_lark_grammar.
    """
    grammar_path = (
        Path(__file__).parent.parent.parent
        / "shared"
        / "grammars"
        / "powerbuilder.lark"
    )

    if not grammar_path.exists():
        # Try archive location
        grammar_path = (
            Path(__file__).parent.parent.parent.parent
            / "archive"
            / "src"
            / "parse"
            / "grammar"
            / "definitions"
            / "powerbuilder.lark"
        )

    if not grammar_path.exists():
        return Error("PowerBuilder grammar not found")

    # Use adapter's load function
    return load_lark_grammar(grammar_path)


# ============================================================================
# ERROR RECOVERY
# ============================================================================


def parse_with_error_recovery(
    source: str, parser: LarkParserAdapter, max_errors: int = 10
) -> Result[LarkTree, str]:
    """Parse with error recovery.

    Attempts to recover from parse errors and continue.
    """
    errors = []
    partial_trees = []

    # Split source into statements/blocks for partial parsing
    blocks = _split_into_blocks(source)

    for block in blocks:
        block_result = parse_powerbuilder_source(block, parser)
        if isinstance(block_result, Success):
            partial_trees.append(block_result.value)
        else:
            errors.append(block_result.error)
            if len(errors) >= max_errors:
                break

    if not partial_trees and errors:
        return Error(f"Parse failed with {len(errors)} errors")

    # Combine partial trees
    if partial_trees:
        combined = _combine_partial_trees(partial_trees)
        return Success(combined)

    return Error("No parseable content found")


def _split_into_blocks(source: str) -> List[str]:
    """Split source into parseable blocks for error recovery."""
    # Simple splitting by function/class boundaries
    blocks = []
    current_block = []

    for line in source.split("\n"):
        if line.strip().startswith(("function ", "class ", "window ")):
            if current_block:
                blocks.append("\n".join(current_block))
                current_block = []
        current_block.append(line)

    if current_block:
        blocks.append("\n".join(current_block))

    return blocks


def _combine_partial_trees(trees: List[LarkTree]) -> LarkTree:
    """Combine partial parse trees into one."""
    # Simplified combination - would need proper merging logic
    if len(trees) == 1:
        return trees[0]

    # Create combined tree by merging the Lark trees
    from lark import Tree

    combined_tree = Tree("program", [t.tree for t in trees])

    return LarkTree(
        tree=combined_tree,
        source="",  # Combined source
        metadata={"combined": True},
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def count_lark_nodes(tree: Union[Tree, Token]) -> int:
    """Count nodes in a Lark tree."""
    if isinstance(tree, Token):
        return 1
    return 1 + sum(count_lark_nodes(child) for child in tree.children)
