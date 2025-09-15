# PowerRebuilder Development Guide

This guide consolidates all active development documentation for the PowerRebuilder PowerBuilder reverse engineering project.

## Table of Contents

1. [Migration Guide](#migration-guide)
2. [Test Coverage Improvement](#test-coverage-improvement)
3. [File Naming Standards](#file-naming-standards)
4. [Code Quality Tools](#code-quality-tools)
5. [Future Architecture Plans](#future-architecture-plans)

---

## Migration Guide

This section helps developers update their code to work with the consolidated project structure.

### Quick Reference - Import Changes

| Old Import | New Import |
|------------|------------|
| `from src.model.ast.exception_handling import TryCatchStatement` | `from src.model.ast.exception_handling import TryCatchStatement` |
| `from src.common.types import validate_simple_type` | `from src.common.types import validate_simple_type` |
| `from src.parse.utils.grammar_loader import load_grammar` | `from src.parse.utils.grammar_loader import load_grammar` |
| `from src.parse.parsers.transaction import TransactionParser` | `from src.parse.parsers.transaction import TransactionParser` |
| `from src.extract.pbd_core.data_block import DataClass` | `from src.extract.pbd_core.data_block import DataClass` |

### Function Renames

| Old Function | New Function |
|--------------|--------------|
| `bin2int(data)` | `binary_to_int(data)` |
| `bin2time(data)` | `binary_to_time(data)` |

### Module Relocations

| Old Location | New Location | Notes |
|--------------|--------------|-------|
| `extract/pbd_core/library.py::calculate_content_hash` | `extract/pbd_io/utils.py` | Moved to utilities |
| `extract/pbd_core/core.py::save_to_file` | `extract/pbd_io/file_operations.py` | Consolidated file ops |
| `extract/pbd_core/library.py::load_pfc_hashes` | `extract/pbd_core/pfc_utils.py` | Extracted PFC utilities |

### Migration Examples

#### Update Exception Imports
```python
# Before
from src.model.ast.exception_handling import (
    TryCatchStatement,
    CatchBlock,
    ThrowStatement
)

# After
from src.model.ast.exception_handling import (
    TryCatchStatement,
    CatchBlock,
    ThrowStatement
)
```

#### Update Type System Imports
```python
# Before
from src.common.types import (
    validate_simple_type,
    get_pb_type_info,
    PBType
)

# After
from src.common.types import (
    validate_simple_type,
    get_pb_type_info,
    PBType
)
```

#### Update Parser Imports
```python
# Before
from src.parse.parsers.transaction import TransactionParser

# After
from src.parse.parsers.transaction import TransactionParser
```

---

## Test Coverage Improvement

### Current State
- **Line Coverage**: 1% (Critical)
- **File Coverage**: ~51% (54/106 source files have tests)
- **Test Files**: 85 (but most aren't running due to import errors)

### Root Causes
1. **Import Errors**: Module reorganization broke most test imports
2. **Configuration Issues**: pytest.ini restricts which tests run
3. **Outdated APIs**: Tests expect old interfaces that changed
4. **Missing Dependencies**: Some modules referenced in tests don't exist

### Improvement Strategy

#### Phase 1: Fix Existing Tests (Week 1)
**Goal**: Get from 1% to 30% coverage by fixing what we have

1. **Auto-fix Import Errors**
   ```bash
   # Run the automated fixer
   python scripts/maintenance/fix_test_coverage.py --fix-imports

   # Verify fixes
   python scripts/maintenance/fix_test_coverage.py --analyze
   ```

2. **Update pytest Configuration**
   Edit `pyproject.toml`:
   ```toml
   [tool.pytest.ini_options]
   # Remove or expand testpaths to include all tests
   testpaths = ["tests"]
   # Remove --maxfail=1 to see all failures
   addopts = "-ra --strict-markers --strict-config --cov --cov-branch --cov-report=term-missing --cov-report=html"
   ```

3. **Fix API Changes**
   - Change `error.details` to `error.context` in error handling tests
   - Update import paths for moved classes
   - Fix references to removed modules

#### Phase 2: Test Critical Components (Week 2)
**Goal**: Get from 30% to 60% coverage by testing core functionality

1. **Coordinator Tests** (Highest Priority)
   ```python
   # tests/test_coordinators/test_extract_coordinator.py
   def test_extract_coordinator_full_pipeline():
       """Test complete extraction pipeline."""
       coordinator = ExtractCoordinator()
       result = coordinator.extract_all("test_data/sample.pbl")
       assert result.success
       assert len(result.extracted_files) > 0
   ```

2. **Parser Tests**
   - Test each parser with valid and invalid input
   - Test error handling and recovery
   - Test grammar loading and caching

3. **Model Validation Tests**
   - Test AST node validation
   - Test type system validation
   - Test scope management

#### Phase 3: Integration Tests (Week 3)
**Goal**: Get from 60% to 80% coverage with end-to-end tests

1. **Full Pipeline Tests**
   ```python
   def test_full_reverse_engineering_pipeline():
       """Test complete PBL → Flutter conversion."""
       # Extract
       extracted = extract_coordinator.extract_all("sample.pbl")
       # Parse
       parsed = parse_coordinator.parse_all(extracted)
       # Model
       modeled = model_coordinator.build_models(parsed)
       # Decompile
       decompiled = decompile_coordinator.decompile_all(modeled)
       # Generate
       generated = generate_coordinator.generate_flutter(decompiled)
       assert generated.success
   ```

2. **Performance Tests**
   - Test with large PBL files
   - Measure memory usage
   - Profile bottlenecks

### Critical Files Needing Tests

| Module | Priority | Current Coverage | Target |
|--------|----------|------------------|---------|
| `extract_coordinator.py` | HIGH | 0% | 90% |
| `parse_coordinator.py` | HIGH | 0% | 90% |
| `model_coordinator.py` | HIGH | 0% | 85% |
| `decompile_coordinator.py` | HIGH | 0% | 85% |
| `generate_coordinator.py` | HIGH | 0% | 85% |
| `pcode_decoder.py` | MEDIUM | 15% | 80% |
| `expression_reconstructor.py` | MEDIUM | 20% | 80% |

---

## File Naming Standards

### Principles
1. **Clarity over brevity** - `cross_reference.py` not `crossref.py`
2. **Consistency** - Use same patterns across modules
3. **Avoid abbreviations** - `powerbuilder_` not `pb_`
4. **Descriptive names** - `exception_handling.py` not `exception.py`

### Recommended Renames

#### High Priority (Misleading Names)

| Current Name | Proposed Name | Reason |
|-------------|---------------|---------|
| `model/base/exception.py` | `model/ast/exception_handling.py` | Contains AST nodes for try-catch, not exceptions |
| `model/utils/type_system.py` | **DELETE** | Deprecated re-export module |
| `parse/grammar.py` | `parse/utils/grammar_loader.py` | Does more than just grammar - loads and parses types |

#### Medium Priority (Inconsistent Naming)

| Current Name | Proposed Name | Reason |
|-------------|---------------|---------|
| `parse/pb_preprocessor.py` | `parse/powerbuilder_preprocessor.py` | Consistency - avoid abbreviations |
| `extract/pbd_core/` | `extract/core/` | Redundant prefix - already in extract module |
| `extract/pbd_io/` | `extract/io/` | Redundant prefix |
| `parse/visitors/` | `parse/transformers/` | More accurate - they transform, not just visit |

#### Low Priority (Generic Names)

| Current Name | Proposed Name | Reason |
|-------------|---------------|---------|
| `*_coordinator.py` | `coordinator.py` | Since they're already in descriptive directories |
| `parse/base_parser.py` | `parse/parser_base.py` | Noun-first convention |
| `model/utils/base.py` | `model/utils/node_base.py` | More specific about what base it provides |

### Naming Conventions

1. **Files**: `snake_case.py`
2. **Classes**: `PascalCase`
3. **Functions**: `snake_case`
4. **Constants**: `UPPER_SNAKE_CASE`
5. **Private**: `_leading_underscore`

---

## Code Quality Tools

### Dead Code Detection with Vulture

We use Vulture to detect unused code. It's configured to reduce false positives from common patterns like visitor methods and parser parameters.

#### Running Vulture

```bash
# Quick check with our configuration
python scripts/check_dead_code.py

# Check specific module
python -m vulture src/parse/ .vulture_whitelist.py --min-confidence 80

# Verbose output
python -m vulture src/ .vulture_whitelist.py --min-confidence 80 --verbose
```

#### Configuration

- **pyproject.toml**: Contains ignore patterns and settings
- **.vulture_whitelist.py**: Dummy definitions for intentionally unused names
- **Confidence**: Set to 80% to reduce false positives

See [Dead Code Detection Guide](./DEAD_CODE_DETECTION.md) for detailed information.

### Other Quality Tools

```bash
# Type checking
mypy src/

# Linting and formatting
ruff check src/
ruff format src/

# Test coverage
pytest --cov=src tests/
```

---

## Future Architecture Plans

### Current Issues
1. Duplicate SQL parser implementations
2. Inconsistent naming conventions
3. Some modules doing too much (grammar.py)
4. Deprecated modules still present
5. Model coordinator not integrated with pipeline

### Proposed New Structure

```
powerrebuilder/
├── common/
│   ├── __init__.py
│   ├── exceptions.py          # Shared exception classes
│   ├── types.py               # Type definitions and validation
│   ├── pipeline.py            # Base pipeline coordinator
│   └── utils/
│       ├── __init__.py
│       ├── file_utils.py      # Common file operations
│       ├── string_utils.py    # String manipulation
│       └── validation.py      # Common validation functions
│
├── extract/
│   ├── __init__.py
│   ├── coordinator.py         # Main extraction coordinator
│   ├── core/                  # Core PBD functionality
│   │   ├── __init__.py
│   │   ├── structures/        # PBD data structures
│   │   ├── analysis/          # Analysis tools
│   │   └── utils/             # Extraction utilities
│   └── io/                    # I/O operations
│       ├── __init__.py
│       ├── file_operations.py
│       └── scanners.py
│
├── parse/
│   ├── __init__.py
│   ├── coordinator.py         # Main parsing coordinator
│   ├── parsers/               # Individual parsers
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── window.py
│   │   ├── datawindow.py
│   │   ├── menu.py
│   │   ├── function.py
│   │   ├── structure.py
│   │   ├── user_object.py
│   │   ├── application.py
│   │   ├── sql.py
│   │   └── transaction.py
│   ├── grammar/               # Grammar files
│   │   ├── powerbuilder.lark
│   │   ├── sql.lark
│   │   └── datawindow.lark
│   └── transformers/          # AST transformers
│       ├── __init__.py
│       ├── base.py
│       ├── powerbuilder.py
│       └── sql.py
│
├── model/
│   ├── __init__.py
│   ├── coordinator.py         # Model building coordinator
│   ├── ast/                   # AST node definitions
│   │   ├── __init__.py
│   │   ├── nodes.py
│   │   ├── types.py
│   │   ├── functions.py
│   │   └── statements.py
│   ├── entities/              # Domain entities
│   │   ├── __init__.py
│   │   ├── window.py
│   │   ├── datawindow.py
│   │   └── application.py
│   └── validation/            # Model validation
│       ├── __init__.py
│       └── validators.py
│
├── decompile/
│   ├── __init__.py
│   ├── coordinator.py         # Decompilation coordinator
│   ├── core/                  # Core decompilation
│   │   ├── __init__.py
│   │   ├── pcode_decoder.py
│   │   └── expression_reconstructor.py
│   └── analysis/              # Code analysis
│       ├── __init__.py
│       └── control_flow.py
│
└── generate/
    ├── __init__.py
    ├── coordinator.py         # Generation coordinator
    ├── backend/               # Backend generation
    │   ├── __init__.py
    │   ├── models.py
    │   └── services.py
    └── flutter/               # Flutter generation
        ├── __init__.py
        ├── screens.py
        └── widgets.py
```

### Key Improvements

1. **Common Module**: Shared utilities and base classes
2. **Consistent Structure**: Each module has a coordinator and clear subdirectories
3. **Clear Separation**: Parse/Transform/Generate phases are distinct
4. **No Redundancy**: Single implementation for each feature
5. **Better Organization**: Related functionality grouped together

### Migration Path

1. **Phase 1**: Create common module and move shared code
2. **Phase 2**: Reorganize extract module (pbd_core → core, pbd_io → io)
3. **Phase 3**: Consolidate parsers and fix hierarchy
4. **Phase 4**: Integrate model coordinator with pipeline
5. **Phase 5**: Clean up and remove deprecated code

### Benefits

- **Easier Testing**: Clear module boundaries
- **Better Maintainability**: Logical organization
- **Reduced Duplication**: Common patterns extracted
- **Clearer Pipeline**: Each phase has clear inputs/outputs
- **Extensibility**: Easy to add new parsers or generators

---

## Development Workflow

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/powerrebuilder.git
cd powerrebuilder

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
mypy .
```

### Code Style Guidelines

1. **Type Hints**: Use type hints for all function signatures
2. **Docstrings**: Google-style docstrings for all public functions
3. **Comments**: Explain "why" not "what"
4. **Line Length**: 88 characters (Black default)
5. **Imports**: Sorted with `isort`

### Commit Guidelines

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test additions or fixes
- `chore:` Build process or auxiliary tool changes

### Pull Request Process

1. Create feature branch from `main`
2. Make changes following style guidelines
3. Add/update tests
4. Update documentation
5. Run full test suite
6. Submit PR with clear description

---

## Troubleshooting

### Common Issues

#### Import Errors After Refactoring
```python
# If you see: ImportError: cannot import name 'Parser' from 'parse.transaction_parser'
# Solution: Update to new import path
from src.parse.parsers.transaction import TransactionParser
```

#### Test Discovery Issues
```bash
# If pytest can't find tests
pytest --collect-only  # See what pytest finds
pytest tests/  # Explicitly specify test directory
```

#### Grammar Loading Errors
```python
# If grammar files aren't found
# Check GRAMMAR_DIR is set correctly
from src.parse.utils.grammar_loader import GRAMMAR_DIR
print(GRAMMAR_DIR)  # Should point to src/parse/grammar/
```

### Getting Help

1. Check this guide first
2. Search existing issues on GitHub
3. Ask in development chat/forum
4. Create detailed issue with reproduction steps
