# Extract Module

## Overview

The Extract module is responsible for extracting PowerBuilder source code from compiled PBD (PowerBuilder Dynamic Library) files. It provides the first stage of the SIME Finch pipeline, converting binary PBD files into their constituent source files.

## Structure

```
extract/
├── __init__.py
├── constants.py          # Magic numbers and constants
├── extract_coordinator.py # Orchestrates extraction process
├── pbd/                  # PBD file handling
│   ├── extraction/       # Core extraction logic
│   │   ├── extractor.py  # Main extraction implementation
│   │   └── library.py    # PBD library handling
│   ├── io/              # File I/O operations
│   │   └── file_operations.py
│   ├── structures/      # PBD data structures
│   │   ├── data_block.py
│   │   ├── data_corruption_fix.py
│   │   ├── entry_recovery.py
│   │   ├── header.py
│   │   └── node.py
│   └── utils/           # Utilities
│       └── powerbuilder_decoder.py
└── py.typed             # Type checking marker
```

## Key Components

### ExtractCoordinator
The main orchestrator that manages the extraction process for PBD files.

### PBD Structures
- **Header**: Parses PBD file headers to understand file structure
- **Node**: Represents entries in the PBD file tree
- **DataBlock**: Handles individual data blocks within PBD files
- **EntryRecovery**: Recovers corrupted or malformed entries

### Extraction Process
1. Read PBD file header
2. Parse the file structure tree
3. Extract individual objects (windows, functions, etc.)
4. Handle data corruption and recovery
5. Write extracted source files

## Usage

```python
from extract.extract_coordinator import ExtractCoordinator

coordinator = ExtractCoordinator()
coordinator.extract_pbd("input.pbd", "output_directory/")
```

## Features

- Handles PowerBuilder 10-12.6 PBD files
- Automatic corruption detection and recovery
- Magic number validation for data integrity
- Comprehensive error handling and logging
- Support for all PowerBuilder object types

## Error Recovery

The module includes sophisticated error recovery mechanisms:
- Magic number detection for corrupted data blocks
- Position-based decoding for malformed entries
- Automatic retry with different decoding strategies
- Detailed logging of recovery attempts

## Dependencies

- Python 3.9+
- No external dependencies (uses only standard library)

## Related Modules

- **Parse**: Processes the extracted source files
- **Model**: Creates AST from parsed code
- **Decompile**: Handles binary DataWindow extraction
