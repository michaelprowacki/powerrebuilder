# PowerRebuilder Architecture

## System Overview

PowerRebuilder is a reverse engineering toolkit that transforms compiled PowerBuilder applications into modern codebases through a **five-stage sequential pipeline**.

## Pipeline Architecture

```
PBL/PBD → Extract → Decompile → Parse → Model → Generate → Modern Code
         (P-code)   (Source)    (AST)   (Models)         (Flutter/Python)
```

### Stage Dependencies
Each stage **MUST** run in order as each depends on the previous stage's output:
- Extract produces P-code files that Decompile needs
- Decompile produces source files that Parse needs
- Parse produces AST that Model needs
- Model produces semantic models that Generate needs

## Stage 1: Extract

### Purpose
Extracts compiled P-code and resources from PowerBuilder PBL/PBD archives.

### Key Components
- **`ExtractCoordinator`**: Main orchestrator
- **`BinaryFileParser`**: Parses PBL/PBD binary structure
- **`Library`**: PowerBuilder version detection (6.0-12.5)
- **`ResourceExtractor`**: Extracts embedded resources

### Process
1. Detect PowerBuilder version and encoding (ASCII/Unicode)
2. Parse binary headers and node structures
3. Extract individual objects as `.fun` files (P-code)
4. Extract embedded resources (images, audio, etc.)

### Output
- P-code files (`.fun`) containing compiled bytecode
- Resource files (images, audio, binary data)
- Metadata about extracted objects

## Stage 2: Decompile

### Purpose
Reconstructs PowerBuilder source code from P-code bytecode.

### Key Components
- **`DecompileCoordinator`**: Main orchestrator
- **P-code Detection** (tiered system):
  - `HighPerformancePCodeDetector`: O(n) Boyer-Moore pattern matching
  - `TieredPCodeDetector`: 4-tier progressive detection
- **`PCodeDecoderV2`**: Version-aware opcode decoder
- **`EnhancedExpressionReconstructor`**: Stack-to-expression conversion

### Process
1. Detect P-code boundaries in binary files
2. Decode opcodes (256 for PB 6.0, 594 for PB 8.0+)
3. Reconstruct control flow (if/while/for/case)
4. Lift stack operations to expressions
5. Generate PowerBuilder source syntax

### Output
PowerBuilder source files:
- `.sru` (user objects)
- `.srw` (windows)
- `.srm` (menus)
- `.srd` (DataWindows)

## Stage 3: Parse

### Purpose
Transforms PowerBuilder source into Abstract Syntax Trees (ASTs).

### Key Components
- **`ParseCoordinator`**: Main orchestrator
- **`GrammarManager`**: Loads and caches Lark grammars
- **`EnhancedPowerBuilderParser`**: Main parser with error recovery
- **`PowerBuilderPreprocessor`**: Source cleanup
- **`PowerBuilderTransformer`**: Parse tree to AST conversion

### Grammar System
- EBNF grammars in `src/parse/grammar/definitions/`
- Modular design with separate grammars for different constructs
- Lark parser with Earley algorithm for robustness

### Process
1. Preprocess source (remove headers, handle continuations)
2. Parse with appropriate grammar based on file type
3. Transform parse tree to semantic AST
4. Apply error recovery for malformed code
5. Serialize AST to JSON

### Output
JSON files containing:
- Structured AST representation
- Source location information
- Metadata about parsed objects
- Error/warning information

## Stage 4: Model

### Purpose
Builds semantic models from ASTs with resolved types and dependencies.

### Key Components
- **`ASTProcessor`**: Loads and processes AST files
- **`ModelExtractorVisitor`**: Extracts semantic information
- **`TypeRegistry`**: Manages PowerBuilder type system
- **`CrossModuleReferenceResolver`**: Resolves inter-module dependencies

### Type System
- Basic types (integer, string, boolean, etc.)
- Custom types with inheritance
- Array types with bounds
- DataWindow types
- Parameterized types

### Process
1. Load AST JSON files
2. Extract semantic entities (functions, variables, events)
3. Resolve type references
4. Build symbol tables
5. Resolve cross-module dependencies

### Output
Semantic models containing:
- Resolved type information
- Dependency graphs
- Symbol tables
- Method/event signatures

## Stage 5: Generate

### Purpose
Generates modern application code from semantic models.

### Key Components
- **`GenerateCoordinator`**: Main orchestrator
- **Template Engine**: Jinja2-based code generation
- **Converters**:
  - `UIConverter`: PowerBuilder controls → Flutter widgets
  - `TypeConverter`: Type system mapping
  - `EventConverter`: Event handling transformation
  - `ExpressionConverter`: Expression translation

### Target Platforms

#### Flutter/Dart
- Complete mobile applications
- Glassmorphism design system
- Material Design widgets
- State management with Provider

#### Python/Litestar
- Web APIs with SQLModel
- Pydantic data models
- Service layer architecture
- Database integration

### Process
1. Load semantic models
2. Apply transformation rules
3. Generate code using templates
4. Organize output structure
5. Apply formatting and validation

### Output Structure
```
flutter/
├── lib/
│   ├── screens/      # UI screens
│   ├── widgets/      # Custom widgets
│   ├── models/       # Data models
│   └── services/     # Business logic
└── pubspec.yaml

python/
├── models/           # SQLModel classes
├── services/         # Business logic
└── api/             # API endpoints
```

## Design Decisions

### Sequential Pipeline
- Simplifies data flow and debugging
- Each stage has clear input/output contracts
- Enables incremental processing and caching

### No Dependency Injection
- Direct imports for simplicity
- Factory pattern for complex object creation
- Services composed explicitly

### Grammar-Based Parsing
- Maintainable grammar definitions
- Robust error recovery
- Extensible for new PowerBuilder features

### Template-Based Generation
- Separation of logic and presentation
- Easy to add new target platforms
- Consistent code formatting

## Performance Optimizations

### P-code Detection
- Tiered detection for performance/accuracy tradeoff
- File segmentation for large files
- Pattern caching for repeated structures

### Parsing
- Grammar caching to avoid recompilation
- Parallel file processing within stages
- Error recovery to continue on failures

### Generation
- Template compilation caching
- Streaming output for large projects
- Parallel file generation

## Extension Points

### Adding New PowerBuilder Features
1. Update grammar in `src/parse/grammar/`
2. Add AST nodes in `src/model/ast/`
3. Update visitors in `src/model/visitors/`
4. Add converters in `src/generate/converters/`
5. Create templates in `src/generate/templates/`

### Adding New Target Platforms
1. Create generator in `src/generate/coordinators/`
2. Implement converters for type/expression mapping
3. Add templates for code generation
4. Register in factory

## Limitations

### PowerBuilder Support
- Versions 6.0-12.5 supported
- Some advanced features may not be fully supported
- PFC (PowerBuilder Foundation Classes) partial support

### Code Generation
- Some PowerBuilder patterns have no direct equivalent
- Manual adjustment may be needed for complex logic
- DataWindow expressions require special handling

### Performance
- Large files may require significant memory
- Sequential pipeline limits parallelization
- P-code detection can be slow for corrupted files
