# Critical Issues & Priority Fixes

## 🚨 Critical Issues (Must Fix)

### 1. Incomplete P-Code Decompilation
**Impact:** Core functionality broken
**Files:** `decompile/pcode_decoder.py`, `decompile/decompile_structured.py`

**What's Missing:**
- Stack simulation for expression evaluation
- Control flow graph construction
- Pattern matching for high-level constructs
- Method invocation handling

**Fix Priority:** IMMEDIATE
**Estimated Effort:** 2-3 weeks

### 2. Parser-Model Disconnection
**Impact:** Parse phase output unusable
**Files:** `parse/visitors/pb_transformer.py`

**What's Missing:**
- Transformer doesn't create model objects
- Grammar rules not mapped to AST nodes
- No semantic validation

**Fix Priority:** HIGH
**Estimated Effort:** 1 week

### 3. Type Annotations Missing
**Impact:** Type safety compromised, IDE support limited
**Files:** Throughout codebase

**What's Missing:**
- Function signatures lack type hints
- Class attributes untyped
- Generic types not specified

**Fix Priority:** HIGH
**Estimated Effort:** 1 week (can be parallelized)

## 🔴 High Priority Issues

### 4. Hardcoded Paths in Generation
**Files:** `generate/code_generator.py`
```python
# Current (BAD):
def generate_models():
    input_path = "output/parsed"  # Hardcoded!

# Should be:
def generate_models(input_path: Path, output_path: Path):
    # Use provided paths
```

### 5. Large Function Complexity
**Files:** `extract/pbd_core/library.py`
- `Library.__init__` - 200+ lines
- Needs refactoring into smaller methods

### 6. Security: Unsafe YAML Loading
**Files:** `add_missing_opcodes.py`
```python
# Current:
yaml.load(stream, OrderedLoader)  # Unsafe!

# Should be:
yaml.safe_load(stream)  # With custom constructors
```

## 🟡 Medium Priority Issues

### 7. Low Test Coverage (28.35%)
- Missing integration tests
- No decompiler tests
- Limited edge case coverage

### 8. Memory Management
- Entire files loaded into memory
- No streaming support for large files
- Potential memory leaks with circular references

### 9. Performance Bottlenecks
- Single-threaded processing
- No caching layer
- Repeated I/O operations

## 🟢 Lower Priority Issues

### 10. Documentation Gaps
- Missing API documentation
- No user guide
- Limited examples

### 11. Developer Experience
- No debugging tools
- Limited error messages
- No progress persistence

### 12. Code Smells
- Magic numbers scattered
- Inconsistent logging
- Dead code present

## Quick Wins (Can Fix Today)

1. **Add Type Annotations to Core Functions**
```python
# Add to main.py and core modules
from pathlib import Path
from typing import List, Optional, Dict
```

2. **Extract Magic Numbers**
```python
# Create constants.py
BLOCK_SIZE_256 = 256
BLOCK_SIZE_512 = 512
BLOCK_SIZE_1024 = 1024
VALID_BLOCK_SIZES = [BLOCK_SIZE_256, BLOCK_SIZE_512, BLOCK_SIZE_1024]
```

3. **Fix Security Issues**
- Replace unsafe yaml.load
- Add path validation
- Sanitize inputs

## Recommended Fix Order

### Week 1: Foundation
1. ✅ Set up CI/CD pipeline
2. ✅ Add type annotations to core modules
3. ✅ Fix security issues
4. ✅ Extract magic numbers

### Week 2-3: Core Functionality
1. 🔨 Complete P-Code stack simulation
2. 🔨 Implement control flow analysis
3. 🔨 Connect parser to model

### Week 4: Testing & Quality
1. 📝 Write integration tests
2. 📝 Increase coverage to 50%
3. 📝 Refactor large functions

### Week 5-6: Polish
1. 🎨 Fix generation hardcoding
2. 🎨 Improve error handling
3. 🎨 Update documentation

## Success Metrics

- [ ] P-Code decompiler can handle basic functions
- [ ] Parser produces valid AST nodes
- [ ] Type checking passes with --strict
- [ ] Test coverage > 50%
- [ ] No hardcoded paths
- [ ] All security issues resolved

## Resource Allocation

**Developer 1:** P-Code decompilation (full time)
**Developer 2:** Parser integration + Type annotations
**Developer 3:** Testing + Documentation

## Notes for Next Session

When continuing work, start with:
1. Check `test_pcode/` for P-Code samples
2. Review `opcodes.yaml` for instruction definitions
3. Look at `model/ast/` for target AST structure
4. Use `extract/pbd_core/` as example of good practices

The most critical issue is completing the P-Code decompiler. Without it, the tool cannot fulfill its primary purpose of converting PowerBuilder to modern code.
