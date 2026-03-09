# Domain-Driven Filename Changes

This document tracks the filename changes made to follow Scott Wlaschin's functional domain modeling principles and PowerBuilder domain language.

## Core Principle
Filenames should use the domain expert's language (PowerBuilder developers) rather than generic computer science terminology.

## Domain Module Renames

### Extract Domain
- `extract_pbl.py` → `read_pbl_library.py`
- `extract_pbd.py` → `read_pbd_library.py`
- `analyze_binary.py` → `inspect_pbl_structure.py`
- `functional_extract.py` → `pbl_extraction_workflow.py`
- `extract_pbl_functional.py` → `pbl_library_workflow.py`

### Parse Domain
- `parse_source.py` → `parse_powerscript.py`
- `parse_datawindow.py` → `parse_datawindow_syntax.py`

### Decompile Domain
- `decompile_pcode.py` → `pcode_to_powerscript.py`

### Model Domain
- `build_model.py` → `powerbuilder_application_model.py`
- `symbol_resolution.py` → `resolve_powerbuilder_inheritance.py`
- `analyze_complexity.py` → `measure_powerbuilder_complexity.py`
- `analyze_database.py` → `map_datawindow_relationships.py`

### Generate Domain (Migration)
- `generate_flutter.py` → `migrate_to_flutter.py`
- `generate_tauri.py` → `migrate_to_tauri.py`
- `generate_dioxus.py` → `migrate_to_dioxus.py`
- `generate_tests.py` → `create_powerbuilder_tests.py`
- `generate_dockerfile.py` → `create_deployment_container.py`
- `enhance_with_ai.py` → `optimize_migrated_code.py`

## Generate Module Renames
- `flutter.py` → `flutter_migration.py`
- `tauri.py` → `tauri_migration.py`
- `dioxus.py` → `dioxus_migration.py`
- `portable_patterns.py` → `powerbuilder_pattern_library.py`

## Application Layer Renames
- `extract_library.py` → `powerbuilder_library_service.py`
- `parse_to_ast.py` → `powerscript_parsing_service.py`

## Why These Changes?

1. **Domain Language**: Uses PowerBuilder terminology (PBL, PowerScript, DataWindow) instead of generic terms (extract, parse, generate)

2. **Intention-Revealing**: Names like `pcode_to_powerscript.py` clearly express the transformation being performed

3. **Business Capabilities**: Names like `migrate_to_flutter.py` describe the business capability, not the technical implementation

4. **No Technical Jargon**: Avoided terms like "parser", "extractor", "generator" unless they are part of the PowerBuilder domain language

## Result

The codebase now speaks the language of PowerBuilder developers, making it more maintainable and understandable for domain experts, following Scott Wlaschin's principle:

> "The code should use the domain expert's language"
