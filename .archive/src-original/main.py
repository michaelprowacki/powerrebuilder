#!/usr/bin/env python
"""PowerRebuilder - Main Entry Point.

A tool for reverse engineering PowerBuilder applications into modern codebases.
Following Scott Wlaschin's Functional Domain Modeling principles.
"""

import sys


def main():
    """Main entry point for PowerRebuilder."""
    print("PowerRebuilder - FDM Architecture")
    print("=" * 50)
    print("\nA tool for transforming PowerBuilder applications to modern code")
    print("\nUsage:")
    print("  python src_new/main.py extract <pbl_file> <output_dir>")
    print("  python src_new/main.py parse <source_dir> <output_dir>")
    print("  python src_new/main.py generate <model_dir> <output_dir>")
    print("\nPipeline stages:")
    print("  1. Extract: PBL/PBD → P-code files")
    print("  2. Decompile: P-code → PowerScript source")
    print("  3. Parse: PowerScript → AST")
    print("  4. Model: AST → Semantic models")
    print("  5. Generate: Models → Flutter/Python")

    if len(sys.argv) > 1:
        command = sys.argv[1]
        print(f"\nCommand '{command}' not yet implemented in FDM version")
        print("Use the old main.py for now, or implement the command here")

    return 0


if __name__ == "__main__":
    sys.exit(main())
