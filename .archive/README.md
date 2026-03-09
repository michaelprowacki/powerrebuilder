# Archive Directory

This directory contains experimental scripts and development artifacts that are no longer actively used but may have historical or reference value.

## experimental_scripts/

These scripts were created during development and testing of PowerRebuilder features:

- **analyze_pbd_structure.py** - Early exploration of PBD file format structure
- **extract_metadata.py** - Experiments with extracting metadata from DAT* sections
- **build_object_model.py** - Building object models from extracted metadata
- **generate_modern_code.py** - Early code generation experiments
- **process_all_pbd.py** - Batch processing script for all PBD files
- **process_pbd_src_new.py** - Testing the src_new implementation
- **simple_extract.py** - Simplified extraction for debugging
- **fix_imports.py** - Script to fix import statements in src_new
- **test_*.py** - Various test scripts for pipeline stages
- **PBD_PROCESSING_REPORT.md** - Report from processing DCM system files

These files are kept for reference but should not be used in production. The main pipeline functionality is properly implemented in the `src/` and `src_new/` directories.
