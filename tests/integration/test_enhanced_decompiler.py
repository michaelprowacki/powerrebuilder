#!/usr/bin/env python3
"""Test the enhanced decompiler components."""

import logging
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# from src.decompile.generators.unified_decompiler import UnifiedDecompiler  # Module doesn't exist
from src.decompile.coordinator import PowerBuilderDecompiler as UnifiedDecompiler
from src.extract.pbd.library import Library

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def test_decompile_object(pbd_path: Path, object_name: str) -> None:
    """Test decompiling a specific object from a PBD."""
    logger.info(f"Testing decompilation of {object_name} from {pbd_path.name}")

    try:
        # Open the PBD file
        library = Library(str(pbd_path))

        # Find the object
        if object_name not in library.entries_map:
            logger.error(f"Object {object_name} not found in {pbd_path.name}")
            logger.info(
                f"Available objects: {list(library.entries_map.keys())[:10]}...",
            )
            return

        entry = library.entries_map[object_name]
        logger.info(
            f"Found {entry.objectname} at offset {entry.offset:#x}, size {entry.objectsize}",
        )

        # Create decompiler
        decompiler = UnifiedDecompiler()

        # Open the PBD file for reading
        with open(pbd_path, "rb") as f:
            # Decompile the object
            decoded_obj = decompiler.decompile_object(
                f,
                entry.offset,
                entry.objectsize,
                entry.objectname,
            )

            if decoded_obj:
                logger.info(f"Successfully decompiled {entry.objectname}")

                # Generate output
                from src.decompile.core.output import OutputFormatter

                formatter = OutputFormatter()

                control_blocks = decoded_obj.metadata.get("control_blocks", [])
                output_lines = formatter.format_object(
                    decoded_obj,
                    control_blocks,
                    str(pbd_path),
                )

                # Save output
                output_path = Path(f"output/test_enhanced/{entry.objectname}.pb")
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, "w", encoding="utf-8") as out_f:
                    out_f.write("\n".join(output_lines))

                logger.info(f"Output saved to {output_path}")

                # Print first 50 lines
                for _i, _line in enumerate(output_lines[:50]):
                    pass
                if len(output_lines) > 50:
                    pass

            else:
                logger.error(f"Failed to decompile {entry.objectname}")

    # Test: catch all exceptions to verify error handling
    except Exception as e:
        logger.error(f"Error testing decompiler: {e}", exc_info=True)


def main() -> None:
    """Test the enhanced decompiler on various objects."""
    # Test on a few objects from different PBDs
    test_cases = [
        ("data/input/pbd_files/dcm_accounting.pbd", "of_get_linked_acc.fun"),
        ("data/input/pbd_files/dcm_accounting.pbd", "of_update_coa.fun"),
        ("data/input/pbd_files/dcm_accounting.pbd", "of_tj_report.fun"),
    ]

    for pbd_path, object_name in test_cases:
        pbd_file = Path(pbd_path)
        if pbd_file.exists():
            test_decompile_object(pbd_file, object_name)
        else:
            logger.warning(f"PBD file not found: {pbd_path}")


if __name__ == "__main__":
    main()
