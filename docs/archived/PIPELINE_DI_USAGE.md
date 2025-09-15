# Pipeline Coordinator Dependency Injection Usage

The `PipelineCoordinator` now supports two usage patterns:

## 1. Simple Constructor (Backward Compatible)

This is the original pattern used by the CLI and existing code:

```python
from src.common.pipeline.pipeline_coordinator import PipelineCoordinator

# Simple usage - creates all coordinators internally
coordinator = PipelineCoordinator(
    input_dir="/path/to/pbl/files",
    output_dir="/path/to/output",
    temp_dir="/path/to/temp",  # Optional
    config={
        'extract': {
            'enable_byte_recovery': True,
            'extract_resources': True
        },
        'decompile': {
            'debug_mode': False
        },
        'generate': {
            'target_framework': 'flutter',
            'null_safety': True
        }
    }
)

# Run the pipeline
results = coordinator.process_files(['file1.pbl', 'file2.pbl'])
```

## 2. Dependency Injection Pattern

This pattern allows you to provide your own coordinator instances, which is useful for:
- Unit testing with mocks
- Custom implementations
- Fine-grained control over each stage

```python
from src.common.pipeline.pipeline_coordinator import PipelineCoordinator
from src.extract.core_coordinator import ExtractCoordinator
from src.decompile.decompile_coordinator import DecompileCoordinator
from src.parse.parse_coordinator import ParseCoordinator
from src.model.coordinator import ModelCoordinator
from src.generate.generate_coordinator import GenerateCoordinator
from src.core.recovery import FileErrorCollector, PipelineCheckpoint

# Create individual coordinators with custom configurations
extract_coordinator = ExtractCoordinator(
    input_path="/path/to/input",
    output_dir="/path/to/extracted",
    enable_byte_recovery=True,
    extract_resources=True,
    show_progress=True
)

decompile_coordinator = DecompileCoordinator(
    input_dir="/path/to/extracted",
    output_dir="/path/to/decompiled",
    enable_byte_recovery=False,
    output_format="pb",
    enable_filtering=True
)

parse_coordinator = ParseCoordinator(
    input_dir="/path/to/decompiled",
    output_dir="/path/to/parsed",
    library_paths=["/path/to/libraries"]
)

model_coordinator = ModelCoordinator(
    input_dir="/path/to/parsed",
    output_dir="/path/to/models"
)

generate_coordinator = GenerateCoordinator(
    input_dir="/path/to/models",
    output_dir="/path/to/output",
    framework='flutter',
    null_safety=True,
    generate_tests=False
)

# Optional: Custom error handling
error_collector = FileErrorCollector()
checkpoint = PipelineCheckpoint("/path/to/checkpoint")

# Create pipeline with DI
coordinator = PipelineCoordinator(
    extract_coordinator=extract_coordinator,
    decompile_coordinator=decompile_coordinator,
    parse_coordinator=parse_coordinator,
    model_coordinator=model_coordinator,
    generate_coordinator=generate_coordinator,
    error_collector=error_collector,
    checkpoint=checkpoint
)

# Run the pipeline
results = coordinator.process_files(['file1.pbl', 'file2.pbl'])
```

## Benefits of DI Pattern

1. **Testability**: Easy to mock individual coordinators for unit tests
2. **Flexibility**: Can use custom implementations of coordinators
3. **Reusability**: Can share coordinator instances across multiple pipelines
4. **Configuration**: Each coordinator can be configured independently

## Example: Testing with Mocks

```python
from unittest.mock import Mock

# Create mock coordinators
mock_extract = Mock()
mock_extract.extract_single_file.return_value = True

mock_decompile = Mock()
mock_decompile.decompile_extracted_file.return_value = True

# ... create other mocks ...

# Create pipeline with mocks
coordinator = PipelineCoordinator(
    extract_coordinator=mock_extract,
    decompile_coordinator=mock_decompile,
    # ... other mocks ...
)

# Test pipeline behavior
results = coordinator.process_files(['test.pbl'])

# Verify mocks were called correctly
assert mock_extract.extract_single_file.called
assert mock_decompile.decompile_extracted_file.called
```

## Partial DI

You can provide only some coordinators and let the pipeline create defaults for the rest:

```python
# Only provide a custom extract coordinator
custom_extract = ExtractCoordinator(
    input_path="/custom/path",
    output_dir="/custom/output",
    enable_byte_recovery=True
)

coordinator = PipelineCoordinator(
    extract_coordinator=custom_extract
    # Other coordinators will be created with defaults
)
```

## Migration Guide

Existing code using the simple constructor will continue to work without changes. The DI pattern is purely additive and opt-in.

To migrate to DI:
1. Create individual coordinator instances
2. Pass them to PipelineCoordinator constructor
3. Remove the simple constructor parameters (input_dir, output_dir, etc.)
