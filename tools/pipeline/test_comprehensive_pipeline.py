#!/usr/bin/env python3
"""Comprehensive pipeline test for SIME Finch.

This script tests the entire pipeline from input through generation,
with detailed logging and error reporting at each stage.
"""

import json
import logging
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pipeline_test.log", mode="w"),
    ],
)
logger = logging.getLogger(__name__)


class PipelineTestRunner:
    """Runs comprehensive tests on the SIME Finch pipeline."""

    def __init__(self, test_name: str = "pipeline_test") -> None:
        self.test_name = test_name
        self.project_root = Path(__file__).parent.parent.parent
        self.test_output_dir = (
            self.project_root / "output" / f"test_{test_name}_{int(time.time())}"
        )
        self.results = {
            "test_name": test_name,
            "start_time": time.time(),
            "stages": {},
        }

    def setup(self) -> None:
        """Setup test environment."""
        logger.info(f"Setting up test environment in {self.test_output_dir}")
        self.test_output_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (self.test_output_dir / "extracted").mkdir(exist_ok=True)
        (self.test_output_dir / "parsed").mkdir(exist_ok=True)
        (self.test_output_dir / "decompiled").mkdir(exist_ok=True)
        (self.test_output_dir / "generated").mkdir(exist_ok=True)

    def run_command(self, cmd: list[str], stage: str) -> dict[str, Any]:
        """Run a command and capture results."""
        logger.info(f"Running {stage}: {' '.join(cmd)}")
        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                check=False,
            )

            duration = time.time() - start_time
            success = result.returncode == 0

            stage_result = {
                "command": " ".join(cmd),
                "success": success,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }

            if success:
                logger.info(f"✓ {stage} completed successfully in {duration:.2f}s")
            else:
                logger.error(f"✗ {stage} failed with return code {result.returncode}")
                logger.error(f"STDERR: {result.stderr}")

            return stage_result

        except Exception as e:
            logger.exception(f"✗ {stage} failed with exception: {e}")
            return {
                "command": " ".join(cmd),
                "success": False,
                "duration": time.time() - start_time,
                "error": str(e),
            }

    def test_extraction(self, input_files: list[Path]) -> dict[str, Any]:
        """Test extraction stage."""
        logger.info("=" * 60)
        logger.info("STAGE 1: EXTRACTION")
        logger.info("=" * 60)

        extract_results = {
            "files": {},
            "summary": {},
        }

        # Test individual file extraction
        for input_file in input_files[:3]:  # Test first 3 files
            logger.info(f"Testing extraction of {input_file.name}")

            cmd = [
                "uv",
                "run",
                "python",
                "-m",
                "main",
                "extract",
                "files",
                str(input_file),
                str(self.test_output_dir / "extracted" / input_file.stem),
                "--debug",
            ]

            result = self.run_command(cmd, f"extract_{input_file.name}")
            extract_results["files"][input_file.name] = result

        # Test batch extraction with byte recovery
        logger.info("Testing batch extraction with byte recovery...")
        cmd = [
            "uv",
            "run",
            "python",
            "-m",
            "main",
            "extract",
            "files",
            str(self.project_root / "input" / "pbd_files"),
            str(self.test_output_dir / "extracted"),
            "--debug",
            "--enable-byte-recovery",
        ]

        extract_results["summary"] = self.run_command(cmd, "extract_batch")

        # Count extracted files
        extracted_files = list((self.test_output_dir / "extracted").rglob("*"))
        logger.info(f"Total files extracted: {len(extracted_files)}")
        extract_results["extracted_count"] = len(extracted_files)

        return extract_results

    def test_parsing(self) -> dict[str, Any]:
        """Test parsing stage."""
        logger.info("=" * 60)
        logger.info("STAGE 2: PARSING")
        logger.info("=" * 60)

        cmd = [
            "uv",
            "run",
            "python",
            "-m",
            "main",
            "parse",
            str(self.test_output_dir / "extracted"),
            str(self.test_output_dir / "parsed"),
        ]

        result = self.run_command(cmd, "parse")

        # Check parsing summary
        summary_file = self.test_output_dir / "parsed" / "parsed_summary.json"
        if summary_file.exists():
            with open(summary_file) as f:
                summary = json.load(f)
                logger.info(f"Parsing summary: {json.dumps(summary, indent=2)}")
                result["summary"] = summary

        return result

    def test_decompilation(self) -> dict[str, Any]:
        """Test decompilation stage."""
        logger.info("=" * 60)
        logger.info("STAGE 3: DECOMPILATION")
        logger.info("=" * 60)

        cmd = [
            "uv",
            "run",
            "python",
            "-m",
            "main",
            "decompile",
            str(self.test_output_dir / "extracted"),
            str(self.test_output_dir / "decompiled"),
        ]

        result = self.run_command(cmd, "decompile")

        # Count decompiled files
        decompiled_files = list((self.test_output_dir / "decompiled").rglob("*.fun"))
        logger.info(f"Total functions decompiled: {len(decompiled_files)}")
        result["decompiled_count"] = len(decompiled_files)

        return result

    def test_generation(self) -> dict[str, Any]:
        """Test code generation stage."""
        logger.info("=" * 60)
        logger.info("STAGE 4: CODE GENERATION")
        logger.info("=" * 60)

        cmd = [
            "uv",
            "run",
            "python",
            "-m",
            "main",
            "generate",
            "--parsed-dir",
            str(self.test_output_dir / "parsed"),
            "--decompiled-dir",
            str(self.test_output_dir / "decompiled"),
        ]

        result = self.run_command(cmd, "generate")

        # Count generated files
        generated_files = {
            "models": list((self.test_output_dir / "generated").rglob("*.py")),
            "flutter": list((self.test_output_dir / "generated").rglob("*.dart")),
            "services": list(
                (self.test_output_dir / "generated").rglob("*service*.py")
            ),
        }

        for file_type, files in generated_files.items():
            logger.info(f"Generated {len(files)} {file_type} files")

        result["generated_counts"] = {k: len(v) for k, v in generated_files.items()}

        return result

    def test_full_pipeline(self) -> dict[str, Any]:
        """Test the full pipeline with the 'all' command."""
        logger.info("=" * 60)
        logger.info("FULL PIPELINE TEST")
        logger.info("=" * 60)

        # Create a separate output directory for full pipeline test
        full_test_dir = self.test_output_dir / "full_pipeline"
        full_test_dir.mkdir(exist_ok=True)

        cmd = [
            "uv",
            "run",
            "python",
            "-m",
            "main",
            "all",
            "--pbl-input-dir",
            str(self.project_root / "input" / "pbd_files"),
            "--base-output-dir",
            str(full_test_dir),
            "--debug",
            "--enable-byte-recovery",
        ]

        result = self.run_command(cmd, "full_pipeline")

        # Analyze output structure
        output_analysis = {}
        for subdir in ["extracted", "parsed", "decompiled"]:
            path = full_test_dir / subdir
            if path.exists():
                file_count = len(list(path.rglob("*")))
                output_analysis[subdir] = file_count
                logger.info(f"{subdir}: {file_count} files")

        result["output_analysis"] = output_analysis

        return result

    def run_all_tests(self):
        """Run all pipeline tests."""
        self.setup()

        # Get test input files
        input_dir = self.project_root / "input" / "pbd_files"
        input_files = list(input_dir.glob("*.pbd"))[:5]  # Test with first 5 PBD files

        logger.info(f"Testing with {len(input_files)} PBD files from {input_dir}")

        # Run individual stage tests
        self.results["stages"]["extraction"] = self.test_extraction(input_files)
        self.results["stages"]["parsing"] = self.test_parsing()
        self.results["stages"]["decompilation"] = self.test_decompilation()
        self.results["stages"]["generation"] = self.test_generation()

        # Run full pipeline test
        self.results["stages"]["full_pipeline"] = self.test_full_pipeline()

        # Calculate summary
        self.results["end_time"] = time.time()
        self.results["total_duration"] = (
            self.results["end_time"] - self.results["start_time"]
        )

        # Save results
        results_file = self.test_output_dir / "test_results.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2, default=str)

        logger.info("=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total test duration: {self.results['total_duration']:.2f}s")
        logger.info(f"Results saved to: {results_file}")

        # Print stage summaries
        for stage_name, stage_data in self.results["stages"].items():
            if isinstance(stage_data, dict) and "success" in stage_data:
                status = "✓" if stage_data["success"] else "✗"
                logger.info(
                    f"{status} {stage_name}: {'PASSED' if stage_data['success'] else 'FAILED'}"
                )

        return self.results

    def cleanup(self, keep_output: bool = True) -> None:
        """Clean up test artifacts."""
        if not keep_output and self.test_output_dir.exists():
            logger.info(f"Cleaning up test directory: {self.test_output_dir}")
            shutil.rmtree(self.test_output_dir)


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test SIME Finch pipeline")
    parser.add_argument(
        "--name", default="pipeline_test", help="Test name for output directory"
    )
    parser.add_argument(
        "--cleanup", action="store_true", help="Clean up test output after completion"
    )
    parser.add_argument(
        "--quick", action="store_true", help="Run quick test with limited files"
    )

    args = parser.parse_args()

    # Run tests
    runner = PipelineTestRunner(test_name=args.name)

    try:
        results = runner.run_all_tests()

        # Check if all tests passed
        all_passed = all(
            stage.get("success", False)
            for stage in results["stages"].values()
            if isinstance(stage, dict) and "success" in stage
        )

        if all_passed:
            logger.info("✓ All pipeline tests PASSED!")
            exit_code = 0
        else:
            logger.error("✗ Some pipeline tests FAILED!")
            exit_code = 1

    except Exception as e:
        logger.error(f"Test runner failed: {e}", exc_info=True)
        exit_code = 2
    finally:
        if args.cleanup:
            runner.cleanup(keep_output=False)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
