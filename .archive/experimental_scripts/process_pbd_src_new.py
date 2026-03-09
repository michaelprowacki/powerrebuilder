#!/usr/bin/env python3
"""
Process PBD files using src_new pipeline.

This script uses the working src_new modules to extract and process
PowerBuilder PBD files through the complete pipeline.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

# Add src_new to path
sys.path.insert(0, "src_new")

# Import src_new modules
from extract import AdvancedPBLExtractor
from decompile import DecompileCoordinator
from parse.parser import PowerBuilderParser
from model import ModelCoordinator
from generate import GenerateCoordinator
from _core import TargetLanguage

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("pbd_src_new.log")],
)
logger = logging.getLogger(__name__)


class PBDPipeline:
    """Complete pipeline for PBD processing using src_new."""

    def __init__(self, output_base: Path):
        """Initialize pipeline.

        Args:
            output_base: Base directory for output
        """
        self.output_base = Path(output_base)
        self.results = {
            "files_processed": [],
            "stages": {
                "extract": {"success": 0, "failed": 0},
                "decompile": {"success": 0, "failed": 0},
                "parse": {"success": 0, "failed": 0},
                "model": {"success": 0, "failed": 0},
                "generate": {"success": 0, "failed": 0},
            },
            "errors": [],
            "start_time": None,
            "end_time": None,
        }

    def process_file(self, pbd_file: Path) -> Dict:
        """Process a single PBD file through all stages.

        Args:
            pbd_file: Path to PBD file

        Returns:
            Processing results for this file
        """
        file_result = {
            "file": str(pbd_file),
            "size": pbd_file.stat().st_size,
            "stages": {},
            "success": False,
        }

        # Create output directory for this file
        file_base = pbd_file.stem
        file_output = self.output_base / file_base
        file_output.mkdir(parents=True, exist_ok=True)

        logger.info(f"\nProcessing: {pbd_file.name}")
        logger.info(f"Output: {file_output}")

        # Stage 1: Extract
        extract_output = file_output / "1_extracted"
        extract_success = self.run_extract(pbd_file, extract_output)
        file_result["stages"]["extract"] = extract_success
        self.results["stages"]["extract"][
            "success" if extract_success else "failed"
        ] += 1

        if not extract_success:
            logger.warning(
                f"Extraction failed for {pbd_file.name}, skipping remaining stages"
            )
            return file_result

        # Stage 2: Decompile
        decompile_output = file_output / "2_decompiled"
        decompile_success = self.run_decompile(extract_output, decompile_output)
        file_result["stages"]["decompile"] = decompile_success
        self.results["stages"]["decompile"][
            "success" if decompile_success else "failed"
        ] += 1

        # Stage 3: Parse (may fail due to grammar issues)
        parse_output = file_output / "3_parsed"
        parse_success = self.run_parse(decompile_output, parse_output)
        file_result["stages"]["parse"] = parse_success
        self.results["stages"]["parse"]["success" if parse_success else "failed"] += 1

        # Stage 4: Model (if parse succeeded)
        if parse_success:
            model_output = file_output / "4_models"
            model_success = self.run_model(parse_output, model_output)
            file_result["stages"]["model"] = model_success
            self.results["stages"]["model"][
                "success" if model_success else "failed"
            ] += 1

            # Stage 5: Generate (if model succeeded)
            if model_success:
                generate_output = file_output / "5_generated"
                generate_success = self.run_generate(model_output, generate_output)
                file_result["stages"]["generate"] = generate_success
                self.results["stages"]["generate"][
                    "success" if generate_success else "failed"
                ] += 1

                file_result["success"] = generate_success

        return file_result

    def run_extract(self, input_path: Path, output_path: Path) -> bool:
        """Run extraction stage.

        Args:
            input_path: PBD file path
            output_path: Output directory

        Returns:
            True if successful
        """
        try:
            logger.info("  Stage 1: Extracting...")
            output_path.mkdir(parents=True, exist_ok=True)

            # Since our PBD files use HDR* format, use custom extraction
            extracted_count = self.extract_hdr_format(input_path, output_path)

            if extracted_count > 0:
                logger.info(f"    ✓ Extracted {extracted_count} sections")
                return True

            # Fallback to AdvancedPBLExtractor
            logger.info("    Trying AdvancedPBLExtractor with recovery...")
            extractor = AdvancedPBLExtractor(enable_recovery=True)
            objects = extractor.extract_with_recovery(input_path, output_path)

            if objects:
                logger.info(f"    ✓ Extracted {len(objects)} objects")
                return True
            else:
                logger.error("    ✗ No files extracted")
                return False

        except Exception as e:
            logger.error(f"    ✗ Extraction failed: {e}")
            self.results["errors"].append(
                {"file": str(input_path), "stage": "extract", "error": str(e)}
            )
            return False

    def extract_hdr_format(self, pbd_file: Path, output_dir: Path) -> int:
        """Extract HDR* format PBD files.

        Args:
            pbd_file: Input PBD file
            output_dir: Output directory

        Returns:
            Number of sections extracted
        """

        with open(pbd_file, "rb") as f:
            data = f.read()

        extracted = 0
        markers = [b"HDR*", b"ENT*", b"DAT*", b"NOD*", b"FRE*"]

        # Find and extract each section type
        for marker in markers:
            offset = 0
            while offset < len(data) - 4:
                pos = data.find(marker, offset)
                if pos == -1:
                    break

                # Find next marker to determine section size
                next_pos = len(data)
                for next_marker in markers:
                    next_marker_pos = data.find(next_marker, pos + 4)
                    if next_marker_pos != -1 and next_marker_pos < next_pos:
                        next_pos = next_marker_pos

                # Extract section
                section_data = data[pos:next_pos]
                if len(section_data) > 4:
                    # Save section
                    filename = f"{marker.decode('ascii', 'ignore')}_{pos:08x}.fun"
                    output_file = output_dir / filename
                    output_file.write_bytes(section_data)
                    extracted += 1

                offset = pos + 4

        return extracted

    def run_decompile(self, input_path: Path, output_path: Path) -> bool:
        """Run decompile stage.

        Args:
            input_path: Directory with extracted files
            output_path: Output directory

        Returns:
            True if successful
        """
        try:
            logger.info("  Stage 2: Decompiling...")
            output_path.mkdir(parents=True, exist_ok=True)

            # Get all .fun files
            fun_files = list(input_path.glob("*.fun"))
            if not fun_files:
                logger.warning("    No .fun files to decompile")
                return False

            coordinator = DecompileCoordinator(input_path, output_path)

            # Process each .fun file
            success_count = 0
            for fun_file in fun_files:
                if coordinator.process_file(fun_file, output_path):
                    success_count += 1

            # Check for output files
            output_files = list(output_path.glob("*.sr*"))
            if output_files:
                logger.info(f"    ✓ Decompiled to {len(output_files)} source files")
                return True
            else:
                logger.warning("    ✗ No source files generated")
                return False

        except Exception as e:
            logger.error(f"    ✗ Decompile failed: {e}")
            self.results["errors"].append({"stage": "decompile", "error": str(e)})
            return False

    def run_parse(self, input_path: Path, output_path: Path) -> bool:
        """Run parse stage.

        Args:
            input_path: Directory with source files
            output_path: Output directory

        Returns:
            True if successful
        """
        try:
            logger.info("  Stage 3: Parsing...")
            output_path.mkdir(parents=True, exist_ok=True)

            # Get source files
            source_files = list(input_path.glob("*.sr*"))
            if not source_files:
                logger.warning("    No source files to parse")
                return False

            parser = PowerBuilderParser()
            parsed_count = 0

            for source_file in source_files:
                try:
                    content = source_file.read_text(encoding="utf-8", errors="ignore")
                    result = parser.parse(content)

                    if result.success:
                        # Save AST
                        ast_file = output_path / f"{source_file.stem}.json"
                        ast_data = {
                            "source": source_file.name,
                            "ast": self._ast_to_dict(result.ast),
                        }
                        ast_file.write_text(json.dumps(ast_data, indent=2))
                        parsed_count += 1
                except Exception as e:
                    logger.debug(f"    Failed to parse {source_file.name}: {e}")

            if parsed_count > 0:
                logger.info(f"    ✓ Parsed {parsed_count}/{len(source_files)} files")
                return True
            else:
                logger.warning("    ✗ No files successfully parsed")
                return False

        except Exception as e:
            logger.error(f"    ✗ Parse failed: {e}")
            self.results["errors"].append({"stage": "parse", "error": str(e)})
            return False

    def run_model(self, input_path: Path, output_path: Path) -> bool:
        """Run model building stage.

        Args:
            input_path: Directory with AST files
            output_path: Output directory

        Returns:
            True if successful
        """
        try:
            logger.info("  Stage 4: Building models...")
            output_path.mkdir(parents=True, exist_ok=True)

            coordinator = ModelCoordinator(input_path, output_path)
            result = coordinator.execute()

            # Check for model files
            model_files = list(output_path.glob("*.json"))
            if model_files:
                logger.info(f"    ✓ Created {len(model_files)} model files")
                return True
            else:
                logger.warning("    ✗ No models generated")
                return False

        except Exception as e:
            logger.error(f"    ✗ Model building failed: {e}")
            self.results["errors"].append({"stage": "model", "error": str(e)})
            return False

    def run_generate(self, input_path: Path, output_path: Path) -> bool:
        """Run code generation stage.

        Args:
            input_path: Directory with model files
            output_path: Output directory

        Returns:
            True if successful
        """
        try:
            logger.info("  Stage 5: Generating code...")
            output_path.mkdir(parents=True, exist_ok=True)

            coordinator = GenerateCoordinator(input_path, output_path)
            coordinator.target = TargetLanguage.DART  # Generate Flutter/Dart
            result = coordinator.execute()

            # Check for generated files
            generated_files = list(output_path.rglob("*.*"))
            if generated_files:
                logger.info(f"    ✓ Generated {len(generated_files)} files")
                return True
            else:
                logger.warning("    ✗ No code generated")
                return False

        except Exception as e:
            logger.error(f"    ✗ Code generation failed: {e}")
            self.results["errors"].append({"stage": "generate", "error": str(e)})
            return False

    def _ast_to_dict(self, ast) -> Dict:
        """Convert AST to dictionary.

        Args:
            ast: AST node

        Returns:
            Dictionary representation
        """
        if ast is None:
            return None

        result = {
            "type": getattr(ast, "node_type", "unknown"),
        }

        if hasattr(ast, "value"):
            result["value"] = ast.value

        if hasattr(ast, "children"):
            result["children"] = [self._ast_to_dict(child) for child in ast.children]

        return result

    def process_all(self, pbd_dir: Path, test_mode: bool = False) -> Dict:
        """Process all PBD files in directory.

        Args:
            pbd_dir: Directory containing PBD files
            test_mode: If True, only process 3 smallest files

        Returns:
            Complete results
        """
        self.results["start_time"] = datetime.now().isoformat()

        # Get PBD files
        pbd_files = sorted(pbd_dir.glob("*.pbd"), key=lambda f: f.stat().st_size)

        if test_mode:
            pbd_files = pbd_files[:3]
            logger.info(f"TEST MODE: Processing {len(pbd_files)} smallest files")
        else:
            logger.info(f"Processing {len(pbd_files)} PBD files")

        # Process each file
        for pbd_file in pbd_files:
            file_result = self.process_file(pbd_file)
            self.results["files_processed"].append(file_result)

        self.results["end_time"] = datetime.now().isoformat()

        # Calculate summary statistics
        self.results["summary"] = {
            "total_files": len(pbd_files),
            "successful": sum(
                1 for f in self.results["files_processed"] if f.get("success")
            ),
            "total_size_mb": sum(f["size"] for f in self.results["files_processed"])
            / 1024
            / 1024,
        }

        # Save results
        self.save_results()

        return self.results

    def save_results(self):
        """Save processing results to JSON."""
        report_file = self.output_base / "pipeline_results.json"
        report_file.write_text(json.dumps(self.results, indent=2))
        logger.info(f"\nResults saved to: {report_file}")

        # Print summary
        print("\n" + "=" * 60)
        print("PIPELINE SUMMARY")
        print("=" * 60)
        print(f"Total files: {self.results['summary']['total_files']}")
        print(f"Successful: {self.results['summary']['successful']}")
        print(f"Total size: {self.results['summary']['total_size_mb']:.2f} MB")
        print("\nStage Results:")
        for stage, stats in self.results["stages"].items():
            total = stats["success"] + stats["failed"]
            if total > 0:
                rate = (stats["success"] / total) * 100
                print(f"  {stage}: {stats['success']}/{total} ({rate:.1f}%)")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Process PBD files with src_new pipeline"
    )
    parser.add_argument(
        "--input-dir", default="data/pbd_files", help="Directory containing PBD files"
    )
    parser.add_argument(
        "--output-dir", default="output/src_new_pipeline", help="Output directory"
    )
    parser.add_argument(
        "--test", action="store_true", help="Test mode: process only 3 smallest files"
    )

    args = parser.parse_args()

    # Create pipeline
    pipeline = PBDPipeline(output_base=Path(args.output_dir))

    # Process files
    results = pipeline.process_all(pbd_dir=Path(args.input_dir), test_mode=args.test)

    # Exit with appropriate code
    if results["summary"]["successful"] == results["summary"]["total_files"]:
        sys.exit(0)  # All successful
    elif results["summary"]["successful"] > 0:
        sys.exit(1)  # Partial success
    else:
        sys.exit(2)  # All failed


if __name__ == "__main__":
    main()
