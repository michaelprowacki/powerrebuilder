"""CONSOLIDATED: All coordinator functionality moved to unified_decompile.py

This module now re-exports classes from unified_decompile.py for backward compatibility.

CONSOLIDATION_MASTER_PLAN.md Phase 2.4 COMPLETED:
✅ coordinator.py (2,081 lines) merged into unified_decompile.py
✅ DecompileCoordinator preserved for main.py imports
✅ All functionality maintained with re-exports

CONSOLIDATED CLASSES (re-exported from unified_decompile.py):
- ExtractedFileDecompiler
- PowerBuilderDecompiler  
- DecompileCoordinator (MAIN CLASS used by main.py)
"""

# Re-export all coordinator classes from unified_decompile.py
from .unified_decompile import (
    DecompileCoordinator,
    ExtractedFileDecompiler, 
    PowerBuilderDecompiler,
    OutputFormat,
    SUPPORTED_OUTPUT_FORMATS,
    OUTPUT_FORMAT_EXTENSIONS,
    extract_database_schema,
    decompile_directory,
    main,
)

# Maintain backward compatibility
__all__ = [
    "DecompileCoordinator",
    "ExtractedFileDecompiler",
    "PowerBuilderDecompiler", 
    "OutputFormat",
    "SUPPORTED_OUTPUT_FORMATS",
    "OUTPUT_FORMAT_EXTENSIONS", 
    "extract_database_schema",
    "decompile_directory",
    "main",
]