# PowerRebuilder: Complete Technical Guide

## Table of Contents
1. [Executive Overview](#executive-overview)
2. [System Architecture](#system-architecture)
3. [The Five-Stage Pipeline](#the-five-stage-pipeline)
4. [PowerBuilder Concepts](#powerbuilder-concepts)
5. [Code Generation Targets](#code-generation-targets)
6. [Technical Deep Dives](#technical-deep-dives)
7. [Development Guide](#development-guide)
8. [Real-World Usage](#real-world-usage)
9. [Code Examples](#code-examples)
10. [Reference Section](#reference-section)

---

## Executive Overview

### What is PowerRebuilder?

PowerRebuilder is a sophisticated reverse engineering toolkit that transforms compiled PowerBuilder applications into modern codebases. It addresses the critical business need of migrating legacy PowerBuilder systems—many of which are decades old and mission-critical—to contemporary technology stacks without losing functionality or business logic.

### The Problem It Solves

PowerBuilder, once a dominant RAD (Rapid Application Development) tool from the 1990s-2000s, has left thousands of organizations with legacy applications that are:
- Difficult to maintain (declining PowerBuilder expertise)
- Expensive to license
- Incompatible with modern deployment models (cloud, mobile, web)
- Trapped in proprietary binary formats (PBL/PBD files)

PowerRebuilder liberates these applications by:
1. **Extracting** compiled bytecode from proprietary binaries
2. **Decompiling** bytecode back to source code
3. **Parsing** source into abstract syntax trees (ASTs)
4. **Building** semantic models with resolved types and dependencies
5. **Generating** modern application code in multiple target languages

### Key Capabilities

- **Multi-version support**: PowerBuilder 6.0 through 12.5
- **Format handling**: Both PBL (libraries) and PBD (dynamic libraries)
- **Complete transformation**: From binary to deployable modern applications
- **Multiple targets**: Flutter (mobile), Python/Litestar (web APIs), Rust/Tauri (desktop), and more
- **Preservation**: Maintains business logic, UI structure, and data relationships

### Real-World Application

The project includes test data from a complete Dental Clinic Management (DCM) system with 54 modules covering:
- Patient management (`dcm_patient.pbd`)
- Appointment scheduling (`dcm_appointments.pbd`)
- Billing and accounting (`dcm_billing.pbd`, `dcm_accounting.pbd`)
- Insurance processing (`dcm_hicaps.pbd`)
- And 50+ other modules totaling ~70MB of compiled PowerBuilder code

---

## System Architecture

### Project Structure

```
powerrebuilder/
├── main.py                 # Primary CLI entry point (71KB, 1900+ lines)
├── src/                    # Original implementation (68 Python files)
│   ├── extract/           # Binary extraction stage
│   ├── decompile/         # P-code decompilation
│   ├── parse/             # Grammar-based parsing
│   ├── model/             # Semantic modeling
│   ├── generate/          # Code generation
│   └── adapters/          # Various adapters and utilities
├── src_new/               # Refactored implementation (62 Python files)
│   ├── _core/            # Core models and types
│   ├── _patterns/        # Reusable abstractions
│   ├── extract/          # Enhanced extraction
│   ├── decompile/        # Improved decompilation
│   ├── parse/            # Parser with better error recovery
│   ├── model/            # Advanced semantic analysis
│   ├── generate/         # Multi-target generation
│   └── ai/               # AI-assisted code understanding
├── data/
│   └── pbd_files/        # 54 DCM system modules
├── tests/                # Comprehensive test suite
│   ├── fixtures/         # Sample PowerBuilder files
│   ├── unit/            # Unit tests
│   └── integration/     # Integration tests
├── docs/                 # Architecture and API documentation
└── output/              # Generated code output
```

### Dual Implementation Strategy

The project maintains two parallel implementations:

**`src/` - Original Implementation**
- Battle-tested with real-world files
- Complex adapter pattern architecture
- Some technical debt from iterative development
- ~68 Python modules

**`src_new/` - Refactored Implementation**
- Cleaner architecture with extracted patterns
- Better separation of concerns
- Enhanced error handling and observability
- ~62 Python modules

Both implementations share the same five-stage pipeline concept but differ in internal organization.

### Core Abstractions (`src_new/_patterns/`)

The refactored implementation extracts common patterns into reusable components:

```python
# Base coordinator for all pipeline stages
class BaseCoordinator(ABC):
    """Abstract base for pipeline stage coordinators."""

    def process(self) -> CoordinatorResult:
        """Process all files in the input directory."""
        files = self.discover_files()
        for file in files:
            success = self.process_file(file, self.output_path)
            # Track success/failure
        return CoordinatorResult(...)

# Binary file operations
class BinaryReader:
    """Unified binary file reader with all common operations."""

    def read_uint32(self) -> int:
        """Read unsigned 32-bit integer."""
        return self.read_struct("I")[0]

    def find_pattern(self, pattern: bytes) -> int:
        """Find byte pattern in file."""
        # Boyer-Moore pattern matching
```

### Design Philosophy

1. **Sequential Pipeline**: Each stage must complete before the next begins
2. **No Dependency Injection**: Direct imports for simplicity
3. **Grammar-Based Parsing**: Maintainable EBNF grammars
4. **Template-Based Generation**: Jinja2 templates for code generation
5. **Version Awareness**: Different handling for PowerBuilder versions
6. **Error Recovery**: Continue processing despite individual file failures

---

## The Five-Stage Pipeline

### Stage 1: Extract - Binary Archaeology

The extraction stage performs binary archaeology on PowerBuilder's proprietary formats.

**Input**: PBL/PBD binary files
**Output**: P-code files (`.fun`) and resources

#### Binary Format Structure

PowerBuilder uses two main formats:
- **PBL**: PowerBuilder Library (source + compiled)
- **PBD**: PowerBuilder Dynamic Library (compiled only)

Modern PBD files (12.5+) use a segmented structure:
```
HDR* | Header block with version info
ENT* | Entry catalog with object names
DAT* | Data blocks with compiled code
NOD* | Node tree for organization
FRE* | Free space markers
```

#### Implementation (`src_new/extract/extractor.py`)

```python
class PBLParser:
    """Parser for PowerBuilder Library files."""

    def parse(self) -> PBLFile:
        with BinaryReader(self.file_path) as self.reader:
            # Check file signature
            signature = self.reader.read(4)

            if signature == b'HDR*':
                # Modern segmented format
                return self._parse_hdr_file()
            elif signature in [b'PBL\x06', b'PBD\x06']:
                # Classic format
                return self._parse_classic_file()
```

The extractor handles:
- Version detection (6.0 through 12.5)
- Encoding detection (ASCII vs Unicode)
- Corruption recovery
- Resource extraction (images, sounds, etc.)

### Stage 2: Decompile - From Bytecode to Source

The decompilation stage reconstructs PowerBuilder source from P-code bytecode.

**Input**: P-code files (`.fun`)
**Output**: PowerBuilder source (`.sru`, `.srw`, `.srm`, `.srd`)

#### P-code Architecture

PowerBuilder compiles to a stack-based bytecode with:
- **256 opcodes** in version 6.0
- **594 opcodes** in version 8.0+
- Stack operations, jumps, function calls
- Object-oriented constructs

#### Opcode Examples (`src/decompile/opcodes/opcodes.py`)

```python
OPCODES = {
    0x01: ("PUSH_CONST_0", 0, None),           # Push 0 onto stack
    0x32: ("PUSH_CONST_INT", 2, "uint16le"),   # Push 16-bit integer
    0x35: ("PUSH_VARIABLE", 2, "var_index"),   # Push variable value
    0x5C: ("JUMP", 2, "jump_offset"),          # Unconditional jump
    0x5D: ("JUMP_IF_FALSE", 2, "jump_offset"), # Conditional jump
    0x85: ("CALL_FUNCTION", 4, "func_info"),   # Function call
    # ... 577 more opcodes
}
```

#### Decompilation Process

```python
class PCodeDecoder:
    """Decoder for PowerBuilder P-code."""

    def decode_function(self, bytecode: bytes) -> DecompiledFunction:
        instructions = []
        offset = 0

        while offset < len(bytecode):
            opcode = bytecode[offset]
            mnemonic, operand_size, hint = OPCODES.get(opcode)

            # Read operands
            operands = bytecode[offset+1:offset+1+operand_size]

            # Create instruction
            instruction = PCodeInstruction(
                offset=offset,
                opcode=opcode,
                mnemonic=mnemonic,
                operands=self._decode_operands(operands, hint)
            )
            instructions.append(instruction)
            offset += 1 + operand_size

        # Reconstruct control flow
        return self._build_control_flow(instructions)
```

The decompiler features:
- **Tiered P-code detection** for performance
- **Expression reconstruction** from stack operations
- **Control flow analysis** (loops, conditionals)
- **Type inference** from operations

### Stage 3: Parse - Building Abstract Syntax Trees

The parsing stage transforms PowerBuilder source into structured ASTs.

**Input**: PowerBuilder source files
**Output**: AST in JSON format

#### Grammar System

PowerRebuilder uses Lark parser with EBNF grammars:

```python
# Window grammar (simplified)
WINDOW_GRAMMAR = r'''
window: window_header window_body

window_header: "global"? "type" IDENTIFIER "from" IDENTIFIER
             | "window" IDENTIFIER

window_body: variable_declarations*
            event_definition*
            function_definition*
            "end" "type"

variable_declaration: type_name IDENTIFIER array_bounds? "=" expression
                    | type_name IDENTIFIER array_bounds?

event_definition: "event" IDENTIFIER "(" parameters? ")"
                 statements
                 "end" "event"

function_definition: access_modifier? "function" return_type IDENTIFIER
                    "(" parameters? ")"
                    statements
                    "end" "function"
'''
```

#### Parser Implementation (`src_new/parse/parser.py`)

```python
class PowerBuilderParser(BaseParser):
    """Parser for PowerBuilder source files."""

    def parse(self, source: str, file_type: str = None) -> ParseResult:
        # Preprocess source
        cleaned = self._preprocess(source)

        # Select appropriate grammar
        grammar = self._get_grammar(file_type)

        # Parse with Lark
        parser = Lark(grammar, parser='earley', debug=True)
        tree = parser.parse(cleaned)

        # Transform to AST
        ast = PowerBuilderTransformer().transform(tree)

        return ParseResult(
            success=True,
            ast=ast,
            source_map=self._build_source_map(tree)
        )
```

The parser handles:
- Multiple object types (windows, datawindows, menus, etc.)
- Error recovery for malformed code
- Source location tracking
- Comment preservation

### Stage 4: Model - Semantic Analysis

The modeling stage builds semantic models from ASTs with resolved types and dependencies.

**Input**: AST JSON files
**Output**: Semantic models with type information

#### Type System

PowerBuilder's type system includes:
- **Basic types**: integer, long, string, boolean, decimal, date, datetime
- **Arrays**: Fixed and variable bounds
- **Objects**: Classes with inheritance
- **Structures**: Composite types
- **DataWindows**: Special data-bound controls

#### Model Building (`src_new/model/builder.py`)

```python
class ModelExtractorVisitor(ASTVisitor):
    """Extract semantic information from AST."""

    def visit_class_definition(self, node: ASTNode) -> SemanticObject:
        obj = SemanticObject(
            name=node.name,
            type=ObjectType.from_string(node.type),
            parent=node.extends
        )

        # Extract properties
        for var in node.variables:
            prop = Property(
                name=var.name,
                data_type=self._resolve_type(var.type),
                access_modifier=var.access,
                initial_value=var.initial
            )
            obj.properties.append(prop)

        # Extract methods
        for func in node.functions:
            method = Method(
                name=func.name,
                return_type=self._resolve_type(func.return_type),
                parameters=self._extract_parameters(func.params),
                body=func.statements
            )
            obj.methods.append(method)

        return obj
```

The model builder performs:
- Type resolution and inference
- Dependency graph construction
- Symbol table management
- Cross-module reference resolution
- Inheritance hierarchy analysis

### Stage 5: Generate - Modern Code Creation

The generation stage produces modern application code from semantic models.

**Input**: Semantic models
**Output**: Complete modern applications

#### Template Engine

Code generation uses Jinja2 templates for flexibility:

```python
# Flutter widget template
FLUTTER_WIDGET_TEMPLATE = '''
class {{ class_name }} extends StatefulWidget {
  const {{ class_name }}({super.key});

  @override
  State<{{ class_name }}> createState() => _{{ class_name }}State();
}

class _{{ class_name }}State extends State<{{ class_name }}> {
  {% for property in properties %}
  {{ property.dart_type }} {{ property.name }} = {{ property.initial_value }};
  {% endfor %}

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('{{ title }}')),
      body: Column(
        children: [
          {% for control in controls %}
          {{ generate_widget(control) }},
          {% endfor %}
        ],
      ),
    );
  }
}
'''
```

#### Multi-Target Generation

The generator supports multiple output targets:

```python
class GenerateCoordinator:
    """Coordinator for code generation stage."""

    def _create_generator(self) -> BaseCodeGenerator:
        if self.target == TargetLanguage.FLUTTER:
            return FlutterGenerator(self.target)
        elif self.target == TargetLanguage.PYTHON:
            return PythonGenerator(self.target)
        elif self.target == TargetLanguage.TAURI:
            return TauriGenerator(self.input_path, self.output_path)
        elif self.target == TargetLanguage.DIOXUS:
            return DioxusGenerator(self.input_path, self.output_path)
        # ... more targets
```

---

## PowerBuilder Concepts

### Object Types

PowerBuilder organizes code into several object types:

| Extension | Object Type | Description | Modern Equivalent |
|-----------|------------|-------------|-------------------|
| `.sra` | Application | Entry point and globals | main.dart / app.py |
| `.srw` | Window | UI forms with controls | Screen/View/Page |
| `.sru` | User Object | Reusable components | Widget/Component |
| `.srm` | Menu | Menu definitions | Menu/Navigation |
| `.srd` | DataWindow | Data-bound grids | DataTable/GridView |
| `.srs` | Structure | Data structures | Class/Model |
| `.srf` | Function | Global functions | Utility functions |

### DataWindow - PowerBuilder's Killer Feature

DataWindows are PowerBuilder's unique feature combining:
- SQL query definition
- Result set presentation
- Data modification tracking
- Built-in printing and export

Example DataWindow definition:
```sql
SELECT patient.patient_id,
       patient.first_name,
       patient.last_name,
       patient.birth_date,
       patient.insurance_id
FROM patient
WHERE patient.status = :as_status
ORDER BY patient.last_name ASC
```

This becomes a complete CRUD interface with sorting, filtering, and editing capabilities.

### Event-Driven Architecture

PowerBuilder uses an event-driven model similar to modern frameworks:

```powerbuilder
// PowerBuilder event
event clicked()
    MessageBox("Info", "Button was clicked")
    this.enabled = false
end event

// Translates to Flutter
onPressed: () {
  showDialog(
    context: context,
    builder: (context) => AlertDialog(
      title: Text("Info"),
      content: Text("Button was clicked"),
    ),
  );
  setState(() {
    enabled = false;
  });
}
```

### Version Evolution

| Version | Year | Key Features | Opcodes |
|---------|------|--------------|---------|
| 6.0 | 1997 | Web deployment | 256 |
| 7.0 | 1999 | EJB support | 256 |
| 8.0 | 2001 | Web services | 594 |
| 9.0 | 2003 | .NET support | 594 |
| 10.0 | 2004 | Windows forms | 594 |
| 11.0 | 2006 | .NET 2.0 | 594 |
| 12.0 | 2008 | WPF support | 594 |
| 12.5 | 2010 | 64-bit | 594 |

---

## Code Generation Targets

### Flutter/Dart - Mobile Applications

Flutter generation produces complete mobile applications with:

**Architecture:**
```
flutter_app/
├── lib/
│   ├── main.dart           # App entry point
│   ├── screens/            # UI screens (from windows)
│   ├── widgets/            # Reusable widgets (from user objects)
│   ├── models/             # Data models (from structures)
│   ├── services/           # Business logic (from NVOs)
│   └── providers/          # State management
├── pubspec.yaml            # Dependencies
└── assets/                 # Images and resources
```

**Features:**
- Material Design UI components
- Glassmorphism design system
- Provider state management
- SQLite local database
- HTTP API integration

### Python/Litestar - Web APIs

Python generation creates modern async web APIs:

**Architecture:**
```
python_api/
├── models/                 # SQLModel/Pydantic models
│   ├── patient.py
│   └── appointment.py
├── services/              # Business logic layer
│   ├── patient_service.py
│   └── billing_service.py
├── api/                   # REST endpoints
│   ├── patient_api.py
│   └── appointment_api.py
├── main.py               # Application entry
└── requirements.txt      # Dependencies
```

**Example API Endpoint:**
```python
class PatientController(Controller):
    """Patient API controller."""

    path = "/api/patients"
    dependencies = {"service": Provide(provide_patient_service)}

    @get()
    async def list_patients(self, service: PatientService) -> List[Patient]:
        """Get all patients."""
        return await service.get_all_patients()

    @post()
    async def create_patient(self, data: Patient, service: PatientService) -> Patient:
        """Create new patient."""
        return await service.create_patient(data)
```

### Rust/Tauri - Native Desktop

Tauri generation creates lightweight native desktop applications:

**Architecture:**
```
tauri_app/
├── src/
│   ├── main.rs            # Rust backend
│   ├── commands.rs        # Tauri commands
│   ├── models/            # Data structures
│   └── state.rs           # Application state
├── index.html             # Frontend entry
├── Cargo.toml            # Rust dependencies
└── tauri.conf.json       # Tauri configuration
```

**Features:**
- Native performance
- Small binary size (~10MB)
- System tray integration
- File system access
- Cross-platform (Windows, macOS, Linux)

### Rust/Dioxus - Web/Desktop Hybrid

Dioxus enables write-once, run-anywhere Rust applications:

```rust
#[component]
pub fn PatientView() -> Element {
    let patients = use_signal(|| Vec::<Patient>::new());

    rsx! {
        div {
            class: "patient-list",
            for patient in patients.read().iter() {
                PatientCard { patient: patient.clone() }
            }
        }
    }
}
```

---

## Technical Deep Dives

### Binary Format Analysis

PowerBuilder's binary formats evolved over versions but maintain backward compatibility:

#### PBL Header Structure (Classic Format)
```
Offset  Size  Description
0x0000  4     Signature ('PBL\x06' or 'PBD\x06')
0x0004  4     Format version
0x0008  4     Creation timestamp
0x000C  4     Modification timestamp
0x0010  4     Comment size
0x0014  N     Comment (if size > 0)
...     4     First node offset
...     4     Node count
```

#### HDR* Format (Modern)
```python
def analyze_hdr_format(data: bytes):
    """Analyze HDR* format structure."""
    offset = 0

    while offset < len(data):
        marker = data[offset:offset+4]

        if marker == b'HDR*':
            # Header block
            block_size = struct.unpack('<I', data[offset+4:offset+8])[0]
            # Contains: PowerBuilder version, creation date, etc.

        elif marker == b'ENT*':
            # Entry catalog
            block_size = struct.unpack('<I', data[offset+4:offset+8])[0]
            # Contains: Object names and metadata

        elif marker == b'DAT*':
            # Data block
            block_size = struct.unpack('<I', data[offset+4:offset+8])[0]
            # Contains: Compiled P-code or object data
```

### P-code Detection Algorithms

The decompiler uses a tiered detection system for performance:

```python
class TieredPCodeDetector:
    """Multi-tier P-code detection for performance."""

    def detect_pcode(self, data: bytes) -> List[PCodeRegion]:
        # Tier 1: Ultra-fast signature check (<1ms)
        if self._has_pcode_signature(data):
            return self._quick_extract(data)

        # Tier 2: Fast pattern matching (~10ms)
        patterns = self._find_common_patterns(data)
        if patterns:
            return self._pattern_based_extract(data, patterns)

        # Tier 3: Comprehensive analysis (~100ms)
        opcodes = self._scan_for_opcodes(data)
        if opcodes:
            return self._opcode_based_extract(data, opcodes)

        # Tier 4: Deep inspection (1s+)
        return self._deep_analysis(data)
```

### AST Transformation Pipeline

The AST transformation uses the visitor pattern for flexibility:

```python
class ASTTransformer:
    """Transform parse tree to semantic AST."""

    def transform(self, tree: Tree) -> ASTNode:
        return self._visit(tree)

    def _visit(self, node):
        if isinstance(node, Tree):
            method_name = f"visit_{node.data}"
            if hasattr(self, method_name):
                return getattr(self, method_name)(node)
            return self._visit_generic(node)
        return node

    def visit_window_definition(self, node: Tree) -> WindowAST:
        return WindowAST(
            name=self._get_identifier(node),
            parent=self._get_parent(node),
            variables=self._extract_variables(node),
            events=self._extract_events(node),
            controls=self._extract_controls(node)
        )
```

### Template Engine Integration

Code generation leverages Jinja2's power for maintainable templates:

```python
class TemplateManager:
    """Manages code generation templates."""

    def __init__(self, template_dir: Path):
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Register custom filters
        self.env.filters['to_dart_type'] = self.to_dart_type
        self.env.filters['to_python_type'] = self.to_python_type

    def render(self, template_name: str, context: dict) -> str:
        template = self.env.get_template(template_name)
        return template.render(**context)
```

---

## Development Guide

### Environment Setup

**Requirements:**
- Python 3.13+
- uv (Python package manager)
- Task (build automation)
- Git

**Installation:**
```bash
# Clone repository
git clone https://github.com/michaelprowacki/powerrebuilder.git
cd powerrebuilder

# Install dependencies with uv
uv sync --dev

# Or traditional pip
pip install -e .

# Verify installation
python main.py --help
```

### Running the Pipeline

**Full Pipeline (Recommended for first-time users):**
```bash
# Process a single PBL file
python main.py all input.pbl output/

# Process directory of PBD files
python main.py all data/pbd_files/ output/ --parallel --workers 8
```

**Individual Stages (For debugging or partial processing):**
```bash
# Stage 1: Extract
python main.py extract data/pbd_files/dcm_patient.pbd output/extracted/
ls output/extracted/  # Check .fun files

# Stage 2: Decompile
python main.py decompile output/extracted/ output/decompiled/
ls output/decompiled/  # Check .sru/.srw files

# Stage 3: Parse
python main.py parse output/decompiled/ output/parsed/
cat output/parsed/patient.json  # Examine AST

# Stage 4: Model
python main.py model output/parsed/ output/models/

# Stage 5: Generate
python main.py generate output/models/ output/flutter/ --target flutter
python main.py generate output/models/ output/python/ --target python
```

### Testing

**Run Test Suite:**
```bash
# All tests
task test

# Specific module
uv run pytest tests/unit/decompile/ -v

# With coverage
task coverage
open htmlcov/index.html

# Performance tests
task benchmark:perf
```

**Test Structure:**
```
tests/
├── fixtures/           # Sample PowerBuilder files
│   ├── simple_window.srw
│   ├── complex_datawindow.srd
│   └── pcode_files/
├── unit/              # Unit tests
│   ├── test_extract.py
│   ├── test_decompile.py
│   └── test_parse.py
└── integration/       # End-to-end tests
```

### Common Issues and Solutions

**Issue: Import errors with DI system**
```python
# Old (remove):
from src.infrastructure.di import container

# New (use direct imports):
from src.extract import ExtractCoordinator
```

**Issue: Memory usage with large files**
```bash
# Use streaming mode
python main.py extract large.pbd output/ --streaming

# Increase memory limit
ulimit -v unlimited
```

**Issue: Parser failures on malformed code**
```python
# Enable error recovery
python main.py parse input/ output/ --error-recovery --continue-on-error
```

**Issue: Slow P-code detection**
```bash
# Use parallel processing
python main.py decompile input/ output/ --parallel --workers 16

# Skip deep analysis
python main.py decompile input/ output/ --detection-tier fast
```

### Performance Optimization

**File-Level Parallelism:**
```python
# Within stages, files can be processed in parallel
coordinator = ExtractCoordinator(
    input_path=Path("input"),
    output_path=Path("output"),
    parallel=True,
    max_workers=8
)
```

**Memory-Mapped Files:**
```python
# For large files, use memory mapping
with BinaryReader(file_path, use_mmap=True) as reader:
    # Process without loading entire file
```

**Grammar Caching:**
```python
# Grammars are compiled once and cached
grammar_manager = GrammarManager()
grammar = grammar_manager.get_grammar("window")  # Cached after first use
```

---

## Real-World Usage

### Processing the DCM System

The Dental Clinic Management system serves as a real-world test case:

**System Overview:**
- 54 PowerBuilder modules
- ~70MB of compiled code
- 15+ years of development
- Mission-critical healthcare application

**Processing Workflow:**
```bash
# 1. Extract all modules
python main.py extract data/pbd_files/ output/dcm_extracted/

# 2. Decompile to source
python main.py decompile output/dcm_extracted/ output/dcm_source/

# 3. Parse to AST
python main.py parse output/dcm_source/ output/dcm_ast/

# 4. Build models
python main.py model output/dcm_ast/ output/dcm_models/

# 5. Generate modern code
python main.py generate output/dcm_models/ output/dcm_flutter/ --target flutter
python main.py generate output/dcm_models/ output/dcm_api/ --target python
```

### Migration Strategy

**Phase 1: Assessment**
1. Inventory PowerBuilder applications
2. Identify critical business logic
3. Map dependencies
4. Estimate complexity

**Phase 2: Extraction**
1. Run extraction pipeline
2. Validate output completeness
3. Identify missing components
4. Document issues

**Phase 3: Transformation**
1. Generate target code
2. Review and adjust templates
3. Add modern features (authentication, logging)
4. Integrate with existing systems

**Phase 4: Validation**
1. Unit test business logic
2. UI/UX testing
3. Performance testing
4. User acceptance testing

### Handling Large Applications

For applications with hundreds of modules:

```python
# Batch processing script
import os
from pathlib import Path

def process_large_app(input_dir: Path, output_base: Path):
    """Process large PowerBuilder application."""

    # Group modules by functionality
    modules = group_modules_by_prefix(input_dir)

    for group_name, files in modules.items():
        print(f"Processing {group_name} ({len(files)} files)")

        output_dir = output_base / group_name

        # Process each group independently
        for file in files:
            try:
                process_file(file, output_dir)
            except Exception as e:
                log_error(file, e)
                continue
```

---

## Code Examples

### Complete Processing Example

Let's walk through processing a simple PowerBuilder window:

**Input: `patient_window.srw`**
```powerbuilder
$PBExportHeader$patient_window.srw
forward
global type patient_window from window
end type
type cb_save from commandbutton within patient_window
end type
type dw_patient from datawindow within patient_window
end type
end forward

global type patient_window from window
integer width = 2400
integer height = 1600
string title = "Patient Information"
cb_save cb_save
dw_patient dw_patient
end type

event open()
    dw_patient.SetTransObject(SQLCA)
    dw_patient.Retrieve()
end event

type cb_save from commandbutton within patient_window
integer x = 1800
integer y = 1400
integer width = 400
integer height = 112
string text = "Save"
end type

event clicked()
    if dw_patient.Update() = 1 then
        Commit;
        MessageBox("Success", "Patient saved successfully")
    else
        Rollback;
        MessageBox("Error", "Failed to save patient")
    end if
end event
```

**Stage 1 - Extraction Output: `patient_window.fun`**
```
[Binary P-code data - 2KB of compiled bytecode]
```

**Stage 2 - Decompilation Output: `patient_window.sru`**
```powerbuilder
// Decompiled from P-code
global type patient_window from window
    integer width = 2400
    integer height = 1600
    string title = "Patient Information"

    event open()
        dw_patient.SetTransObject(SQLCA)
        dw_patient.Retrieve()
    end event
end type

type cb_save from commandbutton within patient_window
    event clicked()
        if dw_patient.Update() = 1 then
            Commit;
            MessageBox("Success", "Patient saved successfully")
        else
            Rollback;
            MessageBox("Error", "Failed to save patient")
        end if
    end event
end type
```

**Stage 3 - Parse Output: `patient_window.json`**
```json
{
  "type": "window",
  "name": "patient_window",
  "parent": "window",
  "properties": [
    {"name": "width", "type": "integer", "value": 2400},
    {"name": "height", "type": "integer", "value": 1600},
    {"name": "title", "type": "string", "value": "Patient Information"}
  ],
  "controls": [
    {
      "type": "commandbutton",
      "name": "cb_save",
      "properties": [
        {"name": "x", "value": 1800},
        {"name": "y", "value": 1400},
        {"name": "text", "value": "Save"}
      ],
      "events": [
        {
          "name": "clicked",
          "body": [
            {
              "type": "if_statement",
              "condition": {"type": "binary_op", "operator": "==",
                          "left": {"type": "method_call", "object": "dw_patient", "method": "Update"},
                          "right": {"type": "literal", "value": 1}},
              "then_branch": [
                {"type": "statement", "value": "Commit"},
                {"type": "method_call", "method": "MessageBox",
                 "args": ["Success", "Patient saved successfully"]}
              ],
              "else_branch": [
                {"type": "statement", "value": "Rollback"},
                {"type": "method_call", "method": "MessageBox",
                 "args": ["Error", "Failed to save patient"]}
              ]
            }
          ]
        }
      ]
    },
    {
      "type": "datawindow",
      "name": "dw_patient"
    }
  ],
  "events": [
    {
      "name": "open",
      "body": [
        {"type": "method_call", "object": "dw_patient", "method": "SetTransObject", "args": ["SQLCA"]},
        {"type": "method_call", "object": "dw_patient", "method": "Retrieve"}
      ]
    }
  ]
}
```

**Stage 4 - Model Output: Semantic Model**
```python
SemanticObject(
    name="patient_window",
    type=ObjectType.WINDOW,
    parent="window",
    properties=[
        Property(name="width", data_type="integer", value=2400),
        Property(name="height", data_type="integer", value=1600),
        Property(name="title", data_type="string", value="Patient Information")
    ],
    methods=[],
    events=[
        Event(
            name="open",
            statements=[
                MethodCall(object="dw_patient", method="SetTransObject", args=["SQLCA"]),
                MethodCall(object="dw_patient", method="Retrieve")
            ]
        )
    ],
    controls=[
        Control(
            type="commandbutton",
            name="cb_save",
            events=[
                Event(name="clicked", statements=[...])
            ]
        ),
        Control(type="datawindow", name="dw_patient")
    ]
)
```

**Stage 5 - Flutter Output: `patient_window.dart`**
```dart
import 'package:flutter/material.dart';
import '../models/patient.dart';
import '../services/patient_service.dart';

class PatientWindow extends StatefulWidget {
  const PatientWindow({super.key});

  @override
  State<PatientWindow> createState() => _PatientWindowState();
}

class _PatientWindowState extends State<PatientWindow> {
  final PatientService _patientService = PatientService();
  List<Patient> _patients = [];
  bool _hasChanges = false;

  @override
  void initState() {
    super.initState();
    _loadPatients();
  }

  Future<void> _loadPatients() async {
    final patients = await _patientService.retrieve();
    setState(() {
      _patients = patients;
    });
  }

  Future<void> _savePatient() async {
    try {
      await _patientService.update(_patients);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Patient saved successfully')),
        );
        setState(() {
          _hasChanges = false;
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to save patient: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Patient Information'),
      ),
      body: Column(
        children: [
          Expanded(
            child: DataTable(
              columns: const [
                DataColumn(label: Text('ID')),
                DataColumn(label: Text('Name')),
                DataColumn(label: Text('Birth Date')),
              ],
              rows: _patients.map((patient) => DataRow(
                cells: [
                  DataCell(Text(patient.id.toString())),
                  DataCell(
                    TextFormField(
                      initialValue: patient.name,
                      onChanged: (value) {
                        patient.name = value;
                        setState(() {
                          _hasChanges = true;
                        });
                      },
                    ),
                  ),
                  DataCell(Text(patient.birthDate.toString())),
                ],
              )).toList(),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: ElevatedButton(
              onPressed: _hasChanges ? _savePatient : null,
              child: const Text('Save'),
            ),
          ),
        ],
      ),
    );
  }
}
```

**Stage 5 - Python Output: `patient_api.py`**
```python
from typing import List
from litestar import Controller, get, post, put, delete
from litestar.di import Provide

from models.patient import Patient
from services.patient_service import PatientService

def provide_patient_service() -> PatientService:
    """Provide patient service instance."""
    return PatientService()

class PatientController(Controller):
    """Patient API controller - generated from patient_window."""

    path = "/api/patients"
    dependencies = {"service": Provide(provide_patient_service)}

    @get()
    async def list_patients(self, service: PatientService) -> List[Patient]:
        """Get all patients - maps to dw_patient.Retrieve()."""
        return await service.get_all_patients()

    @put("/{patient_id:int}")
    async def update_patient(
        self, patient_id: int, data: Patient, service: PatientService
    ) -> Patient:
        """Update patient - maps to dw_patient.Update()."""
        patient = await service.update_patient(patient_id, data)
        if not patient:
            raise ValueError(f"Patient {patient_id} not found")
        return patient
```

---

## Reference Section

### Command-Line Interface

**Global Options:**
```bash
python main.py [OPTIONS] COMMAND [ARGS]

Options:
  --loglevel [DEBUG|INFO|WARNING|ERROR]  Logging level
  --parallel                              Enable parallel processing
  --workers INTEGER                       Number of worker processes
  --continue-on-error                     Continue despite errors
  --output-format [json|yaml]             Output format for reports
  --help                                  Show help message
```

**Commands:**

| Command | Description | Key Options |
|---------|-------------|-------------|
| `all` | Run complete pipeline | `--target`, `--streaming` |
| `extract` | Extract from PBL/PBD | `--include-resources`, `--version` |
| `decompile` | Decompile P-code | `--detection-tier`, `--opcode-set` |
| `parse` | Parse to AST | `--grammar`, `--error-recovery` |
| `model` | Build semantic models | `--resolve-types`, `--cross-reference` |
| `generate` | Generate modern code | `--target`, `--template-dir` |
| `analyze` | Analyze PB files | `--format`, `--depth` |
| `validate` | Validate files | `--check-corruption`, `--check-structure` |

### File Formats

**PBL/PBD Binary Format:**
- Magic bytes: `PBL\x06` or `PBD\x06` (classic), `HDR*` (modern)
- Encoding: ASCII (pre-10.0), UTF-16LE (10.0+)
- Compression: Optional ZLIB
- Checksum: CRC32

**P-code Format:**
- Stack-based bytecode
- Variable-length instructions
- Big-endian byte order (pre-8.0), little-endian (8.0+)

**AST JSON Schema:**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "type": {"type": "string", "enum": ["window", "datawindow", "menu", "function"]},
    "name": {"type": "string"},
    "parent": {"type": "string"},
    "properties": {"type": "array"},
    "methods": {"type": "array"},
    "events": {"type": "array"}
  },
  "required": ["type", "name"]
}
```

### Opcode Reference (Partial)

| Opcode | Mnemonic | Stack Effect | Description |
|--------|----------|--------------|-------------|
| 0x01 | PUSH_CONST_0 | → 0 | Push zero |
| 0x02 | PUSH_CONST_1 | → 1 | Push one |
| 0x32 | PUSH_CONST_INT | → n | Push 16-bit integer |
| 0x35 | PUSH_VARIABLE | → value | Push variable value |
| 0x40 | POP | value → | Pop and discard |
| 0x41 | DUP | a → a, a | Duplicate top |
| 0x50 | ADD | a, b → a+b | Addition |
| 0x51 | SUB | a, b → a-b | Subtraction |
| 0x5C | JUMP | → | Unconditional jump |
| 0x5D | JUMP_IF_FALSE | cond → | Jump if false |
| 0x85 | CALL_FUNCTION | args → result | Function call |
| 0x90 | RETURN | value → | Return from function |

### Configuration Files

**`pyproject.toml` - Project configuration:**
```toml
[project]
name = "powerrebuilder"
version = "0.1.0"
dependencies = [
    "lark>=1.2.2",        # Parser
    "jinja2>=3.1.6",      # Templates
    "pydantic>=2.0.0",    # Models
    "click>=8.2.1",       # CLI
    "rich>=14.1.0",       # Output
]

[tool.ruff]
line-length = 100
target-version = "py313"
```

**`taskfile.yml` - Build automation:**
```yaml
version: '3'

tasks:
  test:
    desc: Run tests
    cmds:
      - uv run pytest tests/ -v

  format:
    desc: Format code
    cmds:
      - ruff format .

  lint:
    desc: Lint code
    cmds:
      - ruff check .
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POWERREBUILDER_LOG_LEVEL` | Logging level | INFO |
| `POWERREBUILDER_WORKERS` | Default worker count | CPU count |
| `POWERREBUILDER_CACHE_DIR` | Cache directory | ~/.cache/powerrebuilder |
| `POWERREBUILDER_TEMPLATE_DIR` | Custom templates | None |

---

## Conclusion

PowerRebuilder represents a significant engineering effort to bridge the gap between legacy PowerBuilder systems and modern application architectures. By providing a complete transformation pipeline from binary to deployable code, it enables organizations to:

1. **Preserve Business Value**: Decades of business logic remain intact
2. **Modernize Technology Stack**: Move to supported, modern platforms
3. **Reduce Costs**: Eliminate PowerBuilder licensing and maintenance
4. **Enable Innovation**: Add modern features like mobile, cloud, and web deployment
5. **Maintain Continuity**: Gradual migration without business disruption

The project continues to evolve with contributions from the community, expanding language support, improving accuracy, and handling edge cases from real-world PowerBuilder applications.

For the latest updates, visit: https://github.com/michaelprowacki/powerrebuilder

---

*This document represents the state of PowerRebuilder as of September 2025. The project is under active development, and features may change.*
