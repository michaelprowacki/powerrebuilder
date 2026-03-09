"""Parse to AST Application Service.

Coordinates parsing PowerScript source to Abstract Syntax Trees.
"""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class ParseToASTDTO:
    """Data transfer object for parse request."""

    source_path: str
    output_dir: str
    strict_mode: bool = False


@dataclass(frozen=True)
class ParseResult:
    """Result of parsing operation."""

    success: bool
    ast_nodes: int
    errors: List[str]


@dataclass(frozen=True)
class ParseEvent:
    """Event emitted during parsing."""

    type: str
    data: dict


@dataclass(frozen=True)
class ASTNode:
    """Simplified AST node representation."""

    type: str
    name: str
    children: List["ASTNode"]
    attributes: dict


async def run(
    dto: ParseToASTDTO, source_reader, ast_writer
) -> Tuple[ParseResult, List[ParseEvent]]:
    """Run the parsing workflow.

    This application service coordinates:
    1. Reading PowerScript source
    2. Parsing to AST
    3. Writing AST output

    Args:
        dto: Parse parameters
        source_reader: Adapter for reading source files
        ast_writer: Adapter for writing AST

    Returns:
        Tuple of parse result and events
    """
    events = []

    try:
        # Read source file
        source_code = await source_reader.read_source(dto.source_path)

        # Parse to AST (simplified - would call domain function)
        # from src_new.domain.parse.parse_powerscript import parse_powerscript
        # result = parse_powerscript(source_code)

        # Mock AST for now
        ast = ASTNode(
            type="function", name="main", children=[], attributes={"returns": "int"}
        )

        # Write AST if output requested
        if dto.output_dir:
            await ast_writer.write_ast(dto.output_dir, ast)

        events.append(
            ParseEvent(
                type="parse_completed", data={"source": dto.source_path, "nodes": 1}
            )
        )

        return (ParseResult(success=True, ast_nodes=1, errors=[]), events)

    except Exception as e:
        return (ParseResult(success=False, ast_nodes=0, errors=[str(e)]), events)
