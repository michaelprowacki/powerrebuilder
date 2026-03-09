# CLAUDE.md - PowerRebuilder Developer Guide

This file provides accurate guidance for Claude Code and developers working with PowerRebuilder.

## Project Overview

PowerRebuilder is a **five-stage sequential pipeline** that reverse engineers compiled PowerBuilder applications into modern codebases (Python/Litestar and Dart/Flutter).

## Installation & Commands

### Setup
```bash
# Install dependencies (using Task and uv)
task deps         # Install all dependencies
task deps:update  # Update all dependencies
# Or manually with uv:
uv sync           # Runtime dependencies
uv sync --dev     # All dependencies including dev
```

### Running the Pipeline
```bash
# Full pipeline (all 5 stages sequentially)
python main.py all input.pbl output/

# Individual stages (MUST run in order)
python main.py extract input.pbl output/extracted/     # Stage 1: Extract P-code
python main.py decompile output/extracted/ output/decompiled/  # Stage 2: P-code to source
python main.py parse output/decompiled/ output/parsed/         # Stage 3: Source to AST
python main.py model output/parsed/ output/models/             # Stage 4: AST to models
python main.py generate output/models/ output/generated/       # Stage 5: Generate code
```

### Testing & Quality
```bash
# Using Task (recommended)
task test          # Run all tests
task coverage      # Generate coverage report
task lint          # Run linting
task format        # Auto-format code
task type          # Type checking
task security      # Security audit

# Or manually with uv:
uv run pytest
uv run pytest tests/unit/extract/ -v
uv run pytest --cov=src --cov-report=html
uv run ruff check .
uv run ruff format .
uv run mypy src/
```

## Pipeline Architecture (Sequential)

**CRITICAL**: The pipeline stages MUST run in order. Each stage depends on the previous stage's output.

### Stage 1: Extract
- **Input**: PowerBuilder PBL/PBD binary archives
- **Output**: P-code files (`.fun`) containing compiled bytecode
- **Module**: `src/extract/`
- **Key Class**: `ExtractCoordinator`

### Stage 2: Decompile
- **Input**: P-code files (`.fun`) from Extract
- **Output**: PowerBuilder source files (`.sru`, `.srw`, `.srm`)
- **Module**: `src/decompile/`
- **Key Class**: `DecompileCoordinator`
- **Note**: Parse CANNOT process P-code directly - it needs the source this stage produces

### Stage 3: Parse
- **Input**: PowerBuilder source files from Decompile
- **Output**: Abstract Syntax Tree (AST) in JSON format
- **Module**: `src/parse/`
- **Key Class**: `ParseCoordinator`
- **Technology**: Lark parser with EBNF grammars

### Stage 4: Model
- **Input**: AST JSON from Parse
- **Output**: Semantic models with resolved dependencies
- **Module**: `src/model/`
- **Key Classes**: `ASTProcessor`, `ModelExtractorVisitor`
- **Note**: ModelCoordinator referenced in main.py may not exist - uses services directly

### Stage 5: Generate
- **Input**: Semantic models from Model
- **Output**: Modern application code (Flutter/Dart or Python/Litestar)
- **Module**: `src/generate/`
- **Key Class**: `GenerateCoordinator`
- **Templates**: Jinja2-based in `src/generate/templates/`

## Important Implementation Notes

### Current Architecture Reality
- **No Dependency Injection**: DI system was removed - direct imports used throughout
- **No Makefile**: Use `uv` commands directly, not `make`
- **Sequential Processing**: Despite some docs claiming parallel, stages run sequentially
- **ModelCoordinator**: May be missing - main.py references it but it might not exist

### P-code Detection (Decompile Stage)
- Uses tiered detection: Ultra-fast → Fast → Comprehensive → Deep analysis
- Located in `src/decompile/pcode/`
- Handles PowerBuilder versions 6.0-12.5

### PowerBuilder Object Types
- `.fun` - Functions (compiled P-code)
- `.srw` - Windows
- `.sru` - User objects
- `.srm` - Menus
- `.srd` - DataWindows
- `.srs` - Structures
- `.sra` - Applications

### Code Generation Targets
- **Flutter/Dart**: Complete mobile apps with glassmorphism design
- **Python/Litestar**: Web APIs with SQLModel/Pydantic models
- **Python Desktop**: tkinter/PyQt5 GUI applications (partial)

## Common Development Tasks

### Debug a Failed Stage
```bash
# Enable debug logging
python main.py --loglevel DEBUG extract input/ output/

# Check intermediate outputs
ls output/extracted/    # Check .fun files
ls output/decompiled/   # Check .sru files
ls output/parsed/       # Check .json AST files
```

### Add Support for New PowerBuilder Feature
1. Update grammar in `src/parse/grammar/definitions/`
2. Add AST node in `src/model/ast/`
3. Update visitor in `src/model/visitors/`
4. Add transformation in `src/generate/converters/`
5. Create template in `src/generate/templates/`

### Fix Import Errors
If you encounter import errors, check:
1. DI imports - remove them, DI system no longer exists
2. ModelCoordinator - may need to use services directly
3. Circular imports - common in model/ast modules

## Testing Guidelines

### Test Structure
```
tests/
├── unit/         # Unit tests for individual components
├── integration/  # Integration tests (may have import issues)
├── fixtures/     # Sample PowerBuilder files
└── benchmarks/   # Performance tests
```

### Running Specific Tests
```bash
# Test a specific module
uv run pytest tests/unit/decompile/ -v

# Skip slow tests
uv run pytest -m "not slow"

# Run with pattern matching
uv run pytest -k "test_pcode"
```

## Task Commands Reference

PowerRebuilder uses [Task](https://taskfile.dev) as its build automation tool (replaces Make).

```bash
# Core Development
task              # List all available tasks
task format       # Auto-format code (ruff, prettier)
task lint         # Lint code
task test         # Run tests
task coverage     # Generate coverage report
task type         # Type checking
task docs         # Build documentation

# Dependencies
task deps         # Install dependencies
task deps:update  # Update all dependencies

# CI/CD
task ci           # Run full CI pipeline
task security     # Security audit
task release      # Create a release

# Environment
task enter        # Initialize project environment
```

## Known Issues & Workarounds

1. **ModelCoordinator**: Now fixed - created `src/model/coordinator.py`
2. **DI Configuration Missing**: DI system was removed - use direct imports
3. **Task vs Make**: Use `task` commands instead of `make`
4. **Test Import Errors**: Missing base types fixed in `src/model/types/base.py`
5. **Parallel Processing**: Pipeline is sequential, files can be parallel within stages

## Performance Tips

- Use `--streaming` flag for large files
- Enable parallel file processing within stages: `--parallel --workers 8`
- P-code detection automatically segments large files for performance

## Getting Help

- Check GitHub issues: https://github.com/michaelprowacki/powerrebuilder/issues
- Issues are labeled with `claude-code` when created through Claude Code
- Priority areas: test coverage (#2), architecture refactoring (#3, #4)
