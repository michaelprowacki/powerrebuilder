# Vertical Slice Architecture for PowerRebuilder

## Overview

PowerRebuilder has been restructured to follow a **Vertical Slice Architecture** with functional domain modeling. Each pipeline stage (extract, decompile, parse, model, generate) is now a cohesive slice with its own domain, application, and infrastructure layers.

## Architecture Principles

1. **Domain files = business functions**: Pure functions, no I/O
2. **Types live near use**: Types defined in `shared.py` within each slice
3. **No repositories**: Specific read models and write stores instead
4. **Ports in app**: Small, specific interfaces using domain types
5. **Workflows are plain functions**: One file per use case with inline DTOs
6. **Mirror slices**: domain/extract/, app/extract/, infra/extract/
7. **ADTs**: Use enums for choices, frozen dataclasses for values
8. **Errors**: Domain errors stay in domain, app wraps infra errors

## Directory Structure

```
src_new/
├── domain/          # Pure business logic (no I/O)
│   ├── extract/
│   │   ├── extract_pbl.py      # Extract from PBL files
│   │   ├── extract_pbd.py      # Extract from PBD files
│   │   └── shared.py           # PBLEntry, ObjectType
│   ├── decompile/
│   │   ├── decompile_pcode.py  # P-code to source
│   │   └── shared.py           # Instruction, OpcodeType
│   └── [parse, model, generate]/
│
├── app/             # Workflows and ports
│   ├── extract/
│   │   ├── ports.py            # IFileReader, IObjectWriter
│   │   └── extract_library.py  # Main workflow with DTO
│   ├── shared/
│   │   └── services.py         # Cross-cutting: ILogger, ICache
│   └── [decompile, parse, model, generate]/
│
└── infra/           # Adapters and I/O
    ├── extract/
    │   ├── read_models/
    │   │   └── library_metadata.py
    │   └── write_stores/
    │       └── extracted_objects.py
    └── [decompile, parse, model, generate]/
```

## Implementation Example: Extract Slice

### Domain Layer (Pure Functions)
```python
# domain/extract/extract_pbl.py
def extract_objects(data: bytes) -> Tuple[List[PBLEntry], List[ExtractionError]]:
    """Pure function: bytes -> domain objects"""
    header = parse_header(data)
    entries = []
    errors = []
    # ... pure transformation logic
    return entries, errors
```

### Application Layer (Workflow)
```python
# app/extract/extract_library.py
@dataclass
class ExtractLibraryDTO:
    library_path: str
    output_dir: str

async def run(dto, file_reader, object_writer) -> Tuple[Result, List[Event]]:
    """Workflow orchestrates I/O with domain logic"""
    data = await file_reader.read_binary(dto.library_path)
    entries, errors = extract_pbl.extract_objects(data)
    await object_writer.write_entries(dto.output_dir, entries)
    return result, events
```

### Infrastructure Layer (Adapters)
```python
# infra/extract/write_stores/extracted_objects.py
class DiskObjectWriter:
    """Adapter for disk I/O"""
    async def write_entries(self, dir: str, entries: List[PBLEntry]):
        # Actual file I/O here
```

## Benefits

1. **Cohesion**: Everything about a feature stays together
2. **Testability**: Pure domain functions are trivial to test
3. **Flexibility**: Easy to swap adapters (disk, cloud, memory)
4. **Clarity**: Clear separation between business logic and I/O
5. **Maintainability**: Changes to one slice don't affect others

## Migration Status

- ✅ Extract slice implemented
- 🚧 Decompile slice (partial)
- ⏳ Parse slice (pending)
- ⏳ Model slice (pending)
- ⏳ Generate slice (pending)

## Usage

```bash
# Test the new architecture
uv run python src_new/test_vertical.py

# Run extraction with new architecture
uv run python src_new/main_vertical.py extract input.pbl output/
```

## Next Steps

1. Complete remaining slices (parse, model, generate)
2. Wire up full pipeline in main_vertical.py
3. Migrate existing functionality from monolithic files
4. Add comprehensive tests for each slice
5. Remove old pattern-based code once migration complete
