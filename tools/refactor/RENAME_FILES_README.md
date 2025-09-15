# File Renaming Script

## Overview
The `rename_files.py` script renames files in the codebase to follow the project's naming conventions:

1. **Common module files** - Renames to adjective_noun pattern (e.g., `distributed.py` → `distributed_manager.py`)
2. **Contracts module files** - Adds `_contracts` suffix (e.g., `models.py` → `models_contracts.py`)
3. **Coordinator files** - Adds module prefix (e.g., `parse/coordinator.py` → `parse/parse_coordinator.py`)
4. **Factory files** - Adds module prefix (e.g., `extract/factory.py` → `extract/extract_factory.py`)

## Usage

### Dry Run (Default)
```bash
python tools/refactor/rename_files.py
```

This will:
- Show all files that would be renamed
- Preview import statements that would be updated
- Display any warnings about manual updates needed

### Execute Renaming
```bash
python tools/refactor/rename_files.py --execute
```

This will:
- Create a backup of the `src` directory in `backup_before_rename/`
- Rename all identified files
- Update import statements throughout the codebase
- Report any files where imports were updated

### Additional Options
- `--no-backup` - Skip creating backup (not recommended)
- `--verify` - Run import verification after renaming
- `--project-root <path>` - Specify project root if not running from project directory

## Files to be Renamed (20 total)

### Module Coordinators (8 files)
- `src/decompile/coordinator.py` → `src/decompile/decompile_coordinator.py`
- `src/parse/coordinator.py` → `src/parse/parse_coordinator.py`
- `src/model/coordinator.py` → `src/model/model_coordinator.py`
- `src/generate/coordinator.py` → `src/generate/generate_coordinator.py`
- `src/extract/coordinator.py` → `src/extract/extract_coordinator.py`

### Module Factories (5 files)
- `src/decompile/factory.py` → `src/decompile/decompile_factory.py`
- `src/parse/factory.py` → `src/parse/parse_factory.py`
- `src/model/factory.py` → `src/model/model_factory.py`
- `src/generate/factory.py` → `src/generate/generate_factory.py`
- `src/extract/factory.py` → `src/extract/extract_factory.py`

### Contracts Module (8 files)
- `src/contracts/models.py` → `src/contracts/models_contracts.py`
- `src/contracts/extractors.py` → `src/contracts/extractors_contracts.py`
- `src/contracts/events.py` → `src/contracts/events_contracts.py`
- `src/contracts/decompilers.py` → `src/contracts/decompilers_contracts.py`
- `src/contracts/parsers.py` → `src/contracts/parsers_contracts.py`
- `src/contracts/generators.py` → `src/contracts/generators_contracts.py`
- `src/contracts/pipeline.py` → `src/contracts/pipeline_contracts.py`
- `src/contracts/state.py` → `src/contracts/state_contracts.py`

### Common Module (2 files)
- `src/common/distributed.py` → `src/common/distributed_manager.py`
- `src/common/streaming.py` → `src/common/stream_handler.py`

## Manual Updates Required

After running the script, you'll need to manually update:

1. **src/extract/__init__.py** - Update the import:
   ```python
   # Change from:
   from src.extract.extract_coordinator import ExtractCoordinator
   # To:
   from src.extract.extract_coordinator import ExtractCoordinator
   ```

2. **Any dynamic imports** - The script will warn about files that may use dynamic imports

## Import Updates

The script will automatically update imports in approximately 91 files throughout the codebase, including:
- Direct imports (`import module.coordinator`)
- From imports (`from module.coordinator import Class`)
- String references in quotes (for dynamic imports)

## Safety Features

1. **Dry run by default** - Shows what would change without making changes
2. **Automatic backup** - Creates `backup_before_rename/` before making changes
3. **Import validation** - Updates all import statements automatically
4. **Warning system** - Alerts about files needing manual updates
5. **Verification** - Optional import verification after renaming

## Recovery

If something goes wrong:
1. The backup is saved in `backup_before_rename/`
2. You can restore with: `rm -rf src/ && mv backup_before_rename/src .`
3. Or use git to revert changes: `git checkout -- src/`
