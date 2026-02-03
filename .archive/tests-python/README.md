# PowerRebuilder Test Suite

Comprehensive test suite for the PowerRebuilder pipeline, designed to match the clean hexagonal architecture of `src_new`.

## 📋 Overview

This test suite provides extensive testing coverage for the PowerRebuilder pipeline using real PowerBuilder files and modern testing practices:

- **Unit Tests**: Isolated component testing
- **Integration Tests**: Pipeline stage interactions
- **E2E Tests**: Complete workflow validation
- **Performance Tests**: Speed and resource benchmarks
- **Property Tests**: Invariant verification with Hypothesis

## 🚀 Quick Start

### Installation

```bash
# Install test dependencies
pip install -r tests_new/requirements-test.txt

# Or using uv
uv pip install -r tests_new/requirements-test.txt
```

### Running Tests

```bash
# Run all tests
pytest tests_new/

# Run specific test categories
pytest tests_new/unit/           # Unit tests only
pytest tests_new/integration/    # Integration tests
pytest tests_new/e2e/            # End-to-end tests
pytest tests_new/performance/    # Performance benchmarks
pytest tests_new/property/       # Property-based tests

# Run with coverage
pytest tests_new/ --cov=src_new --cov-report=html

# Run tests for specific PowerBuilder version
pytest tests_new/ -k "pb6"       # PB 6.0 tests
pytest tests_new/ -k "pb8"       # PB 8.0 tests
pytest tests_new/ -k "pb12"      # PB 12.0 tests

# Run performance benchmarks
pytest tests_new/performance/ --benchmark-only

# Run tests in parallel
pytest tests_new/ -n auto
```

## 📂 Test Structure

```
tests_new/
├── fixtures/              # Test data
│   ├── pbd_files/        # Real PBD files (small/medium/large)
│   ├── pb_code/          # PowerBuilder code samples by version
│   └── test_data.py      # Test data generators
│
├── unit/                 # Unit tests
│   ├── core/            # Core models and enums
│   ├── extract/         # Extraction components
│   ├── decompile/       # Decompilation logic
│   ├── parse/           # Parser and grammar
│   ├── model/           # Semantic models
│   └── generate/        # Code generators
│
├── integration/          # Integration tests
│   ├── pipeline/        # Pipeline stage integration
│   ├── real_files/      # Tests with real PBD/PBL files
│   └── cross_stage/     # Cross-stage validation
│
├── e2e/                  # End-to-end tests
│   ├── scenarios/       # Real-world scenarios
│   ├── workflows/       # Complete workflows
│   └── validation/      # Output validation
│
├── performance/          # Performance tests
│   ├── benchmarks/      # Speed benchmarks
│   ├── load/           # Load testing
│   └── profiling/      # CPU/memory profiling
│
├── property/            # Property-based tests
│   └── test_pcode_properties.py
│
└── utils/               # Test utilities
    └── helpers.py       # Helper functions
```

## 🧪 Test Categories

### Unit Tests (60% coverage)
- Test individual functions and classes in isolation
- Mock external dependencies
- Fast execution (<1ms per test)
- Located in `tests_new/unit/`

Example:
```python
def test_pbd_parser():
    parser = PBDParser()
    result = parser.parse(sample_pbd_file)
    assert result.success is True
```

### Integration Tests (25% coverage)
- Test interactions between modules
- Use real PBD/PBL files
- Validate data flow between stages
- Located in `tests_new/integration/`

Example:
```python
def test_extract_to_decompile_flow():
    # Extract PBD
    extract_result = extract_coordinator.process()
    # Decompile extracted files
    decompile_result = decompile_coordinator.process()
    assert decompile_result.files_processed > 0
```

### E2E Tests (10% coverage)
- Complete pipeline execution
- Real application conversion
- Output validation
- Located in `tests_new/e2e/`

Example:
```python
def test_accounting_app_conversion():
    # Convert complete accounting application
    # Validate Flutter and Python outputs
```

### Performance Tests (3% coverage)
- Benchmark extraction, parsing, generation speed
- Memory usage profiling
- Scalability testing
- Located in `tests_new/performance/`

### Property Tests (2% coverage)
- Invariant verification
- Fuzz testing
- Using Hypothesis framework
- Located in `tests_new/property/`

## 📊 Test Data

### Real PowerBuilder Files

The test suite uses real PBD/PBL files organized by size:

- **Small (<100KB)**: Unit tests, quick validation
  - `dcm_email.pbd`, `dcm_serialnum.pbd`
- **Medium (100-500KB)**: Integration tests
  - `dcm_login.pbd`, `dcm_referral.pbd`
- **Large (>500KB)**: Performance tests
  - `dcm_detailobjects.pbd`, `dcm_wizard.pbd`

### PowerBuilder Versions

Tests cover multiple PB versions:
- PowerBuilder 6.0
- PowerBuilder 8.0
- PowerBuilder 12.0
- PowerBuilder 2022

## 🎯 Key Test Files

### 1. `conftest.py` - Global Configuration
- Pytest fixtures for common test data
- PBD/PBL file loaders
- Mock factories
- Performance profilers

### 2. `test_models.py` - Core Model Tests
- PowerBuilder object model validation
- Method, Property, Event testing
- Serialization/deserialization

### 3. `test_pbd_parser.py` - Binary Parsing
- PBD/PBL format validation
- Binary reader functionality
- Header and entry parsing

### 4. `test_full_pipeline.py` - Pipeline Integration
- Complete pipeline flow
- Multi-stage validation
- Error handling

### 5. `test_accounting_app.py` - E2E Scenario
- Real application conversion
- Semantic validation
- Accuracy metrics

### 6. `test_extraction_speed.py` - Performance
- Extraction benchmarks
- Memory usage tracking
- Scalability testing

### 7. `test_pcode_properties.py` - Property Testing
- Opcode invariants
- Stack operation properties
- Fuzz testing

## 📈 Metrics and Reporting

### Accuracy Metrics
- Extraction rate
- Decompilation success
- Parse accuracy
- Semantic preservation
- Code generation completeness

### Performance Metrics
- Throughput (MB/s)
- Memory usage (peak/average)
- Execution time per stage
- Scalability factor

### Test Reports
- HTML coverage reports
- JSON metrics output
- Performance profiles
- Accuracy dashboards

## 🔧 Configuration

### pytest.ini Settings
```ini
[pytest]
testpaths = .
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
    slow: Tests >5 seconds
    pb6: PowerBuilder 6.0 tests
```

### Custom Command Line Options
```bash
# Run with profiling
pytest tests_new/ --profile

# Run with real files (slow)
pytest tests_new/ --real-files

# Specific PB version
pytest tests_new/ --pb-version=6
```

## 🏃 CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run Unit Tests
  run: pytest tests_new/unit/ --cov=src_new

- name: Run Integration Tests
  run: pytest tests_new/integration/

- name: Run E2E Tests (Nightly)
  run: pytest tests_new/e2e/ --slow
```

## 📊 Success Criteria

- **Code Coverage**: >80% for src_new
- **Test Execution**:
  - Unit tests: <30s total
  - Integration: <2min total
  - E2E: <10min total
- **Accuracy**: >90% semantic correctness
- **Performance**: >0.5 MB/s throughput

## 🔍 Debugging Failed Tests

### Verbose Output
```bash
pytest tests_new/ -vv --tb=long
```

### Run Single Test
```bash
pytest tests_new/unit/core/test_models.py::TestPBObject::test_create_window_object
```

### Debug with pdb
```bash
pytest tests_new/ --pdb
```

## 🤝 Contributing

1. Add tests for new features
2. Ensure all tests pass before PR
3. Maintain >80% code coverage
4. Follow existing test patterns
5. Update fixtures as needed

## 📝 Test Writing Guidelines

### Unit Test Pattern
```python
class TestComponent:
    def test_happy_path(self):
        # Arrange
        component = Component()

        # Act
        result = component.process(input)

        # Assert
        assert result.success is True
```

### Integration Test Pattern
```python
def test_stage_integration(real_pbd_file, temp_dir):
    # Run multiple stages
    extract_result = extract(real_pbd_file, temp_dir)
    decompile_result = decompile(extract_result.output)

    # Validate flow
    assert decompile_result.success
```

### Property Test Pattern
```python
@given(st.integers(min_value=0, max_value=255))
def test_opcode_property(opcode):
    # Property should hold for all inputs
    result = process_opcode(opcode)
    assert 0 <= result <= 255
```

## 📚 Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [PowerBuilder File Format](../docs/pb_format.md)
