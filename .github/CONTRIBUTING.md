# Contributing to PowerRebuilder

Thank you for your interest in contributing to PowerRebuilder! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contribution Process](#contribution-process)
- [Commit Messages](#commit-messages)
- [Testing](#testing)
- [Documentation](#documentation)
- [Release Process](#release-process)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/powerrebuilder.git
   cd powerrebuilder
   ```

3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/powerrebuilder.git
   ```

## Development Setup

### Prerequisites

- Python 3.10 or higher (3.13 recommended)
- uv (modern Python package manager)
- Git
- Docker (optional, for containerized development)

### Installation

1. Install uv:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Install dependencies:
   ```bash
   uv sync --all-extras
   ```

3. Install pre-commit hooks:
   ```bash
   uv run pre-commit install
   ```

4. Run tests to verify setup:
   ```bash
   uv run pytest
   ```

### Development with Docker

For a consistent development environment:

```bash
docker-compose up powerrebuilder-dev
```

## Contribution Process

### 1. Create a Branch

Create a feature branch from `develop`:

```bash
git checkout develop
git pull upstream develop
git checkout -b feature/your-feature-name
```

Use branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or fixes
- `perf/` - Performance improvements

### 2. Make Changes

- Write clean, readable code following Python best practices
- Follow the existing code style and conventions
- Add or update tests for your changes
- Update documentation as needed

### 3. Run Quality Checks

Before committing, run:

```bash
# Format code
uv run ruff format src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type check
uv run mypy src/

# Run tests
uv run pytest tests/

# Or run all checks at once
make lint format type-check test
```

### 4. Commit Your Changes

We use [Conventional Commits](https://www.conventionalcommits.org/) for commit messages:

```bash
git add .
git commit -m "feat: add new extraction capability for DataWindow objects"
```

## Commit Messages

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **perf**: Performance improvements
- **test**: Test additions or modifications
- **build**: Build system changes
- **ci**: CI/CD changes
- **chore**: Maintenance tasks
- **revert**: Revert previous commit

### Examples

```bash
# Feature
feat(extract): add support for PowerBuilder 2022 format

# Bug fix
fix(decompile): resolve memory leak in P-code decoder

# Breaking change
feat(api)!: change response format for extraction endpoint

BREAKING CHANGE: The extraction API now returns a different JSON structure
```

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_extract/test_extractor.py

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run only fast tests
uv run pytest -m "not slow"

# Run integration tests
uv run pytest -m integration
```

### Writing Tests

- Place tests in the appropriate directory under `tests/`
- Use descriptive test names
- Include both positive and negative test cases
- Use fixtures for common test data
- Mark slow tests with `@pytest.mark.slow`
- Mark integration tests with `@pytest.mark.integration`

Example test:

```python
import pytest
from src.extract import Extractor

class TestExtractor:
    def test_extract_valid_pbl_file(self, sample_pbl_file):
        """Test extraction of valid PBL file."""
        extractor = Extractor()
        result = extractor.extract(sample_pbl_file)

        assert result.success
        assert len(result.objects) > 0
        assert result.version == "PB2019R3"

    def test_extract_invalid_file_raises_error(self):
        """Test that invalid file raises appropriate error."""
        extractor = Extractor()

        with pytest.raises(InvalidFileError):
            extractor.extract("not_a_pbl_file.txt")
```

## Documentation

### Code Documentation

- Add docstrings to all public functions, classes, and modules
- Use Google-style docstrings:

```python
def extract_objects(file_path: Path, output_dir: Path) -> List[ExtractedObject]:
    """Extract PowerBuilder objects from a PBL/PBD file.

    Args:
        file_path: Path to the PBL/PBD file.
        output_dir: Directory to write extracted objects.

    Returns:
        List of extracted PowerBuilder objects.

    Raises:
        FileNotFoundError: If the input file doesn't exist.
        ExtractionError: If extraction fails.
    """
```

### Project Documentation

- Update relevant documentation in `docs/`
- Use Markdown format
- Include code examples
- Update `README.md` for significant changes

### Building Documentation

```bash
# Serve documentation locally
uv run mkdocs serve

# Build documentation
uv run mkdocs build
```

## Pull Request Process

1. Update your branch with latest changes:
   ```bash
   git fetch upstream
   git rebase upstream/develop
   ```

2. Push your branch:
   ```bash
   git push origin feature/your-feature-name
   ```

3. Create a Pull Request:
   - Use a descriptive title following conventional commits
   - Fill out the PR template completely
   - Link related issues
   - Add appropriate labels

4. Address Review Comments:
   - Respond to all feedback
   - Make requested changes
   - Re-request review when ready

5. Merge:
   - PRs require at least one approval
   - All CI checks must pass
   - Squash and merge is preferred

## Release Process

Releases are automated through GitHub Actions when changes are pushed to `main`:

1. Version is automatically determined from commit messages
2. Changelog is generated
3. GitHub release is created
4. Package is published to PyPI
5. Docker images are built and pushed

For manual releases, maintainers can trigger the release workflow with a specific version.

## Questions?

If you have questions or need help:

1. Check existing issues and discussions
2. Create a new issue with the `question` label
3. Join our community discussions

Thank you for contributing to PowerRebuilder!
