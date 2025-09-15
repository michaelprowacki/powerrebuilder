# Archived Documentation

This directory contains documentation that has been archived due to outdated or incorrect information.

## Why These Were Archived

### PIPELINE_DI_USAGE.md
- **Reason**: References dependency injection system that was completely removed from codebase
- **Replacement**: Direct imports are now used throughout the codebase

### DEVELOPMENT.md
- **Reason**: Extensive references to Makefile (doesn't exist) and outdated commands
- **Replacement**: Use [../CLAUDE.md](../CLAUDE.md) for accurate development commands

### STATUS.md
- **Reason**: Outdated project status information
- **Replacement**: [../PROJECT_STATUS.md](../PROJECT_STATUS.md) contains current status

### DATA_FLOW.md
- **Reason**: Incorrectly claimed Parse and Decompile stages run in parallel (they're sequential)
- **Replacement**: [../PIPELINE_ARCHITECTURE.md](../PIPELINE_ARCHITECTURE.md) has correct flow

### PERFORMANCE.md & PERFORMANCE_OPTIMIZATION.md
- **Reason**: Significant content overlap and some outdated configuration examples
- **Replacement**: [../PERFORMANCE_GUIDE.md](../PERFORMANCE_GUIDE.md) consolidates both with current information

## Key Changes in Current Codebase

1. **No Dependency Injection**: All DI code was removed, direct imports used instead
2. **No Makefile**: Project uses `uv` package manager with `uv run` commands
3. **Sequential Pipeline**: Extract → Decompile → Parse → Model → Generate (in order)
4. **Model Stage**: Uses services pattern, not separate coordinator class

## How to Access Current Documentation

See [../README.md](../README.md) for the current documentation index with verified, accurate information.

---

*Archived: 2025-01-15 - Documentation consolidation*
