#!/usr/bin/env python3
"""Test script to verify ExtractCoordinator dual-mode functionality."""

from src.extract.extract_coordinator import ExtractCoordinator


def test_simple_mode():
    """Test simple constructor mode."""
    print("Testing simple mode...")

    # Simple mode initialization
    coordinator = ExtractCoordinator(
        input_path="test_data/sample.pbl",
        output_dir="test_output/extracted",
        enable_byte_recovery=False,
        extract_resources=True,
        show_progress=True,
    )

    print("Simple mode initialized:")
    print(f"  Input path: {coordinator.input_path}")
    print(f"  Output dir: {coordinator.output_dir}")
    print(f"  Enable recovery: {coordinator.enable_byte_recovery}")
    print(f"  Extract resources: {coordinator.extract_resources}")
    print(f"  Show progress: {coordinator.show_progress}")
    print(f"  DI services: {coordinator.path_validator is None}")
    print()


def test_di_mode():
    """Test dependency injection mode."""
    print("Testing DI mode...")

    # Mock services
    class MockPathValidator:
        def validate_path(self, path, base_path):
            print(f"Mock: Validating {path}")

        def sanitize_filename(self, filename):
            return filename.replace(" ", "_")

    class MockResourceMonitor:
        def start_monitoring(self):
            print("Mock: Started monitoring")

        def stop_monitoring(self):
            print("Mock: Stopped monitoring")

        def check_file_size(self, size, path):
            print(f"Mock: Checking file size {size} for {path}")

        def check_memory_usage(self):
            pass

    class MockProgressTracker:
        def set_total(self, total):
            print(f"Mock: Progress total set to {total}")

        def update(self, n=1):
            print(f"Mock: Progress updated by {n}")

    # DI mode initialization
    coordinator = ExtractCoordinator(
        path_validator=MockPathValidator(),
        resource_monitor=MockResourceMonitor(),
        progress_tracker=MockProgressTracker(),
    )

    print("DI mode initialized:")
    print(f"  Path validator: {coordinator.path_validator is not None}")
    print(f"  Resource monitor: {coordinator.resource_monitor is not None}")
    print(f"  Progress tracker: {coordinator.progress_tracker is not None}")
    print()


def test_method_compatibility():
    """Test that both modes support the same methods."""
    print("Testing method compatibility...")

    # Simple mode
    simple_coord = ExtractCoordinator("input", "output")

    # Check methods exist
    methods = ["extract", "extract_single_file", "get_statistics", "reset_statistics"]

    for method in methods:
        has_method = hasattr(simple_coord, method)
        print(f"  Has {method}: {has_method}")

    # Test statistics
    stats = simple_coord.get_statistics()
    print(f"  Initial stats: {stats}")
    print()


if __name__ == "__main__":
    print("ExtractCoordinator Dual-Mode Test")
    print("=" * 40)

    test_simple_mode()
    test_di_mode()
    test_method_compatibility()

    print("All tests completed!")
