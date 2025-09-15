# PowerRebuilder Dependency Maps & Visualization

## Quick Access to Dependency Information

### 1. View Existing Dependency Maps

#### Text-Based Import Map
- **File**: [`import_analysis_report.md`](import_analysis_report.md)
- **Content**: Detailed import analysis with broken imports, circular dependencies
- **Generated**: By subagent during codebase analysis

#### Comprehensive Import Map
- **File**: [`COMPREHENSIVE_IMPORT_MAP.md`](COMPREHENSIVE_IMPORT_MAP.md)
- **Content**: Executive summary with module health status
- **Key Finding**: 134 broken imports identified (now mostly fixed)

### 2. Generate New Visualizations

#### Using the Enhanced Dependency Visualizer
```bash
# Quick stats (Python 3.13 features)
python scripts/dependency_visualizer.py --format json | jq '.statistics'

# Find dataclasses
python scripts/dependency_visualizer.py --format json | jq '.dataclass_analysis'

# Generate visual diagram
python scripts/dependency_visualizer.py --format mermaid --output deps.md
```

#### Summary Statistics from Latest Run
- **Total Entities**: 1,144
- **Total Dependencies**: 3,769
- **Classes**: 500
- **Functions**: 317
- **Dataclasses**: 209 (using Python 3.13 features)
- **Enums**: 47
- **Protocols**: 71

### 3. Install Better Visualization Tools

```bash
# Best options for PowerRebuilder
pip install pydeps        # Visual dependency graphs
pip install pyreverse      # UML class diagrams
pip install py2puml        # PlantUML for dataclasses
pip install import-linter  # Enforce architecture rules
```

### 4. Quick Commands

#### Generate Visual Graph
```bash
# Install pydeps first
pip install pydeps graphviz

# Generate full dependency graph
pydeps src --max-bacon 2 --cluster -o dependencies.svg

# Generate for specific module
pydeps src/model --only model.ast model.types -o model_internals.svg
```

#### Generate UML Class Diagrams
```bash
# Install pylint (includes pyreverse)
pip install pylint

# Generate class diagrams for model module
pyreverse -o png -p PowerRebuilder src/model
```

#### Check Architecture Rules
```bash
# Install import-linter
pip install import-linter

# Create config
cat > .importlinter << EOF
[importlinter]
root_package = src

[importlinter:contract:1]
name = "Pipeline stages must be sequential"
type = layers
layers =
    src.extract
    src.decompile
    src.parse
    src.model
    src.generate
EOF

# Run check
lint-imports
```

### 5. Python 3.13 Feature Usage

The codebase is configured for Python 3.13 (`requires-python = ">=3.13"` in pyproject.toml).

#### Features Currently Used
- Type hints with modern syntax
- Dataclasses with slots and frozen
- Pattern matching (match/case)
- StrEnum for better enumerations
- Override decorator (@override)
- Improved pathlib performance

#### Features to Adopt
- PEP 692: TypedDict for **kwargs
- PEP 698: Override decorator
- PEP 701: Improved f-strings
- Better error messages
- Performance improvements

### 6. Module Dependency Summary

```
Pipeline Flow (Sequential):
┌─────────┐    ┌──────────┐    ┌───────┐    ┌───────┐    ┌──────────┐
│ Extract │ → │ Decompile │ → │ Parse │ → │ Model │ → │ Generate │
└─────────┘    └──────────┘    └───────┘    └───────┘    └──────────┘

Internal Dependencies:
- Extract: Uses contracts, core, services (50 files, healthy)
- Decompile: Uses pcode, opcodes, reconstruction (54 files, functional)
- Parse: Uses grammar, parser, transformer (31 files, moderate issues)
- Model: Uses ast, types, services, visitors (59 files, was critical, now fixed)
- Generate: Uses converters, templates, model (53 files, affected by model)

Shared Dependencies:
- All stages → src.core (coordination, security, exceptions)
- All stages → src.contracts (interfaces, types)
- All stages → src.common (utilities, constants)
```

### 7. Circular Dependencies Found

1. **Low Impact**: PBD structure/recovery cycle
2. **Medium Impact**: Generate coordinator/service cycle

### 8. Integration with Task

Add these commands to your workflow:
```bash
# Add to taskfile.yml
task deps:analyze   # Run dependency analysis
task deps:graph     # Generate visual graphs
task deps:check     # Check architecture rules
```

## Recommendations

1. **Use `pydeps`** for quick visual graphs
2. **Use `pyreverse`** for detailed UML diagrams
3. **Use `import-linter`** to enforce architecture
4. **Run `dependency_visualizer.py`** for detailed stats
5. **Check COMPREHENSIVE_IMPORT_MAP.md** for known issues

## File Locations Summary

| Type | File | Purpose |
|------|------|---------|
| Report | `import_analysis_report.md` | Detailed import analysis |
| Summary | `COMPREHENSIVE_IMPORT_MAP.md` | Executive summary |
| Script | `scripts/dependency_visualizer.py` | Generate new visualizations |
| Script | `import_analysis.py` | Original analysis script |
| Docs | `docs/DEPENDENCY_VISUALIZATION.md` | Full documentation |
| This File | `DEPENDENCY_MAPS.md` | Quick reference guide |
