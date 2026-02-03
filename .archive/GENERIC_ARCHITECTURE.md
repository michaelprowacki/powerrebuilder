# Generic Legacy Modernization Architecture

## Overview

PowerRebuilder has been transformed from a PowerBuilder-specific tool into a **generic legacy modernization platform** that can handle multiple compiled languages while maintaining Scott Wlaschin's functional domain modeling principles.

## Supported Languages

The architecture now supports modernization of:

| Language | Archive Formats | Status | Complexity |
|----------|----------------|---------|------------|
| **PowerBuilder** | PBL, PBD | ✅ Implemented | High |
| **Java** | JAR, WAR, EAR, class | ✅ Example Ready | Medium |
| **.NET** | DLL, EXE | 🔄 Planned | Medium |
| **Oracle Forms** | FMB, FMX, MMB | 🔄 Planned | High |
| **Visual Basic 6** | FRM, BAS, CLS | 🔄 Planned | High |
| **Delphi** | DCU, DFM | 🔄 Planned | High |
| **Python** | PYC, PYO | 🔄 Planned | Low |
| **FoxPro** | FXP, APP | 🔄 Planned | High |

## Architecture Components

### 1. Core Domain Types (`legacy_modernization_types.py`)

Generic types that work across all legacy languages:

```python
# Archives (work for PBL, JAR, DLL, etc.)
CompiledArchive = NewType('CompiledArchive', bytes)
Bytecode = NewType('Bytecode', bytes)
SourceCode = NewType('SourceCode', str)

# Objects (represent any compiled object)
class LegacyObjectType(Enum):
    UI_CONTAINER      # Window, Form, Screen
    DATA_PRESENTATION # DataWindow, Grid, Report
    FUNCTION         # Functions, Methods
    CLASS           # Classes, Objects
    MODULE          # Modules, Units

# Application Model (language-agnostic)
class LegacyApplicationModel:
    ui_containers: Dict[str, UIContainer]
    data_presentations: Dict[str, DataPresentation]
    code_modules: Dict[str, CodeModule]
```

### 2. Generic Workflows (`generic_workflows.py`)

Language-agnostic workflows using functional composition:

```python
# Works with ANY compiled archive
ArchiveExtractWorkflow = Callable[[CompiledArchive], Result[List[CompiledObject], Error]]

# Works with ANY bytecode format
BytecodeDecompiler = Callable[[Bytecode], Result[SourceCode, Error]]

# Works with ANY source language
SourceParser = Callable[[SourceCode], Result[GenericAST, Error]]

# Builds model for ANY legacy app
ModelBuilder = Callable[[List[GenericAST]], Result[LegacyApplicationModel, Error]]

# Migrates to modern platforms
MobileMigrator = Callable[[LegacyApplicationModel], Result[ModernMobileCode, Error]]
```

### 3. Language Adapter Interface (`language_adapter.py`)

Protocol that each language adapter must implement:

```python
class LanguageAdapter(Protocol):
    def detect_language(data: bytes) -> Result[SupportedLanguage, str]
    def parse_archive_header(archive: CompiledArchive) -> Result[ArchiveHeader, Error]
    def extract_objects(archive, header) -> Result[List[CompiledObject], Error]
    def decompile_bytecode(bytecode: Bytecode) -> Result[SourceCode, Error]
    def parse_source(source: SourceCode) -> Result[GenericAST, Error]
    def build_model(symbols, asts) -> Result[LegacyApplicationModel, Error]
```

### 4. Language-Specific Adapters

Each language provides an adapter:

```
src_new/adapters/
├── powerbuilder/
│   ├── powerbuilder_adapter.py  # PBL/PBD handling
│   ├── pbl_format.py            # PBL-specific format
│   └── powerscript_parser.py    # PowerScript parsing
├── java/
│   ├── java_adapter.py          # JAR/class handling
│   ├── bytecode_reader.py       # JVM bytecode
│   └── swing_detector.py        # Swing UI detection
├── dotnet/
│   ├── dotnet_adapter.py        # DLL/EXE handling
│   ├── il_reader.py             # .NET IL bytecode
│   └── winforms_parser.py       # WinForms detection
└── oracle_forms/
    ├── oracle_adapter.py         # FMB/FMX handling
    └── plsql_parser.py          # PL/SQL parsing
```

### 5. Automatic Language Detection (`language_detector.py`)

Detects language from file content or extension:

```python
# Auto-detect from content
result = detect_language(archive_data)
# Returns: PowerBuilder, Java, .NET, etc.

# Get appropriate adapter
adapter = get_adapter_for_language(language)

# Process with generic pipeline
pipeline = create_modernization_pipeline(adapter, target="flutter")
modern_code = pipeline(archive_data)
```

## How It Works

### 1. Language Detection
```python
archive = CompiledArchive(file_data)
language, adapter = auto_detect_language(archive)
```

### 2. Extraction
```python
objects = adapter.extract_objects(archive, header)
# Returns generic CompiledObject list
```

### 3. Decompilation (if needed)
```python
for obj in objects:
    if obj.needs_decompilation():
        source = adapter.decompile_bytecode(obj.bytecode)
```

### 4. Parsing
```python
ast = adapter.parse_source(source)
# Returns generic AST structure
```

### 5. Model Building
```python
model = adapter.build_model(symbols, asts)
# Returns LegacyApplicationModel
```

### 6. Migration (language-agnostic)
```python
# Same migrator works for ANY source language!
flutter_code = flutter_migrator(model)
react_code = react_migrator(model)
tauri_code = tauri_migrator(model)
```

## Adding New Languages

To add support for a new language:

1. **Create adapter directory**: `src_new/adapters/newlang/`

2. **Implement adapter**:
```python
class NewLangAdapter(BaseLanguageAdapter):
    def parse_archive_header(self, archive):
        # Handle specific archive format

    def extract_objects(self, archive, header):
        # Extract compiled objects

    def decompile_bytecode(self, bytecode):
        # Decompile to source

    def parse_source(self, source):
        # Parse to AST
```

3. **Register adapter**:
```python
register_adapter(NewLangAdapter())
```

4. **Add detection signatures**:
```python
FILE_SIGNATURES.append(
    FileSignature(b'MAGIC', 0, SupportedLanguage.NEWLANG, 1.0, "Description")
)
```

## Benefits of Generic Architecture

1. **Reusable Core**: The functional workflows work for any compiled language
2. **Language Plugins**: Add new languages via adapters without changing core
3. **Scott Wlaschin Compliant**: Still uses functional domain modeling
4. **Market Expansion**: Handle legacy modernization for many platforms
5. **Consistent Migration**: Same Flutter/React/Tauri generators for all languages

## Example Usage

### PowerBuilder to Flutter
```python
# Auto-detects PowerBuilder from PBL
pbl_data = read_file("app.pbl")
result = modernize_to_flutter(pbl_data)
```

### Java to React
```python
# Auto-detects Java from JAR
jar_data = read_file("legacy.jar")
result = modernize_to_react(jar_data)
```

### Oracle Forms to Tauri
```python
# Auto-detects Oracle Forms from FMB
fmb_data = read_file("form.fmb")
result = modernize_to_tauri(fmb_data)
```

## Migration Complexity

| Source → Target | Complexity | Why |
|----------------|------------|-----|
| PowerBuilder → Flutter | High | DataWindow concept unique |
| Java → Flutter | Medium | Similar OOP patterns |
| .NET → React | Medium | Component models align |
| Oracle Forms → Web | High | Form-based paradigm different |
| VB6 → Modern | High | Event model translation |
| Delphi → Flutter | Medium | Similar component model |

## Future Enhancements

1. **More Languages**: COBOL, RPG, Natural, ABAP
2. **Cloud Targets**: AWS Lambda, Azure Functions, Google Cloud Run
3. **AI Enhancement**: Use LLMs to improve decompilation
4. **Pattern Library**: Reusable migration patterns
5. **Dependency Analysis**: Handle external libraries
6. **Database Migration**: Modernize data layer too

## Conclusion

The generic architecture maintains all the benefits of Scott Wlaschin's functional domain modeling while supporting multiple legacy languages. The adapter pattern allows easy extension without modifying core workflows, making this a true **Universal Legacy Modernization Platform**.
