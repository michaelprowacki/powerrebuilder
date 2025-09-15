# Exception Handling Guidelines

This document provides guidelines for using the unified exception hierarchy in the SIME Finch project.

## Exception Hierarchy Overview

All exceptions inherit from `SimeFinchError`, providing a consistent error handling interface across the project.

```
SimeFinchError (Base)
├── ParseError (Parsing phase)
│   ├── GrammarError
│   │   ├── GrammarLoadError
│   │   ├── GrammarParseError
│   │   └── GrammarNotFoundError
│   ├── PowerBuilderSyntaxError
│   └── PreprocessorError
│       ├── MacroError
│       ├── IncludeError
│       └── ConditionalError
├── ExtractError (Extraction phase)
│   └── PbdError
│       ├── HeaderError
│       ├── NodeError
│       ├── EntryError
│       ├── DatError
│       └── PfcExcludedError
├── DecompileError (Decompilation phase)
├── GenerateError (Code generation phase)
├── ModelError (Model operations)
│   ├── ValidationError
│   │   └── TypeValidationError
│   └── ModelGenerationError
├── TransformError (AST transformation)
│   ├── TransformerError
│   └── VisitorError
├── ConfigurationError (Configuration issues)
├── SecurityError (Security-related)
│   └── PathTraversalError
├── PowerBuilderError (PB-specific)
│   └── TransactionError
└── PowerBuilderToolError (High-level pipeline)
    ├── ExtractionError
    ├── ParsingError
    ├── DecompilationError
    └── GenerationError
```

## When to Use Each Exception Type

### Core Component Errors

#### ParseError
Use for errors during parsing of PowerBuilder source code:
```python
from src.common.exceptions import ParseError, PowerBuilderSyntaxError

try:
    tree = parser.parse(source_code)
except UnexpectedCharacters as e:
    raise PowerBuilderSyntaxError(
        f"Invalid syntax at line {e.line}: {e.get_context()}",
        filename=filename,
        line=e.line,
        column=e.column
    ) from e
```

#### ExtractError
Use for errors during PBL/PBD extraction:
```python
from src.common.exceptions import ExtractError, HeaderError, NodeError

try:
    header = extract_pbl_header(file_bytes)
except struct.error as e:
    raise HeaderError(f"Invalid PBL header format: {e}") from e
except IOError as e:
    raise ExtractError(f"Cannot read PBL file: {e}") from e
```

#### DecompileError
Use for errors during P-code decompilation:
```python
from src.common.exceptions import DecompileError

try:
    instructions = decoder.decode_pcode(pcode_bytes)
except struct.error as e:
    raise DecompileError(f"Invalid P-code format: {e}") from e
```

#### GenerateError
Use for errors during code generation:
```python
from src.common.exceptions import GenerateError

try:
    flutter_code = generator.generate_widget(pb_control)
except KeyError as e:
    raise GenerateError(f"Unknown control type: {e}") from e
```

### Validation Errors

#### ValidationError
Use for general validation failures:
```python
from src.common.exceptions import ValidationError

def validate_config(config):
    if not config.get('required_field'):
        raise ValidationError("Missing required field 'required_field'")
```

#### TypeValidationError
Use for type-related validation failures:
```python
from src.common.exceptions import TypeValidationError

def validate_type(value, expected_type):
    if not isinstance(value, expected_type):
        raise TypeValidationError(
            f"Invalid type for value",
            expected_type=expected_type.__name__,
            actual_type=type(value).__name__
        )
```

### Security Errors

#### SecurityError / PathTraversalError
Use for security-related issues:
```python
from src.common.exceptions import PathTraversalError

def validate_path(path, base_dir):
    if '..' in path:
        raise PathTraversalError(f"Path traversal attempt detected: {path}")
```

## Best Practices

### 1. Be Specific
Always use the most specific exception type available:
```python
# Good
raise GrammarLoadError(f"Cannot find grammar file: {grammar_path}")

# Bad
raise Exception(f"Cannot find grammar file: {grammar_path}")
```

### 2. Add Context Information
Use the context parameter to provide additional debugging information:
```python
raise ParseError(
    "Unexpected end of file",
    filename="window.srw",
    line=42,
    column=15,
    source_text=source_line
)
```

### 3. Chain Exceptions
Always chain exceptions to preserve the original error context:
```python
try:
    result = parse_file(filename)
except IOError as e:
    raise ParseError(f"Cannot read file: {filename}") from e  # Good
    # raise ParseError(f"Cannot read file: {filename}")  # Bad - loses context
```

### 4. Handle Specific Exceptions
Catch specific exceptions rather than broad categories:
```python
# Good
try:
    header = extract_header(data)
except HeaderError:
    # Handle header-specific error
    logger.error("Invalid header format")
    return None
except NodeError:
    # Handle node-specific error
    logger.error("Corrupt node structure")
    return None

# Bad
try:
    header = extract_header(data)
except Exception:
    # Too broad - can't handle specific cases
    return None
```

### 5. Use Exception Context
The base `SimeFinchError` stores context information:
```python
try:
    process_file(path)
except SimeFinchError as e:
    # Access context information
    if e.context.get('line'):
        print(f"Error at line {e.context['line']}")

    # Re-raise with additional context
    raise SimeFinchError(
        "Processing failed",
        original_error=str(e),
        file_path=path,
        **e.context
    ) from e
```

## Examples

### Example 1: Parser Error Handling
```python
from src.common.exceptions import (
    ParseError,
    PowerBuilderSyntaxError,
    GrammarLoadError
)

class PowerBuilderParser:
    def parse(self, source_code: str, filename: str = None):
        try:
            # Load grammar
            grammar = self.load_grammar()
        except FileNotFoundError as e:
            raise GrammarLoadError(
                f"Grammar file not found: {e.filename}"
            ) from e

        try:
            # Parse source
            tree = grammar.parse(source_code)
        except UnexpectedCharacters as e:
            raise PowerBuilderSyntaxError(
                f"Syntax error: {e.get_context()}",
                filename=filename,
                line=e.line,
                column=e.column
            ) from e
        except Exception as e:
            # Catch-all for other parsing errors
            raise ParseError(
                f"Failed to parse {filename}: {e}",
                filename=filename
            ) from e
```

### Example 2: Extraction Error Handling
```python
from src.common.exceptions import (
    ExtractError,
    HeaderError,
    NodeError,
    PfcExcludedError
)

class PBDExtractor:
    def extract_object(self, pbd_file: Path, object_name: str):
        try:
            with open(pbd_file, 'rb') as f:
                data = f.read()
        except IOError as e:
            raise ExtractError(
                f"Cannot read PBD file: {pbd_file}",
                file_path=str(pbd_file)
            ) from e

        try:
            header = self.parse_header(data)
        except struct.error as e:
            raise HeaderError(
                f"Invalid PBD header in {pbd_file.name}",
                file_path=str(pbd_file)
            ) from e

        # Check for PFC exclusion
        if self.is_pfc_object(object_name):
            raise PfcExcludedError(
                object_name=object_name,
                hash_value=self.get_hash(object_name)
            )
```

### Example 3: Generation Error Handling
```python
from src.common.exceptions import (
    GenerateError,
    ValidationError,
    ConfigurationError
)

class CodeGenerator:
    def generate(self, ast: dict, config: dict):
        # Validate configuration
        try:
            self.validate_config(config)
        except KeyError as e:
            raise ConfigurationError(
                f"Missing required config: {e}"
            ) from e

        # Generate code
        try:
            template = self.load_template(config['template'])
            return template.render(ast=ast)
        except TemplateNotFound as e:
            raise GenerateError(
                f"Template not found: {e.name}",
                template_name=e.name
            ) from e
        except Exception as e:
            raise GenerateError(
                f"Code generation failed: {e}",
                template=config.get('template')
            ) from e
```

## Migration from Generic Exceptions

To migrate from generic exception handling:

1. Run the migration script:
   ```bash
   python tools/maintenance/update_exceptions.py --update
   ```

2. Review the generated report in `exception_report.md`

3. Manually update complex cases that the script couldn't handle

4. Add imports for specific exceptions:
   ```python
   from src.common.exceptions import (
       ExtractError,
       ParseError,
       DecompileError,
       GenerateError
   )
   ```

5. Test thoroughly to ensure error handling still works correctly

## Testing Exception Handling

When writing tests, verify that the correct exceptions are raised:

```python
import pytest
from src.common.exceptions import HeaderError, NodeError

def test_invalid_header():
    with pytest.raises(HeaderError) as exc_info:
        extract_header(b"invalid data")

    assert "Invalid PBD header" in str(exc_info.value)
    assert exc_info.value.context.get('file_path') == 'test.pbd'

def test_node_error_chaining():
    with pytest.raises(NodeError) as exc_info:
        parse_node(corrupted_data)

    # Verify the cause is preserved
    assert isinstance(exc_info.value.__cause__, struct.error)
```

## Summary

Using specific exceptions provides several benefits:

1. **Better debugging** - Specific exceptions make it easier to identify where errors occur
2. **Proper error handling** - Different error types can be handled differently
3. **Clear API contracts** - Users know what exceptions to expect
4. **Easier testing** - Tests can verify specific error conditions
5. **Better logging** - Log messages can be more specific and actionable

Always strive to use the most specific exception type and provide helpful context information to make debugging easier.
