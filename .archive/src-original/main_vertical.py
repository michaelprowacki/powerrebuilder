#!/usr/bin/env python
"""PowerRebuilder - Vertical Slice Architecture.

Main entry point using the new vertical slice architecture.
Each pipeline stage is a cohesive slice with domain, app, and infra layers.
"""

import asyncio
import sys
from pathlib import Path
from typing import List

# Import workflows from app layer
from src_new.app.extract.extract_library import (
    run as extract_workflow,
    ExtractLibraryDTO,
)
from src_new.app.parse.parse_to_ast import run as parse_workflow, ParseToASTDTO, ASTNode

# Import adapters
from src_new.adapters.filesystem import FilesystemAdapter


# Simple adapters for demo
class SimpleSourceReader:
    """Simple adapter for reading source files."""

    async def read_source(self, path: str) -> str:
        """Read source file."""
        file_path = Path(path)
        if file_path.exists():
            return file_path.read_text()
        # Return mock source for demo
        return """
function main()
    return 0
end function
"""

    async def get_encoding(self, path: str) -> str:
        """Get file encoding."""
        return "utf-8"


class SimpleASTWriter:
    """Simple adapter for writing AST."""

    async def write_ast_json(self, path: str, ast_dict: dict) -> None:
        """Write AST as JSON."""
        import json

        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(ast_dict, indent=2))


async def run_full_pipeline(input_path: str, output_path: str) -> int:
    """Run the full 5-stage pipeline.

    Extract -> Decompile -> Parse -> Model -> Generate
    """
    print("🚀 PowerRebuilder - Full Pipeline")
    print("=" * 50)

    # Stage 1: Extract
    print("\n📦 Stage 1: Extract")
    file_reader = DiskFileReader()
    object_writer = DiskObjectWriter()

    extract_dto = ExtractLibraryDTO(
        library_path=input_path,
        output_dir=f"{output_path}/extracted",
        validate_only=False,
    )

    extract_result, extract_events = await extract_workflow(
        extract_dto, file_reader, object_writer
    )

    if extract_result.success:
        print(f"  ✓ Extracted {extract_result.objects_extracted} objects")
    else:
        print("  ✗ Extraction failed")
        return 1

    # Stage 2: Decompile
    print("\n🔧 Stage 2: Decompile")
    print("  ⏭️  Skipping (using mock source for demo)")

    # Stage 3: Parse
    print("\n🌲 Stage 3: Parse")
    source_reader = SimpleSourceReader()
    ast_writer = SimpleASTWriter()

    parse_dto = ParseToASTDTO(
        source_path=f"{output_path}/extracted/mock.sru",
        output_path=f"{output_path}/parsed/mock.ast.json",
    )

    parse_result, parse_events = await parse_workflow(
        parse_dto, source_reader, ast_writer
    )

    if parse_result.success:
        print(f"  ✓ Parsed {parse_result.node_count} AST nodes")
    else:
        print(f"  ✗ Parse failed: {parse_result.errors}")

    # Stage 4: Model
    print("\n🏗️  Stage 4: Model")
    # Create mock AST for demo
    mock_ast = ASTNode(
        type=NodeType.MODULE,
        children=(ASTNode(type=NodeType.FUNCTION, value="main", children=()),),
    )

    model_result = build_model(mock_ast)
    if hasattr(model_result, "model"):
        print(f"  ✓ Built model with {len(model_result.model.symbols)} symbols")
        semantic_model = model_result.model
    else:
        print("  ✗ Model building failed")
        return 1

    # Stage 5: Generate
    print("\n✨ Stage 5: Generate")
    generate_result = generate_flutter(semantic_model)

    if hasattr(generate_result, "project"):
        project = generate_result.project
        print(f"  ✓ Generated {len(project.files)} files")

        # Write generated files
        output_base = Path(output_path) / "generated"
        for file in project.files:
            file_path = output_base / file.path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(file.content)
            print(f"    📄 {file.path}")
    else:
        print("  ✗ Generation failed")
        return 1

    print("\n" + "=" * 50)
    print("✅ Pipeline complete!")
    print(f"📁 Output: {output_path}/")

    return 0


async def main(args: List[str]) -> int:
    """Main entry point.

    Args:
        args: Command line arguments

    Returns:
        Exit code (0 for success)
    """
    if len(args) < 3:
        print("Usage: python main_vertical.py <command> <input> <output>")
        print("Commands:")
        print("  extract  - Extract objects from PBL/PBD")
        print("  parse    - Parse source to AST")
        print("  all      - Run full pipeline")
        return 1

    command = args[0]
    input_path = args[1]
    output_path = args[2]

    if command == "extract":
        # Run extract workflow
        filesystem = FilesystemAdapter()

        dto = ExtractLibraryDTO(
            library_path=input_path, output_dir=output_path, validate_only=False
        )

        result, events = await extract_workflow(dto, filesystem)

        # Print results
        if result.success:
            print(f"✓ Extracted {result.objects_extracted} objects")
            print(f"  Format: {result.format}")
            if result.errors:
                print(f"  Warnings: {len(result.errors)} issues encountered")
        else:
            print(
                f"✗ Extraction failed: {result.errors[0] if result.errors else 'Unknown error'}"
            )
            return 1

        # Print events (in real app, these would be published)
        for event in events[-3:]:  # Show last 3 events
            print(f"  Event: {event.type} - {event.data}")

        return 0

    elif command == "parse":
        # Run parse workflow
        source_reader = SimpleSourceReader()
        ast_writer = SimpleASTWriter()

        dto = ParseToASTDTO(source_path=input_path, output_path=output_path)

        result, events = await parse_workflow(dto, source_reader, ast_writer)

        if result.success:
            print(f"✓ Parsed {result.node_count} nodes")
            if result.warnings:
                print(f"  Warnings: {', '.join(result.warnings)}")
        else:
            print(f"✗ Parse failed: {', '.join(result.errors)}")
            return 1

        return 0

    elif command == "all":
        # Run full pipeline
        return await run_full_pipeline(input_path, output_path)

    else:
        print(f"Unknown command: {command}")
        print("Available commands: extract, parse, all")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main(sys.argv[1:]))
    sys.exit(exit_code)
