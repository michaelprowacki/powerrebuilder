#!/usr/bin/env python3
"""PowerRebuilder CLI - Clean command-line interface.

This is the main entry point for the PowerRebuilder pipeline.
Provides a simple, unified interface for all operations.
"""

import logging
import sys
from pathlib import Path

import click

from src_new._core import TargetLanguage
from src_new._patterns import Pipeline
from src_new.decompile import DecompileCoordinator
from src_new.extract import ExtractCoordinator
from src_new.generate import GenerateCoordinator
from src_new.model import ModelCoordinator
from src_new.parse import ParseCoordinator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="2.0.0", prog_name="PowerRebuilder")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress output except errors")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, quiet: bool):
    """PowerRebuilder - Transform PowerBuilder applications to modern code.

    This tool provides a 5-stage pipeline for converting PowerBuilder
    applications to modern languages and frameworks.
    """
    ctx.ensure_object(dict)

    # Configure logging level
    if quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet


@cli.command()
@click.argument(
    "input_path",
    type=click.Path(exists=True),
)
@click.argument(
    "output_path",
    type=click.Path(),
)
@click.option(
    "--target",
    "-t",
    type=click.Choice(["flutter", "python", "typescript", "react", "dioxus"]),
    default="flutter",
    help="Target language/framework",
)
@click.option("--parallel", "-p", is_flag=True, help="Enable parallel processing")
@click.option("--cache", is_flag=True, help="Enable caching")
def all(
    input_path: str,
    output_path: str,
    target: str,
    parallel: bool,
    cache: bool,
):
    """Run the complete pipeline (all 5 stages).

    INPUT_PATH: PBL/PBD file or directory
    OUTPUT_PATH: Output directory for generated code
    """
    logger.info("Starting complete pipeline")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Target: {target}")

    # Create output directory
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create intermediate directories
    extracted_dir = output_dir / "1_extracted"
    decompiled_dir = output_dir / "2_decompiled"
    parsed_dir = output_dir / "3_parsed"
    model_dir = output_dir / "4_model"
    generated_dir = output_dir / "5_generated"

    for dir_path in [
        extracted_dir,
        decompiled_dir,
        parsed_dir,
        model_dir,
        generated_dir,
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Create pipeline stages
    stages = [
        ExtractCoordinator(
            input_path=Path(input_path),
            output_path=extracted_dir,
            config={"parallel": parallel, "cache_enabled": cache},
        ),
        DecompileCoordinator(
            input_path=extracted_dir,
            output_path=decompiled_dir,
            config={"parallel": parallel},
        ),
        ParseCoordinator(
            input_path=decompiled_dir,
            output_path=parsed_dir,
            config={"parallel": parallel},
        ),
        ModelCoordinator(input_path=parsed_dir, output_path=model_dir, config={}),
        GenerateCoordinator(
            input_path=model_dir,
            output_path=generated_dir,
            target=TargetLanguage(target),
            config={},
        ),
    ]

    # Execute pipeline
    pipeline = Pipeline(stages, stop_on_error=True)
    result = pipeline.execute()

    # Check result
    if result.success:
        logger.info("✓ Pipeline completed successfully!")
        logger.info(f"Generated code in: {generated_dir}")
        sys.exit(0)
    else:
        logger.error("✗ Pipeline failed")
        for error in result.errors[:5]:
            logger.error(f"  - {error}")
        sys.exit(1)


@cli.command()
@click.argument(
    "input_path",
    type=click.Path(exists=True),
)
@click.argument(
    "output_path",
    type=click.Path(),
)
@click.option("--recovery", is_flag=True, help="Enable corruption recovery")
def extract(input_path: str, output_path: str, recovery: bool):
    """Extract objects from PBL/PBD files.

    INPUT_PATH: PBL/PBD file or directory
    OUTPUT_PATH: Output directory for extracted files
    """
    logger.info("Running extraction stage")

    coordinator = ExtractCoordinator(
        input_path=Path(input_path),
        output_path=Path(output_path),
        config={"recovery_enabled": recovery},
    )

    result = coordinator.process()

    if result.success:
        logger.info(f"✓ Extracted {result.files_processed} files")
    else:
        logger.error(f"✗ Extraction failed: {result.errors}")
        sys.exit(1)


@cli.command()
@click.argument(
    "input_path",
    type=click.Path(exists=True),
)
@click.argument(
    "output_path",
    type=click.Path(),
)
def decompile(input_path: str, output_path: str):
    """Decompile P-code to PowerBuilder source.

    INPUT_PATH: Directory with .fun files
    OUTPUT_PATH: Output directory for source files
    """
    logger.info("Running decompilation stage")

    coordinator = DecompileCoordinator(
        input_path=Path(input_path),
        output_path=Path(output_path),
    )

    result = coordinator.process()

    if result.success:
        logger.info(f"✓ Decompiled {result.files_processed} files")
    else:
        logger.error(f"✗ Decompilation failed: {result.errors}")
        sys.exit(1)


@cli.command()
@click.argument(
    "input_path",
    type=click.Path(exists=True),
)
@click.argument(
    "output_path",
    type=click.Path(),
)
def parse(input_path: str, output_path: str):
    """Parse PowerBuilder source to AST.

    INPUT_PATH: Directory with source files
    OUTPUT_PATH: Output directory for AST JSON files
    """
    logger.info("Running parsing stage")

    coordinator = ParseCoordinator(
        input_path=Path(input_path),
        output_path=Path(output_path),
    )

    result = coordinator.process()

    if result.success:
        logger.info(f"✓ Parsed {result.files_processed} files")
    else:
        logger.error(f"✗ Parsing failed: {result.errors}")
        sys.exit(1)


@cli.command()
@click.argument(
    "input_path",
    type=click.Path(exists=True),
)
@click.argument(
    "output_path",
    type=click.Path(),
)
def model(input_path: str, output_path: str):
    """Build semantic models from AST.

    INPUT_PATH: Directory with AST JSON files
    OUTPUT_PATH: Output directory for model files
    """
    logger.info("Running model building stage")

    coordinator = ModelCoordinator(
        input_path=Path(input_path),
        output_path=Path(output_path),
    )

    result = coordinator.process()

    if result.success:
        logger.info(f"✓ Built models for {result.files_processed} objects")
    else:
        logger.error(f"✗ Model building failed: {result.errors}")
        sys.exit(1)


@cli.command()
@click.argument(
    "input_path",
    type=click.Path(exists=True),
)
@click.argument(
    "output_path",
    type=click.Path(),
)
@click.option(
    "--target",
    "-t",
    type=click.Choice(["flutter", "python", "typescript", "react", "dioxus"]),
    default="flutter",
    help="Target language/framework",
)
def generate(input_path: str, output_path: str, target: str):
    """Generate modern code from models.

    INPUT_PATH: Directory with model files
    OUTPUT_PATH: Output directory for generated code
    """
    logger.info(f"Generating {target} code")

    coordinator = GenerateCoordinator(
        input_path=Path(input_path),
        output_path=Path(output_path),
        target=TargetLanguage(target),
    )

    result = coordinator.process()

    if result.success:
        logger.info(f"✓ Generated {result.files_processed} files")
        logger.info(f"Code is in: {output_path}")
    else:
        logger.error(f"✗ Generation failed: {result.errors}")
        sys.exit(1)


@cli.command()
@click.argument(
    "file_path",
    type=click.Path(exists=True),
)
def analyze(file_path: str):
    """Analyze a PowerBuilder file.

    FILE_PATH: PBL/PBD or source file to analyze
    """
    file_path = Path(file_path)
    logger.info(f"Analyzing: {file_path}")

    # Determine file type
    if file_path.suffix.lower() in [".pbl", ".pbd"]:
        logger.info("File type: PowerBuilder Library")

        from src_new.extract import PBLParser

        parser = PBLParser(file_path)

        try:
            pbl_file = parser.parse()
            logger.info(f"Version: {pbl_file.version}")
            logger.info(f"Entries: {len(pbl_file.entries)}")
            logger.info(f"Size: {pbl_file.size} bytes")

            for entry in pbl_file.entries[:10]:
                logger.info(f"  - {entry.name} ({entry.type.value})")

            if len(pbl_file.entries) > 10:
                logger.info(f"  ... and {len(pbl_file.entries) - 10} more")

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            sys.exit(1)

    elif file_path.suffix.lower() == ".fun":
        logger.info("File type: P-code function")

        from src_new._patterns import BinaryReader

        with BinaryReader(file_path) as reader:
            logger.info(f"Size: {reader.size} bytes")
            logger.info(f"First 16 bytes: {reader.peek(16).hex()}")

    elif file_path.suffix.lower() in [".sru", ".srw", ".srm", ".srd"]:
        logger.info("File type: PowerBuilder source")

        from src_new._patterns import FileHandler

        file_handler = FileHandler()
        content = file_handler.read_text(file_path)

        logger.info(f"Lines: {len(content.splitlines())}")
        logger.info(f"Size: {len(content)} characters")

        # Detect object type
        if "window type" in content.lower():
            logger.info("Object type: Window")
        elif "datawindow" in content.lower():
            logger.info("Object type: DataWindow")
        elif "menu type" in content.lower():
            logger.info("Object type: Menu")
        else:
            logger.info("Object type: User Object")

    else:
        logger.warning(f"Unknown file type: {file_path.suffix}")


@cli.command()
@click.argument(
    "input_path",
    type=click.Path(exists=True),
)
@click.option("--iterations", "-i", default=3, help="Number of benchmark iterations")
@click.option(
    "--stage",
    type=click.Choice(["extract", "decompile", "parse", "model", "generate", "all"]),
    default="all",
    help="Stage to benchmark",
)
def benchmark(input_path: str, iterations: int, stage: str):
    """Benchmark pipeline performance.

    INPUT_PATH: Input file or directory to benchmark
    """
    import time
    from statistics import mean, stdev

    logger.info(f"Benchmarking {stage} stage with {iterations} iterations")

    times = []
    for i in range(iterations):
        start = time.time()

        # Run the specified stage
        # This is a simplified example - would need actual implementation
        logger.info(f"Iteration {i + 1}/{iterations}...")

        elapsed = time.time() - start
        times.append(elapsed)

    if times:
        logger.info(f"Average: {mean(times):.2f}s")
        if len(times) > 1:
            logger.info(f"Std Dev: {stdev(times):.2f}s")
        logger.info(f"Min: {min(times):.2f}s, Max: {max(times):.2f}s")


@cli.command()
@click.argument(
    "input_path",
    type=click.Path(exists=True),
)
@click.option("--check-corruption", is_flag=True, help="Check for file corruption")
@click.option("--check-structure", is_flag=True, help="Validate file structure")
def validate(input_path: str, check_corruption: bool, check_structure: bool):
    """Validate input files before processing.

    INPUT_PATH: File or directory to validate
    """
    from pathlib import Path
    from src_new.utils.binary import BinaryAnalyzer

    path = Path(input_path)
    logger.info(f"Validating: {path}")

    if path.is_file():
        files = [path]
    else:
        files = list(path.rglob("*.pbl")) + list(path.rglob("*.pbd"))

    analyzer = BinaryAnalyzer()
    issues = []

    for file in files:
        try:
            analysis = analyzer.analyze(file)

            if check_corruption and analysis.corruption:
                issues.append(f"{file}: {', '.join(analysis.corruption)}")

            if check_structure:
                if analysis.format == "Unknown":
                    issues.append(f"{file}: Unknown format")

            logger.info(f"✓ {file.name}: {analysis.format.value}")

        except Exception as e:
            issues.append(f"{file}: {str(e)}")

    if issues:
        logger.error(f"Found {len(issues)} issues:")
        for issue in issues:
            logger.error(f"  - {issue}")
        sys.exit(1)
    else:
        logger.info(f"✓ All {len(files)} files validated successfully")


@cli.command()
@click.option("--cache", is_flag=True, help="Clear cache files")
@click.option("--temp", is_flag=True, help="Clear temporary files")
@click.option("--output", is_flag=True, help="Clear output directories")
@click.option("--all", is_flag=True, help="Clear everything")
@click.confirmation_option(prompt="Are you sure you want to clean?")
def clean(cache: bool, temp: bool, output: bool, all: bool):
    """Clean cache and temporary files."""
    import shutil
    from pathlib import Path

    if all:
        cache = temp = output = True

    if not (cache or temp or output):
        logger.warning("Nothing to clean (specify --cache, --temp, --output, or --all)")
        return

    cleaned = []

    if cache:
        cache_dir = Path(".cache")
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            cleaned.append("cache")

    if temp:
        temp_dirs = [Path("tmp"), Path(".tmp"), Path("temp")]
        for temp_dir in temp_dirs:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                cleaned.append(str(temp_dir))

    if output:
        output_dirs = [Path("output"), Path("dist"), Path("build")]
        for out_dir in output_dirs:
            if out_dir.exists():
                shutil.rmtree(out_dir)
                cleaned.append(str(out_dir))

    if cleaned:
        logger.info(f"✓ Cleaned: {', '.join(cleaned)}")
    else:
        logger.info("Nothing to clean")


@cli.command()
@click.option("--watch", is_flag=True, help="Watch pipeline status in real-time")
def status(watch: bool):
    """Show pipeline execution status."""
    import json
    from pathlib import Path

    status_file = Path(".pipeline_status.json")

    if not status_file.exists():
        logger.info("No pipeline currently running")
        return

    try:
        with open(status_file) as f:
            status_data = json.load(f)

        logger.info("Pipeline Status")
        logger.info("=" * 40)
        logger.info(f"Stage: {status_data.get('stage', 'Unknown')}")
        logger.info(f"Progress: {status_data.get('progress', 0)}%")
        logger.info(f"Files Processed: {status_data.get('files_processed', 0)}")
        logger.info(f"Errors: {status_data.get('errors', 0)}")

        if watch:
            import time

            logger.info("\\nWatching for updates (Ctrl+C to stop)...")
            while True:
                time.sleep(2)
                # Would refresh status here

    except Exception as e:
        logger.error(f"Failed to read status: {e}")


@cli.command()
@click.argument(
    "file_path",
    type=click.Path(exists=True),
)
@click.option("--detailed", is_flag=True, help="Show detailed information")
def inspect(file_path: str, detailed: bool):
    """Inspect PowerBuilder files without extraction.

    FILE_PATH: File to inspect
    """
    from pathlib import Path
    from src_new.extract import PBLParser
    from src_new.utils.binary import BinaryAnalyzer

    path = Path(file_path)
    logger.info(f"Inspecting: {path}")

    analyzer = BinaryAnalyzer()
    analysis = analyzer.analyze(path)

    # Basic info
    logger.info(f"Format: {analysis.format.value}")
    logger.info(f"Size: {analysis.size:,} bytes")
    logger.info(f"Checksum: {analysis.checksum}")
    logger.info(f"Entropy: {analysis.entropy:.2f}")

    if analysis.corruption:
        logger.warning(f"Issues: {', '.join(analysis.corruption)}")

    # Detailed inspection for PBL/PBD
    if analysis.format.value in [
        "PowerBuilder Library",
        "PowerBuilder Dynamic Library",
    ]:
        try:
            parser = PBLParser(path)
            pbl_file = parser.parse()

            logger.info(f"Version: {pbl_file.version}")
            logger.info(f"Entries: {len(pbl_file.entries)}")

            if detailed:
                logger.info("\\nContents:")
                for entry in pbl_file.entries:
                    logger.info(
                        f"  - {entry.name} ({entry.type.value}) - {entry.size} bytes"
                    )

        except Exception as e:
            logger.error(f"Failed to parse: {e}")


@cli.command()
def doctor():
    """Check system configuration and dependencies."""
    logger.info("PowerRebuilder System Check")
    logger.info("=" * 40)

    # Check Python version
    import sys

    py_version = sys.version_info
    if py_version >= (3, 10):
        logger.info(
            f"✓ Python {py_version.major}.{py_version.minor}.{py_version.micro}"
        )
    else:
        logger.error(f"✗ Python {py_version.major}.{py_version.minor} (need 3.10+)")

    # Check required packages
    required_packages = [
        "click",
        "lark",
        "pydantic",
    ]

    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✓ {package} installed")
        except ImportError:
            logger.error(f"✗ {package} not installed")

    # Check directory structure
    src_new = Path("src_new")
    if src_new.exists():
        subdirs = [
            "_patterns",
            "_core",
            "extract",
            "decompile",
            "parse",
            "model",
            "generate",
        ]
        for subdir in subdirs:
            if (src_new / subdir).exists():
                logger.info(f"✓ {subdir}/ exists")
            else:
                logger.error(f"✗ {subdir}/ missing")
    else:
        logger.error("✗ src_new directory not found")

    logger.info("=" * 40)
    logger.info("Check complete")


if __name__ == "__main__":
    cli()
