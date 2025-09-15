# PowerRebuilder

[![GitHub Issues](https://img.shields.io/github/issues/michaelprowacki/powerrebuilder)](https://github.com/michaelprowacki/powerrebuilder/issues)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](https://github.com/michaelprowacki/powerrebuilder/blob/main/LICENSE)

Reverse engineering toolkit that transforms compiled PowerBuilder applications into modern codebases.

## What It Does

PowerRebuilder takes compiled PowerBuilder PBL/PBD files and:
1. **Extracts** the compiled P-code bytecode
2. **Decompiles** P-code back to PowerBuilder source
3. **Parses** source into Abstract Syntax Trees (AST)
4. **Models** the application structure and semantics
5. **Generates** modern code in your target language

### Current Output Targets
- **Python** - Using Litestar framework for web applications
- **Dart/Flutter** - For cross-platform mobile and web apps

### Planned Features
- Plugin architecture for custom output targets
- Additional language targets (TypeScript/React, C#/.NET, Java/Spring)
- Intermediate representation (IR) for better transformation flexibility

## Installation

```bash
# Clone the repository
git clone https://github.com/michaelprowacki/powerrebuilder.git
cd powerrebuilder

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

## Usage

### Basic Usage
```bash
# Full pipeline - PBL to modern code
python main.py all input.pbl output/

# Individual stages (must run in order)
python main.py extract input.pbl output/extracted/
python main.py decompile output/extracted/ output/decompiled/
python main.py parse output/decompiled/ output/parsed/
python main.py model output/parsed/ output/models/
python main.py generate output/models/ output/generated/
```

### Choose Output Target
```bash
# Generate Python/Litestar application
python main.py generate output/models/ output/ --target python

# Generate Dart/Flutter application
python main.py generate output/models/ output/ --target flutter
```

## Architecture

PowerRebuilder uses a multi-stage pipeline with intermediate representations:

```
PBL/PBD → P-code → PowerScript → AST → Semantic Model → Target Code
```

### Key Components

- **P-code Decompiler**: Reconstructs PowerScript from compiled bytecode
- **Lark Parser**: Grammar-based parsing of PowerScript syntax
- **AST Builder**: Creates language-agnostic abstract syntax trees
- **Semantic Analyzer**: Resolves types, dependencies, and control flow
- **Code Generators**: Template-based generation for each target language

### Transformation Strategy

1. **AST-based transformation**: Direct mapping of PowerBuilder constructs to target language equivalents
2. **Semantic preservation**: Maintains business logic while adapting to modern patterns
3. **Framework integration**: Generated code uses modern frameworks (Litestar, Flutter) instead of direct PowerBuilder UI translation

## Development

### Running Tests
```bash
# Run all tests
uv run pytest

# Run specific module tests
uv run pytest tests/unit/decompile/

# Run with coverage
uv run pytest --cov=src
```

### Code Quality
```bash
# Linting
uv run ruff check .

# Formatting
uv run ruff format .

# Type checking
uv run mypy src/
```

## Contributing

See [open issues](https://github.com/michaelprowacki/powerrebuilder/issues) for areas where help is needed:

- Test coverage improvements (#2)
- Architecture refactoring (#3, #4)
- Additional language targets
- Grammar improvements for edge cases
- Documentation and examples

## Project Status

This is an active research project for reverse engineering PowerBuilder applications. While functional for many use cases, it may not handle all PowerBuilder features yet.

### Supported PowerBuilder Features
- DataWindows (basic)
- Windows and user objects
- Functions and events
- SQL statements
- Basic control structures

### Limitations
- Complex DataWindow expressions may need manual adjustment
- Some PowerBuilder-specific features have no direct equivalent in modern frameworks
- PFC (PowerBuilder Foundation Classes) support is partial

## License

Apache License 2.0 - See [LICENSE](LICENSE) file for details.

## Acknowledgments

Built with:
- [Lark Parser](https://github.com/lark-parser/lark) for grammar-based parsing
- [Jinja2](https://jinja.palletsprojects.com/) for code generation templates
- PowerBuilder community for format documentation
