# Configuration Directory

This directory contains application-specific configuration files for the PowerRebuilder project.

## Directory Contents

- **importlinter.ini** - Import rules and architectural constraints
- **performance.yaml** - Performance configuration and limits
- **security.yaml** - Security policies and constraints
- **root_config_files.json** - Documentation of root configuration files (generated)

## Usage

These configuration files are used by various tools and components of the PowerRebuilder project:

1. **Performance Configuration**: Used to tune extraction, parsing, and generation performance
2. **Security Configuration**: Defines security policies for file handling and code generation
3. **Import Linter**: Enforces import rules and dependencies between modules

## Important Note

Tool configuration files (like pyproject.toml, mypy.ini, .pre-commit-config.yaml, etc.)
remain in the project root directory as most tools expect them there by convention.

This config/ directory is specifically for application runtime configuration, not
development tool configuration.

## Adding New Configuration

When adding new configuration files:
1. Use YAML format for complex configurations
2. Use INI format for tool-specific configurations
3. Document any new configuration options in this README
