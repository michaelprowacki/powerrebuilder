# PowerRebuilder Comprehensive Import Map

## Executive Summary

This document provides a complete analysis of the PowerRebuilder codebase's import structure, identifying broken imports, circular dependencies, and providing a dependency graph to understand the architecture.

### Key Findings

- **289 Python files** analyzed across all modules
- **134 broken imports** found (46% of all imports issues)
- **2 circular dependency cycles** detected
- **Major architectural issues** in the model module preventing system functionality

## Critical Issues Requiring Immediate Attention

### 1. Missing Core Base Module (`src.model.types.base`)

**Impact**: CASCADE FAILURE - 25 files cannot import, preventing entire model module from functioning

**Root Cause**: The file `src/model/types/base.py` is missing but referenced by:
- `src/model/types/__init__.py` (line 3)
- `src/model/constructs/pb_access.py` (line 12)
- 23+ other critical model files

**Expected Contents**: Based on import patterns, this file should contain:
```python
# src/model/types/base.py
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional

class NodeKind(Enum):
    """PowerBuilder node types."""
    FUNCTION = auto()
    CLASS = auto()
    VARIABLE = auto()
    # ... other types

@dataclass
class PBNode:
    """Base class for PowerBuilder AST nodes."""
    kind: NodeKind
    name: str
    line: Optional[int] = None

    def accept_visitor(self, visitor):
        """Accept visitor pattern."""
        pass

@dataclass
class SourceAnchor:
    """Source code location information."""
    file: str
    line: int
    column: int
```

### 2. Missing Model Infrastructure Files

**Missing Files Referenced in Git Status**:
- `src/model/ast/literals.py`
- `src/model/ast/node_kind.py`
- `src/model/ast/nodes/expressions.py`
- `src/model/ast/nodes/literals.py`
- `src/model/ast/nodes/variables.py`
- `src/model/base/pb_entity.py`
- `src/model/coordinator.py`
- `src/model/factory.py`
- `src/model/interfaces.py`
- `src/model/model_coordinator.py`
- `src/model/types/base.py`
- `src/model/types/decompile.py`
- `src/model/types/errors.py`
- `src/model/types/interfaces.py`
- `src/model/types/powerbuilder.py`
- `src/model/types/stubs.pyi`
- `src/model/visitors/ast_tree_visitor.py`
- `src/model/visitors/ast_walker.py`
- `src/model/visitors/model_extractor_visitor.py`

## Module-by-Module Import Analysis

### EXTRACT Module (50 files)
**Status**: ✅ Generally healthy
**Top Dependencies**:
- Internal: `src` (195 imports)
- External: `typing` (60), `logging` (38), `pathlib` (33)

**Key Import Patterns**:
```python
# Coordinator pattern
from src.extract.coordinator import ExtractCoordinator
from src.extract.components.orchestrator import ExtractionOrchestrator

# PBD file handling
from src.extract.pbd.library import Library
from src.extract.pbd.structures import extract_nods, extract_pbl_header
```

### DECOMPILE Module (54 files)
**Status**: ⚠️ Some broken imports but functional
**Top Dependencies**:
- Internal: `src` (138 imports)
- External: `typing` (62), `dataclasses` (46), `logging` (38)

**Broken Imports**:
- Missing: `analysis.control`, `analyzers.parser`, `extractors.datawindow`
- Impact: Some advanced decompilation features may fail

### PARSE Module (31 files)
**Status**: ⚠️ Moderate issues
**Top Dependencies**:
- Internal: `src` (133 imports)
- External: `lark` (34), `typing` (31), `logging` (18)

**Broken Imports**:
- Missing: `grammar.loader`, `parser.base`, `preprocessor.imports`
- Impact: Parser coordination and grammar loading affected

### MODEL Module (59 files)
**Status**: 🚨 CRITICAL - CASCADE FAILURES
**Top Dependencies**:
- Internal: `src` (107 imports)
- External: `typing` (70), `dataclasses` (45)

**Critical Issues**:
- **25 files** cannot import due to missing `src.model.types.base`
- **4 files** missing `src.model.interfaces`
- Entire module ecosystem broken

### GENERATE Module (53 files)
**Status**: ⚠️ Affected by model issues
**Top Dependencies**:
- Internal: `src` (96 imports)
- External: `typing` (45), `logging` (36)

**Impact**: Cannot generate code because model imports fail

## Circular Dependencies

### Cycle 1: PBD Structure/Recovery
```
src.extract.pbd.structures → src.extract.pbd.recovery → src.extract.pbd.structures
```
**Impact**: Low - isolated to extraction recovery logic

### Cycle 2: Generate Coordinator/Service
```
src.generate.coordinator → src.generate.coordinators.service → src.generate.coordinator
```
**Impact**: Medium - affects code generation coordination

## Dependency Graph

### Inter-Module Dependencies

```
EXTRACT ──→ COMMON, CONTRACTS, CORE
    ↓
DECOMPILE ──→ CONTRACTS, CORE, EXTRACT, MODEL, PARSE
    ↓
PARSE ──→ COMMON, CONTRACTS, CORE, EXTRACT, MODEL
    ↓
MODEL ──→ CORE, DECOMPILE
    ↓
GENERATE ──→ CONTRACTS, CORE, MODEL, PARSE
```

### Critical Dependency Chain

The system follows a **sequential pipeline architecture**:

1. **EXTRACT** → Extracts P-code from PBL/PBD files
2. **DECOMPILE** → Converts P-code to PowerBuilder source
3. **PARSE** → Creates AST from source code
4. **MODEL** → Builds semantic models from AST
5. **GENERATE** → Produces modern code from models

**Current Failure Point**: Step 4 (MODEL) is completely broken due to missing base types, causing steps 4-5 to fail.

## Import Categories by Risk Level

### 🚨 Critical (System Breaking)
- `src.model.types.base` - **25 files affected**
- `src.model.interfaces` - **4 files affected**
- `src.model.ast.*` family - **20+ files affected**

### ⚠️ High (Feature Breaking)
- `extractors.datawindow` - DataWindow processing affected
- `grammar.loader` - Parser grammar loading affected
- Various specialized parsers and processors

### ⚡ Medium (Functionality Degraded)
- Missing utility modules
- Optional enhancement features
- Advanced analysis capabilities

### ✅ Low (Non-Critical)
- Missing external dependencies (ray, celery)
- Development/debugging tools
- Performance optimizations

## Recommended Fix Priority

### Phase 1: Restore Core Model Module (URGENT)
1. Create `src/model/types/base.py` with `PBNode`, `NodeKind`, `SourceAnchor`
2. Create `src/model/interfaces.py` with core interfaces
3. Create missing AST node files:
   - `src/model/ast/literals.py`
   - `src/model/ast/node_kind.py`
   - `src/model/ast/nodes/expressions.py`
   - `src/model/ast/nodes/literals.py`
   - `src/model/ast/nodes/variables.py`

### Phase 2: Complete Model Infrastructure
1. Create `src/model/base/pb_entity.py`
2. Create `src/model/coordinator.py`
3. Create `src/model/factory.py`
4. Add missing visitor files

### Phase 3: Fix Module-Specific Issues
1. Resolve decompile extractor imports
2. Fix parse coordinator issues
3. Address generate coordination problems

### Phase 4: Resolve Circular Dependencies
1. Refactor PBD structure/recovery cycle
2. Separate generate coordinator concerns

## Test Impact Analysis

**Current Status**: Tests cannot run for model module due to import failures

**Affected Test Suites**:
- `tests/unit/model/` - All tests fail to import
- `tests/integration/` - Pipeline tests fail at model stage
- `tests/unit/generate/` - Code generation tests fail
- Any tests importing model classes

**Expected Resolution**: Once Phase 1 fixes are implemented, approximately 80% of import issues should be resolved, allowing the test suite to run and identify remaining functional issues.

## Architecture Insights

### Strong Points
1. **Clear separation of concerns** - Each module has distinct responsibilities
2. **Sequential pipeline design** - Natural data flow from extract → generate
3. **Comprehensive feature coverage** - Rich decompilation and generation capabilities

### Weak Points
1. **Fragile dependency management** - Missing core files break entire system
2. **Tight coupling** - Model module affects everything downstream
3. **Incomplete module isolation** - Circular dependencies indicate design issues

### Recommendations
1. **Implement interface segregation** - Reduce tight coupling between modules
2. **Add dependency injection** - Make dependencies explicit and testable
3. **Create stable base abstractions** - Ensure core types are never missing
4. **Add import verification CI** - Prevent broken imports from being committed

---

*Generated by comprehensive import analysis - see `import_analysis_report.md` for detailed technical data*
