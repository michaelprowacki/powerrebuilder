# PowerRebuilder Integration Tests

This directory contains comprehensive integration tests for the PowerRebuilder pipeline.

## Overview

The PowerRebuilder pipeline consists of five sequential stages:

1. **Extract**: PBD/PBL → .fun files (P-code)
2. **Decompile**: .fun → .sru files (PowerBuilder source)
3. **Parse**: .sru → AST JSON
4. **Model**: AST → semantic models
5. **Generate**: models → Python/Dart code

## Test Structure

### Core Test Files

- `test_full_pipeline.py` - Main integration test suite
  - `TestFullPipeline` - End-to-end pipeline tests
  - `TestIndividualStages` - Tests for each stage in isolation
  - `TestErrorHandling` - Error recovery and validation
  - `TestDataFlowValidation` - Data transformation verification
  - `TestPerformanceAndScalability` - Performance tests

- `fixtures.py` - Test data generators and helpers
  - `PowerBuilderTestData` - Factory for creating test artifacts
  - `TestDataGenerator` - Complex test scenario generators
  - `PipelineScenarios` - Pre-defined test scenarios

- `test_pipeline_runner.py` - Interactive test runner for debugging

## Running Tests

### Run All Integration Tests

```bash
pytest tests/integration/
```

### Run Specific Test Classes

```bash
# Full pipeline tests only
pytest tests/integration/test_full_pipeline.py::TestFullPipeline

# Individual stage tests
pytest tests/integration/test_full_pipeline.py::TestIndividualStages

# Error handling tests
pytest tests/integration/test_full_pipeline.py::TestErrorHandling
```

### Run Tests by Marker

```bash
# Run only fast tests
pytest tests/integration/ -m "not slow"

# Run only pipeline tests
pytest tests/integration/ -m pipeline

# Run only error handling tests
pytest tests/integration/ -m error
```

### Run with Coverage

```bash
pytest tests/integration/ --cov=src --cov-report=html
```

## Interactive Test Runner

The interactive test runner allows you to debug specific pipeline stages:

### Basic Usage

```bash
# Run full pipeline with simple scenario
python tests/integration/test_pipeline_runner.py run --scenario simple

# Run specific stage
python tests/integration/test_pipeline_runner.py stage --stage parse --scenario simple

# Inspect output from a stage
python tests/integration/test_pipeline_runner.py inspect --stage parse

# Interactive mode
python tests/integration/test_pipeline_runner.py interactive
```

### Available Scenarios

- `simple` - Basic application with window and business logic
- `inheritance` - Tests inheritance and polymorphism
- `crud` - Simple CRUD application
- `transaction` - Transaction processing with rollback
- `events` - Complex event-driven UI

### Interactive Mode Commands

In interactive mode, you can run commands like:

```
> scenario simple      # Load simple scenario
> run                  # Run full pipeline
> stage decompile      # Run specific stage
> inspect parse        # View parse output
> inspect parse test_object.ast.json  # View specific file
> quit                 # Exit
```

## Test Scenarios

### Simple Application (`simple`)

Creates a basic PowerBuilder application with:
- Application object
- Main window with button and text field
- Business logic object with methods
- DataWindow for employee list

### Inheritance Test (`inheritance`)

Tests object-oriented features:
- Base class with virtual methods
- Derived class with overrides
- Protected member access

### CRUD Application (`crud`)

Tests data manipulation:
- DataWindow with SQL
- Window with data controls
- Service object for database operations

### Transaction Processing (`transaction`)

Tests transaction handling:
- Transaction manager object
- Commit/rollback logic
- Error handling

### Event-Driven UI (`events`)

Tests complex UI interactions:
- Custom events
- Event propagation
- Inter-control communication

## Writing New Tests

### Adding a Test Case

```python
def test_new_feature(self, temp_workspace):
    """Test description."""
    # Setup test data
    PipelineTestFixtures.create_mock_sru_file(
        temp_workspace / "source" / "test.sru"
    )

    # Run pipeline stage
    parse_files(
        str(temp_workspace / "source"),
        str(temp_workspace / "output")
    )

    # Verify results
    assert (temp_workspace / "output" / "test.ast.json").exists()
```

### Adding a Test Scenario

```python
@staticmethod
def my_scenario() -> Dict[str, Any]:
    """My test scenario."""
    return {
        "name": "My Scenario",
        "description": "Description",
        "objects": [
            {
                "type": "Window",
                "name": "w_test",
                "controls": [...]
            }
        ]
    }
```

## Debugging Failed Tests

### Enable Verbose Output

```bash
pytest tests/integration/ -v -s
```

### Keep Test Workspace

By default, tests use temporary directories. To keep the workspace:

```bash
python tests/integration/test_pipeline_runner.py run --workspace ./test_output
```

### Inspect Intermediate Files

After a test failure, use the test runner to inspect outputs:

```bash
python tests/integration/test_pipeline_runner.py inspect --stage decompile --workspace ./test_output
```

## Performance Testing

### Run Performance Benchmarks

```bash
pytest tests/integration/test_full_pipeline.py::test_pipeline_benchmark -v
```

### Profile Pipeline Execution

```python
# In test code
def test_profile_pipeline(self, temp_workspace):
    import cProfile
    import pstats

    profiler = cProfile.Profile()
    profiler.enable()

    # Run pipeline
    self.test_full_pipeline_happy_path(temp_workspace)

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)
```

## Continuous Integration

The integration tests are designed to work in CI environments:

```yaml
# Example GitHub Actions workflow
- name: Run Integration Tests
  run: |
    pytest tests/integration/ \
      --junitxml=test-results/integration.xml \
      --cov=src \
      --cov-report=xml
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure PYTHONPATH includes the project root
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **File Not Found**: Check that test fixtures are creating files in the correct locations

3. **Stage Dependencies**: Remember that stages must run in order:
   Extract → Decompile → Parse → Model → Generate

4. **Memory Issues**: For large file tests, increase pytest memory limit:
   ```bash
   pytest tests/integration/ --max-memory=2GB
   ```

### Getting Help

- Check test output for detailed error messages
- Use the interactive runner to debug specific stages
- Enable verbose logging with `-v` flag
- Check intermediate files in the workspace
