#!/usr/bin/env python3
"""
Batch process all PBD files through the PowerRebuilder pipeline.

This script processes all PBD files in data/pbd_files/ through the complete
5-stage pipeline and generates a comprehensive report.
"""

import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("pbd_processing.log")],
)
logger = logging.getLogger(__name__)


class PBDProcessor:
    """Batch processor for PowerBuilder PBD files."""

    def __init__(self, input_dir: Path, output_dir: Path):
        """Initialize processor.

        Args:
            input_dir: Directory containing PBD files
            output_dir: Base output directory for processed files
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.results = {
            "processed": [],
            "failed": [],
            "stats": {
                "total_files": 0,
                "successful": 0,
                "failed": 0,
                "total_size_bytes": 0,
                "processing_time_seconds": 0,
                "stage_success_rates": {},
            },
        }

    def process_all(self, test_mode: bool = False) -> Dict:
        """Process all PBD files.

        Args:
            test_mode: If True, only process first 3 smallest files

        Returns:
            Processing results dictionary
        """
        start_time = time.time()

        # Get all PBD files
        pbd_files = sorted(self.input_dir.glob("*.pbd"), key=lambda f: f.stat().st_size)

        if test_mode:
            # Process only the 3 smallest files for testing
            pbd_files = pbd_files[:3]
            logger.info("TEST MODE: Processing only 3 smallest files")

        self.results["stats"]["total_files"] = len(pbd_files)

        logger.info(f"Found {len(pbd_files)} PBD files to process")

        for idx, pbd_file in enumerate(pbd_files, 1):
            file_size = pbd_file.stat().st_size
            self.results["stats"]["total_size_bytes"] += file_size

            logger.info(f"\n{'=' * 60}")
            logger.info(f"Processing [{idx}/{len(pbd_files)}]: {pbd_file.name}")
            logger.info(
                f"File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)"
            )
            logger.info(f"{'=' * 60}")

            success = self.process_single_file(pbd_file)

            if success:
                self.results["processed"].append(str(pbd_file))
                self.results["stats"]["successful"] += 1
            else:
                self.results["failed"].append(str(pbd_file))
                self.results["stats"]["failed"] += 1

        self.results["stats"]["processing_time_seconds"] = time.time() - start_time

        # Calculate success rate
        if self.results["stats"]["total_files"] > 0:
            success_rate = (
                self.results["stats"]["successful"]
                / self.results["stats"]["total_files"]
            ) * 100
            self.results["stats"]["overall_success_rate"] = f"{success_rate:.1f}%"

        # Save report
        self.save_report()

        return self.results

    def process_single_file(self, pbd_file: Path) -> bool:
        """Process a single PBD file through all pipeline stages.

        Args:
            pbd_file: Path to PBD file

        Returns:
            True if all stages succeeded, False otherwise
        """
        # Create output directory for this file
        file_base = pbd_file.stem
        file_output_dir = self.output_dir / file_base

        stages = {
            "extract": ("1_extracted", "Extract P-code from PBD"),
            "decompile": ("2_decompiled", "Decompile P-code to source"),
            "parse": ("3_parsed", "Parse source to AST"),
            "model": ("4_models", "Build semantic models"),
            "generate": ("5_generated", "Generate modern code"),
        }

        all_success = True
        stage_results = {}

        for stage_name, (output_subdir, description) in stages.items():
            stage_output = file_output_dir / output_subdir
            stage_output.mkdir(parents=True, exist_ok=True)

            logger.info(f"  Stage: {description}")

            # Determine input path for this stage
            if stage_name == "extract":
                input_path = pbd_file
            elif stage_name == "decompile":
                input_path = file_output_dir / "1_extracted"
            elif stage_name == "parse":
                input_path = file_output_dir / "2_decompiled"
            elif stage_name == "model":
                input_path = file_output_dir / "3_parsed"
            elif stage_name == "generate":
                input_path = file_output_dir / "4_models"

            # Run the stage
            success = self.run_stage(stage_name, input_path, stage_output)
            stage_results[stage_name] = success

            if not success:
                logger.error(f"    ✗ {stage_name} failed for {pbd_file.name}")
                all_success = False
                # Continue to next file if a stage fails
                break
            else:
                logger.info(f"    ✓ {stage_name} completed")

        # Update stage statistics
        for stage, success in stage_results.items():
            if stage not in self.results["stats"]["stage_success_rates"]:
                self.results["stats"]["stage_success_rates"][stage] = {
                    "success": 0,
                    "total": 0,
                }
            self.results["stats"]["stage_success_rates"][stage]["total"] += 1
            if success:
                self.results["stats"]["stage_success_rates"][stage]["success"] += 1

        return all_success

    def run_stage(self, stage: str, input_path: Path, output_path: Path) -> bool:
        """Run a single pipeline stage.

        Args:
            stage: Stage name
            input_path: Input path for stage
            output_path: Output path for stage

        Returns:
            True if stage succeeded, False otherwise
        """
        try:
            # Build command
            cmd = [
                "uv",
                "run",
                "python",
                "main.py",
                stage,
                str(input_path),
                str(output_path),
            ]

            # Add stage-specific options
            if stage == "extract":
                cmd.extend(["--streaming", "--validate"])
            elif stage == "decompile":
                cmd.extend(["--streaming"])
            elif stage == "generate":
                cmd.extend(["--target", "flutter"])

            # Run command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout per stage
            )

            if result.returncode != 0:
                logger.debug(f"Stage {stage} error: {result.stderr}")
                return False

            # Check if output was created
            if stage == "extract":
                # Check for .fun files
                fun_files = list(output_path.glob("*.fun"))
                return len(fun_files) > 0
            elif stage == "decompile":
                # Check for .sru files
                sru_files = list(output_path.glob("*.sru"))
                return len(sru_files) > 0
            elif stage == "parse":
                # Check for .json files
                json_files = list(output_path.glob("*.json"))
                return len(json_files) > 0
            else:
                # For model and generate, just check if directory has content
                return any(output_path.iterdir())

        except subprocess.TimeoutExpired:
            logger.error(f"Stage {stage} timed out after 5 minutes")
            return False
        except Exception as e:
            logger.error(f"Stage {stage} failed with error: {e}")
            return False

    def save_report(self):
        """Save processing report to JSON file."""
        report_path = self.output_dir / "processing_report.json"

        # Calculate stage success rates
        for stage, stats in self.results["stats"]["stage_success_rates"].items():
            if stats["total"] > 0:
                rate = (stats["success"] / stats["total"]) * 100
                stats["success_rate"] = f"{rate:.1f}%"

        # Add timestamp
        self.results["timestamp"] = datetime.now().isoformat()

        # Add summary
        self.results["summary"] = {
            "total_files": self.results["stats"]["total_files"],
            "successful": self.results["stats"]["successful"],
            "failed": self.results["stats"]["failed"],
            "success_rate": self.results["stats"].get("overall_success_rate", "0%"),
            "processing_time": f"{self.results['stats']['processing_time_seconds']:.1f} seconds",
            "total_size": f"{self.results['stats']['total_size_bytes'] / 1024 / 1024:.1f} MB",
        }

        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"\nReport saved to: {report_path}")

        # Print summary
        print("\n" + "=" * 60)
        print("PROCESSING SUMMARY")
        print("=" * 60)
        print(f"Total files: {self.results['summary']['total_files']}")
        print(f"Successful: {self.results['summary']['successful']}")
        print(f"Failed: {self.results['summary']['failed']}")
        print(f"Success rate: {self.results['summary']['success_rate']}")
        print(f"Processing time: {self.results['summary']['processing_time']}")
        print(f"Total size processed: {self.results['summary']['total_size']}")

        if self.results["stats"]["stage_success_rates"]:
            print("\nStage Success Rates:")
            for stage, stats in self.results["stats"]["stage_success_rates"].items():
                print(
                    f"  {stage}: {stats.get('success_rate', 'N/A')} "
                    f"({stats['success']}/{stats['total']})"
                )


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Batch process PBD files")
    parser.add_argument(
        "--input-dir", default="data/pbd_files", help="Directory containing PBD files"
    )
    parser.add_argument(
        "--output-dir",
        default="output/pbd_processed",
        help="Output directory for processed files",
    )
    parser.add_argument(
        "--test", action="store_true", help="Test mode: process only 3 smallest files"
    )

    args = parser.parse_args()

    # Create processor
    processor = PBDProcessor(
        input_dir=Path(args.input_dir), output_dir=Path(args.output_dir)
    )

    # Process files
    results = processor.process_all(test_mode=args.test)

    # Return exit code based on results
    if results["stats"]["failed"] == 0:
        sys.exit(0)
    elif results["stats"]["successful"] > 0:
        sys.exit(1)  # Partial success
    else:
        sys.exit(2)  # Complete failure


if __name__ == "__main__":
    main()
