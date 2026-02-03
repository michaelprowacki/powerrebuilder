"""Parse Application - Parse to AST Workflow.

This workflow orchestrates parsing PowerBuilder source to AST.
"""

from dataclasses import dataclass
from typing import List, Tuple
from enum import Enum

from src_new.domain.parse import parse_source
from src_new.domain.parse.shared import ASTNode, ParseSuccess, ParseFailed
from .ports import ISourceReader, IASTWriter


# ============================================================================
# DTOs - Inline with workflow
# ============================================================================


@dataclass
class ParseToASTDTO:
    """Input DTO for parsing workflow."""

    source_path: str
    output_path: str
    validate_only: bool = False
    include_metadata: bool = True


@dataclass
class ParseResult:
    """Output from parsing workflow."""

    success: bool
    source_path: str
    output_path: str
    node_count: int
    errors: List[str]
    warnings: List[str]


# ============================================================================
# Events
# ============================================================================


class ParseEventType(Enum):
    """Types of parse events."""

    PARSE_STARTED = "parse_started"
    PARSE_COMPLETED = "parse_completed"
    PARSE_FAILED = "parse_failed"
    SYNTAX_ERROR = "syntax_error"
    AST_GENERATED = "ast_generated"


@dataclass
class ParseEvent:
    """Event from parse workflow."""

    type: ParseEventType
    source_path: str
    data: dict


# ============================================================================
# Workflow
# ============================================================================


async def run(
    dto: ParseToASTDTO,
    source_reader: ISourceReader,
    ast_writer: IASTWriter,
) -> Tuple[ParseResult, List[ParseEvent]]:
    """Parse source to AST workflow.

    Orchestrates parsing PowerBuilder source code to AST.

    Args:
        dto: Input parameters
        source_reader: Port for reading source
        ast_writer: Port for writing AST

    Returns:
        Tuple of (result, events)
    """
    events = []

    # Start event
    events.append(
        ParseEvent(
            type=ParseEventType.PARSE_STARTED,
            source_path=dto.source_path,
            data={"output": dto.output_path},
        )
    )

    try:
        # Read source through port
        source = await source_reader.read_source(dto.source_path)
        encoding = await source_reader.get_encoding(dto.source_path)

    except Exception as e:
        events.append(
            ParseEvent(
                type=ParseEventType.PARSE_FAILED,
                source_path=dto.source_path,
                data={"error": str(e)},
            )
        )
        return ParseResult(
            success=False,
            source_path=dto.source_path,
            output_path=dto.output_path,
            node_count=0,
            errors=[f"Failed to read source: {str(e)}"],
            warnings=[],
        ), events

    # Parse using domain function
    result = parse_source.parse(source)

    # Handle parse result (ADT pattern matching)
    if isinstance(result, ParseSuccess):
        ast = result.ast
        warnings = result.warnings

        # Count nodes
        node_count = count_nodes(ast)

        # Generate AST event
        events.append(
            ParseEvent(
                type=ParseEventType.AST_GENERATED,
                source_path=dto.source_path,
                data={"nodes": node_count, "warnings": len(warnings)},
            )
        )

        # Write AST if not validate only
        if not dto.validate_only:
            try:
                # Convert to dictionary for JSON serialization
                ast_dict = ast_to_dict(ast, dto.include_metadata)
                await ast_writer.write_ast_json(dto.output_path, ast_dict)

            except Exception as e:
                events.append(
                    ParseEvent(
                        type=ParseEventType.PARSE_FAILED,
                        source_path=dto.source_path,
                        data={"error": f"Failed to write AST: {str(e)}"},
                    )
                )
                return ParseResult(
                    success=False,
                    source_path=dto.source_path,
                    output_path=dto.output_path,
                    node_count=node_count,
                    errors=[f"Failed to write AST: {str(e)}"],
                    warnings=warnings,
                ), events

        # Success event
        events.append(
            ParseEvent(
                type=ParseEventType.PARSE_COMPLETED,
                source_path=dto.source_path,
                data={"success": True, "nodes": node_count, "encoding": encoding},
            )
        )

        return ParseResult(
            success=True,
            source_path=dto.source_path,
            output_path=dto.output_path,
            node_count=node_count,
            errors=[],
            warnings=warnings,
        ), events

    elif isinstance(result, ParseFailed):
        # Syntax error event
        events.append(
            ParseEvent(
                type=ParseEventType.SYNTAX_ERROR,
                source_path=dto.source_path,
                data={
                    "error": result.error,
                    "line": result.line,
                    "column": result.column,
                },
            )
        )

        return ParseResult(
            success=False,
            source_path=dto.source_path,
            output_path=dto.output_path,
            node_count=0,
            errors=[f"{result.error} at {result.line}:{result.column}"],
            warnings=[],
        ), events

    else:
        # Should never happen with proper ADT
        raise ValueError(f"Unexpected parse result type: {type(result)}")


def count_nodes(ast: ASTNode) -> int:
    """Count total nodes in AST.

    Pure function to recursively count nodes.
    """
    count = 1  # Count this node
    for child in ast.children:
        count += count_nodes(child)
    return count


def ast_to_dict(node: ASTNode, include_metadata: bool = True) -> dict:
    """Convert AST node to dictionary.

    Pure function for serialization.
    """
    result = {
        "type": node.type.value,
    }

    if node.value is not None:
        result["value"] = node.value

    if node.children:
        result["children"] = [
            ast_to_dict(child, include_metadata) for child in node.children
        ]

    if include_metadata and node.metadata:
        result["metadata"] = node.metadata

    return result


async def run_batch(
    source_files: List[str],
    output_dir: str,
    source_reader: ISourceReader,
    ast_writer: IASTWriter,
) -> Tuple[List[ParseResult], List[ParseEvent]]:
    """Batch parsing workflow.

    Parse multiple source files in sequence.
    """
    results = []
    all_events = []

    for source_path in source_files:
        # Generate output path
        source_name = source_path.split("/")[-1].replace(".sru", ".ast.json")
        output_path = f"{output_dir}/{source_name}"

        dto = ParseToASTDTO(source_path=source_path, output_path=output_path)

        result, events = await run(dto, source_reader, ast_writer)
        results.append(result)
        all_events.extend(events)

    return results, all_events
