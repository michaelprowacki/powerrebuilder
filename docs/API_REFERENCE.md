# API Reference

This document provides comprehensive API documentation for all public interfaces in the PowerRebuilder PowerBuilder reverse engineering system.

## Table of Contents

1. [CLI Commands](#cli-commands)
2. [Pipeline Coordinator](#pipeline-coordinator)
3. [Extraction API](#extraction-api)
4. [Parsing API](#parsing-api)
5. [Decompilation API](#decompilation-api)
6. [Code Generation API](#code-generation-api)
7. [Model Classes](#model-classes)
8. [Utility Functions](#utility-functions)
9. [Configuration](#configuration)
10. [Error Handling](#error-handling)
11. [Progress Tracking](#progress-tracking)
12. [Examples](#examples)

## CLI Commands

### Main Command
```bash
python main.py [OPTIONS] COMMAND [ARGS]...
```

**Options:**
- `--loglevel [DEBUG|INFO|WARNING|ERROR|CRITICAL]`: Set logging level (default: INFO)
- `--traceback/--no-traceback`: Show full traceback on error (default: false)
- `--version`: Show version

### Extract Commands

#### extract files
Extract PowerBuilder source and P-code from PBL/PBD files.

```bash
python main.py extract files [OPTIONS] [INPUT_DIR] [OUTPUT_DIR]
```

**Arguments:**
- `INPUT_DIR`: Directory containing PBL/PBD files (default: input)
- `OUTPUT_DIR`: Directory to write extracted files (default: data/output/current/extracted)

**Options:**
- `--debug`: Enable debug logging
- `--enable-byte-recovery`: Enable byte-level recovery for corrupted files
- `--unicode`: Use unicode mode for extraction

#### extract to-text
Convert PowerBuilder binary files to readable text format.

```bash
python main.py extract to-text [OPTIONS] INPUT_FILE
```

**Options:**
- `-o, --output PATH`: Output text file path
- `-s, --stdout`: Also print to stdout

#### extract inspect
Inspect PBD file structure.

```bash
python main.py extract inspect [FILES]...
```

#### extract hexdump
View hexdump of PowerBuilder files.

```bash
python main.py extract hexdump [FILES]...
```

### Parse Command
Parse PowerBuilder source files into Abstract Syntax Trees.

```bash
python main.py parse [INPUT_DIR] [OUTPUT_DIR]
```

**Arguments:**
- `INPUT_DIR`: Directory with extracted PB source files (default: data/output/current/extracted)
- `OUTPUT_DIR`: Directory for parsed AST data (default: data/output/current/parsed)

### Decompile Command
Decompile PowerBuilder P-code files to high-level pseudocode.

```bash
python main.py decompile [INPUT_DIR] [OUTPUT_DIR]
```

**Arguments:**
- `INPUT_DIR`: Directory with extracted P-code files (default: data/output/current/extracted)
- `OUTPUT_DIR`: Directory for decompiled code (default: data/output/current/decompiled)

### Generate Command
Generate modern application code from parsed and decompiled data.

```bash
python main.py generate [OPTIONS]
```

**Options:**
- `--parsed-dir PATH`: Directory containing parsed AST files
- `--decompiled-dir PATH`: Directory containing decompiled functions

### Schema Command
Extract and document database schema from PowerBuilder code.

```bash
python main.py schema [OPTIONS]
```

**Options:**
- `--project-dir PATH`: PowerBuilder project directory (default: .)
- `-o, --output-dir PATH`: Output directory for schema documentation
- `-f, --format [markdown|html|json]`: Output format (default: markdown)
- `--include-flows/--no-flows`: Include data flow analysis

### All Command
Run the full pipeline: extract, parse, decompile, generate.

```bash
python main.py all [OPTIONS]
```

**Options:**
- `--pbl-input-dir PATH`: Input directory with PBL/PBD files
- `--base-output-dir PATH`: Base directory for all output
- `--debug`: Enable debug logging
- `--enable-byte-recovery`: Enable byte-level recovery

### Performance Commands

#### extract-streaming
Extract PBD files using streaming for better memory efficiency.

```bash
python main.py extract-streaming [OPTIONS] INPUT_PATH OUTPUT_PATH
```

**Options:**
- `--streaming/--no-streaming`: Use streaming extraction (default: enabled)
- `--async/--sync`: Use async extraction
- `--chunk-size INT`: Chunk size for streaming (default: 8192)

#### all-parallel
Run full pipeline with performance optimizations.

```bash
python main.py all-parallel [OPTIONS] INPUT_PATH OUTPUT_PATH
```

**Options:**
- `--target [flutter|python|typescript]`: Target language (default: flutter)
- `--parallel/--sequential`: Run stages in parallel (default: enabled)
- `--async/--sync`: Use async pipeline
- `--cache/--no-cache`: Enable AST caching (default: enabled)
- `--streaming/--no-streaming`: Use streaming (default: enabled)

### Utility Commands

#### clean-output
Clean specific output directories.

```bash
python main.py clean-output [OPTIONS] [TARGET_DIR]
```

**Options:**
- `--force`: Actually delete files (without this, only lists)
- `--full-recovery`: Target recovery directory
- `--full-extracted`: Target extracted directory
- `--full-decompiled`: Target decompiled directory
- `--full-parsed`: Target parsed directory
- `--test-outputs`: Clean all test_* directories

#### cache-stats
Display cache statistics.

```bash
python main.py cache-stats [OPTIONS]
```

**Options:**
- `--size INT`: Maximum cache entries (default: 1000)
- `--memory INT`: Maximum cache memory in MB (default: 512)

## Pipeline Coordinator

### Class: `PipelineCoordinator`

Main entry point for PowerBuilder to Flutter conversion.

```python
from src.common.pipeline.pipeline_coordinator import PipelineCoordinator

coordinator = PipelineCoordinator(
    input_dir="path/to/pb/files",
    output_dir="path/to/output"
)
```

#### Methods

##### `process_directory(directory: str) -> dict`

Process all PowerBuilder files in a directory.

**Parameters:**
- `directory` (str): Path to directory containing PowerBuilder files

**Returns:**
- `dict`: Result dictionary with keys:
  - `status` (str): 'success', 'partial_success', or 'failed'
  - `stages` (dict): Results from each pipeline stage
  - `statistics` (dict): Conversion statistics
  - `errors` (list): List of errors encountered

**Example:**
```python
result = coordinator.process_directory("/path/to/pb/project")
if result['status'] == 'success':
    print(f"Converted {result['statistics']['total_files']} files")
```

##### `process_file(file_path: str, output_dir: str) -> dict`

Process a single PowerBuilder file.

**Parameters:**
- `file_path` (str): Path to PowerBuilder file
- `output_dir` (str): Output directory for generated files

**Returns:**
- `dict`: Processing result

### Advanced Pipeline Configuration

```python
coordinator = PipelineCoordinator(
    input_dir="input/",
    output_dir="output/",
    options={
        'strict_parsing': False,
        'enable_recovery': True,
        'parallel_processing': True,
        'max_workers': 4
    }
)
```

## Extraction API

### Function: `extract_pbls`

Extract PowerBuilder library files.

```python
from src.extract.core_coordinator import extract_pbls

extracted_files = extract_pbls(
    pbl_files=["app.pbl", "windows.pbl"],
    output_dir="extracted/"
)
```

**Parameters:**
- `pbl_files` (list[str]): List of PBL/PBD file paths
- `output_dir` (str): Output directory
- `show_progress` (bool): Show progress bar (default: True)
- `enable_recovery` (bool): Enable corrupted file recovery (default: True)

**Returns:**
- `list[str]`: List of extracted file paths

### Function: `extract_with_recovery`

Extract with enhanced error recovery.

```python
from src.extract.core_coordinator import extract_with_recovery

result = extract_with_recovery(
    file_path="corrupted.pbl",
    output_dir="recovered/",
    recovery_options={
        'aggressive': True,
        'reconstruct_headers': True
    }
)
```

### Extract Module (Detailed)

```python
from src.extract.core_coordinator import extract_pbls
from src.extract.pbd.extractors.base import extract_pbl

# Extract multiple PBL files
results = extract_pbls(
    input_dir="path/to/pbls",
    output_dir="path/to/output",
    enable_byte_recovery=True
)

# Extract single PBL file
extract_pbl(
    pbl_path="path/to/file.pbl",
    output_dir="path/to/output",
    show_progress=True,
    extract_resources=True
)
```

## Parsing API

### Class: `PowerBuilderParser`

Parse PowerBuilder source code to AST.

```python
from src.parse.parse_coordinator import PowerBuilderParser

parser = PowerBuilderParser()
ast = parser.parse_file("window.srw")
```

#### Methods

##### `parse_file(file_path: str) -> ParseResult`

Parse a PowerBuilder source file.

**Parameters:**
- `file_path` (str): Path to source file

**Returns:**
- `ParseResult`: Object containing:
  - `ast`: Abstract syntax tree
  - `object_type`: Type of PowerBuilder object
  - `metadata`: Additional parsing metadata

##### `parse(source_code: str, object_type: str = None) -> ParseResult`

Parse PowerBuilder source code string.

**Parameters:**
- `source_code` (str): PowerBuilder source code
- `object_type` (str): Optional object type hint

### Class: `DataWindowParser`

Specialized parser for DataWindow syntax.

```python
from src.parse.parse_coordinator import DataWindowParser

dw_parser = DataWindowParser()
dw_definition = dw_parser.parse_datawindow(dw_syntax)
```

### Parse Module (Detailed)

```python
from src.parse.parse_coordinator import parse_powerbuilder_directory
from src.parse.parser.powerbuilder import PowerBuilderParser

# Parse directory of source files
parsed_data = parse_powerbuilder_directory(
    input_path="path/to/sources",
    output_path="path/to/output"
)

# Parse single file
parser = PowerBuilderParser()
ast = parser.parse_file("path/to/file.srw")
```

## Decompilation API

### Decompile Module

```python
from src.decompile.decompile_coordinator import decompile_directory
from src.decompile.pcode.decoder import PCodeDecoder

# Decompile directory
decompile_directory(
    input_dir="path/to/pcode",
    output_dir="path/to/output"
)

# Decompile single file
decoder = PCodeDecoder()
result = decoder.decode_file("path/to/file.fun")
```

## Code Generation API

### Class: `FlutterGenerator`

Generate Flutter code from PowerBuilder AST.

```python
from src.generate.generate_coordinator import FlutterGenerator

generator = FlutterGenerator(
    template_dir="templates/",
    output_dir="flutter_app/"
)
```

#### Methods

##### `generate_screen(window_ast: Window) -> str`

Generate Flutter screen from window AST.

**Parameters:**
- `window_ast` (Window): Window AST node

**Returns:**
- `str`: Path to generated screen file

##### `generate_widget(user_object_ast: UserObject) -> str`

Generate Flutter widget from user object.

##### `generate_model(structure_ast: Structure) -> str`

Generate Dart model class from structure.

### Class: `ModelGenerator`

Generate backend models and services.

```python
from src.generate.generate_coordinator import ModelGenerator

model_gen = ModelGenerator(
    template_dir="templates/backend/",
    output_dir="backend/"
)
```

### Generate Module (Detailed)

```python
from src.generate.generate_coordinator import (
    generate_models,
    generate_services,
    generate_flutter
)

# Generate database models
generate_models("path/to/parsed")

# Generate service layer
generate_services("path/to/parsed", "path/to/decompiled")

# Generate Flutter UI
generate_flutter("path/to/parsed")
```

## Model Classes

### Window

Represents a PowerBuilder window.

```python
from src.model.ast import Window

window = Window(
    name="w_main",
    title="Main Window",
    width=800,
    height=600,
    controls=[],
    events=[],
    methods=[]
)
```

**Attributes:**
- `name` (str): Window name
- `title` (str): Window title
- `width` (int): Width in pixels
- `height` (int): Height in pixels
- `controls` (list[Control]): Child controls
- `events` (list[Event]): Event handlers
- `methods` (list[Function]): Window methods

### DataWindow

Represents a PowerBuilder DataWindow.

```python
from src.model.entities import DataWindow

dw = DataWindow(
    name="d_employee",
    columns=[],
    sql="SELECT * FROM employee",
    presentation_style="grid"
)
```

**Attributes:**
- `name` (str): DataWindow name
- `columns` (list[DataWindowColumn]): Column definitions
- `sql` (str): SQL SELECT statement
- `presentation_style` (str): Display style

### Function

Represents a function or method.

```python
from src.model.ast import Function

func = Function(
    name="calculate",
    return_type=Type("integer"),
    parameters=[],
    body=Block([])
)
```

## Utility Functions

### Type Conversion

```python
from src.generate.converters.utils.type_converter import TypeConverter

converter = TypeConverter()
dart_type = converter.convert_type("integer")  # Returns "int"
```

### Expression Conversion

```python
from src.generate.converters.utils.expression_converter import ExpressionConverter

expr_converter = ExpressionConverter()
dart_expr = expr_converter.convert_expression("a + b * 2")
```

### Progress Tracking

```python
from src.common.pipeline.progress import ProgressTracker

tracker = ProgressTracker()
tracker.start_task("extraction", "Extracting files", total=100)
tracker.update_task("extraction", advance=10)
tracker.complete_task("extraction")
```

## Configuration

### Environment Variables

- `PB_PARSER_ERROR_RECOVERY`: Enable parser error recovery (true/false)
- `PB_PARSER_TYPE`: Parser type (earley/lalr)
- `PB_PARSER_MAX_ERRORS`: Maximum parser errors to collect

### Resource Limits

```python
from src.common.limits import ResourceLimits, ResourceMonitor

# Configure limits
limits = ResourceLimits(
    max_file_size=100 * 1024 * 1024,  # 100MB
    max_memory_usage=2 * 1024 * 1024 * 1024,  # 2GB
    max_files_open=100,
    max_extraction_time=3600  # 1 hour
)

# Monitor resource usage
with ResourceMonitor(limits) as monitor:
    # Your processing code here
    pass
```

### Security Configuration

```python
from src.common.security import SecurityConfig

config = SecurityConfig(
    validate_paths=True,
    sanitize_filenames=True,
    max_path_depth=10,
    allowed_extensions=['.pbl', '.pbd', '.srw', '.sru']
)
```

## Error Handling

All API functions may raise the following exceptions:

- `ExtractError`: Extraction failures
- `ParseError`: Parsing failures
- `DecompileError`: Decompilation failures
- `GenerateError`: Code generation failures
- `PipelineError`: General pipeline failures

Example error handling:

```python
from src.common.exceptions import (
    ExtractError,
    ParseError,
    DecompileError,
    GenerateError,
    PipelineError
)

try:
    result = coordinator.process_file("app.pbl")
except ExtractError as e:
    print(f"Extraction failed: {e}")
except ParseError as e:
    print(f"Parsing failed: {e}")
except DecompileError as e:
    print(f"Decompilation failed: {e}")
except GenerateError as e:
    print(f"Code generation failed: {e}")
except PipelineError as e:
    print(f"Pipeline failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Progress Tracking

```python
from src.common.pipeline.progress import PipelineProgress

# Create progress tracker
progress = PipelineProgress(total_steps=5)

# Track progress
progress.start_step("Extracting files", 1)
# ... do work ...
progress.complete_step(1)

# Get progress info
current = progress.get_current_progress()
print(f"Progress: {current['percentage']}%")
```

## Examples

### Complete Conversion Example

```python
from src.common.pipeline.pipeline_coordinator import PipelineCoordinator
from src.core.logging import configure_pipeline_logging

# Configure logging
configure_pipeline_logging(verbose=True)

# Create pipeline
pipeline = PipelineCoordinator(
    input_dir="powerbuilder_project/",
    output_dir="flutter_output/"
)

# Run conversion
result = pipeline.process_directory("powerbuilder_project/")

# Check results
if result['status'] == 'success':
    print("Conversion successful!")
    print(f"Files converted: {result['statistics']['total_files']}")
    print(f"Output directory: flutter_output/")
else:
    print("Conversion failed or partially failed")
    for error in result.get('errors', []):
        print(f"Error: {error}")
```

### Custom Processing Example

```python
from src.extract.core_coordinator import extract_pbls
from src.parse.parse_coordinator import PowerBuilderParser
from src.generate.generate_coordinator import FlutterGenerator

# Step 1: Extract
files = extract_pbls(["app.pbl"], "temp/")

# Step 2: Parse
parser = PowerBuilderParser()
asts = {}
for file in files:
    result = parser.parse_file(file)
    asts[file] = result.ast

# Step 3: Generate
generator = FlutterGenerator("templates/", "output/")
for file, ast in asts.items():
    if ast.object_type == "window":
        generator.generate_screen(ast)
    elif ast.object_type == "datawindow":
        generator.generate_datawindow_widget(ast)
```

### Logging Configuration Example

```python
from src.core.logging import configure_pipeline_logging

configure_pipeline_logging(
    verbose=True,
    log_file="conversion.log",
    max_message_length=500
)
```

## Version Information

- API Version: 1.0.0
- PowerBuilder Support: 6.x - 12.5
- Flutter Support: 3.x
- Dart SDK: 3.x

## Support

For issues or questions:
- GitHub Issues: https://github.com/powerrebuilder/issues
- Documentation: https://powerrebuilder.readthedocs.io
