# PowerRebuilder Documentation

## Core Documentation (Accurate & Current)

These documents have been verified against the actual codebase:

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Complete pipeline architecture and design
- **[PIPELINE_ARCHITECTURE.md](PIPELINE_ARCHITECTURE.md)** - Sequential pipeline flow and stage dependencies
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Current project state and known issues
- **[PERFORMANCE_GUIDE.md](PERFORMANCE_GUIDE.md)** - Comprehensive performance optimization guide
- **[../CLAUDE.md](../CLAUDE.md)** - Developer guide with accurate commands
- **[../README.md](../README.md)** - Project overview and quick start

## Specialized Topics (Verified Current)

These documents contain specific technical information:

- **[HIGH_PERFORMANCE_PCODE_DETECTION.md](HIGH_PERFORMANCE_PCODE_DETECTION.md)** - P-code detection implementation details
- **[POWERBUILDER_CONVERSION_GUIDE.md](POWERBUILDER_CONVERSION_GUIDE.md)** - PowerBuilder to modern code mapping
- **[powerbuilder_to_flutter_conversion_rules.md](powerbuilder_to_flutter_conversion_rules.md)** - Detailed Flutter conversion rules
- **[SECURITY.md](SECURITY.md)** - Security features and guidelines

## Archived Documentation

These documents contained outdated information and have been moved to `archived/`:

- **archived/PIPELINE_DI_USAGE.md** - Referenced removed dependency injection system
- **archived/DEVELOPMENT.md** - Had Makefile references and outdated commands
- **archived/STATUS.md** - Outdated project status (use PROJECT_STATUS.md instead)
- **archived/DATA_FLOW.md** - Contained incorrect parallel processing claims
- **archived/PERFORMANCE.md** - Merged into PERFORMANCE_GUIDE.md
- **archived/PERFORMANCE_OPTIMIZATION.md** - Merged into PERFORMANCE_GUIDE.md

## Quick Reference

### Running the Pipeline
```bash
# Full pipeline
python main.py all input.pbl output/

# Individual stages (must run in order)
python main.py extract input.pbl output/extracted/
python main.py decompile output/extracted/ output/decompiled/
python main.py parse output/decompiled/ output/parsed/
python main.py model output/parsed/ output/models/
python main.py generate output/models/ output/generated/
```

### Development Commands
```bash
# Testing
uv run pytest

# Code quality
uv run ruff check .
uv run ruff format .
uv run mypy src/
```

## Documentation Standards

When updating documentation:

1. **Verify against code**: Always check that documentation matches implementation
2. **Use actual commands**: Test commands before documenting them
3. **Mark assumptions**: Clearly indicate when something is planned vs implemented
4. **Date updates**: Include last-updated dates on documents
5. **Remove outdated info**: Don't leave incorrect information in place

## Contributing to Documentation

If you find discrepancies:
1. Check the actual code implementation
2. Update the documentation to match reality
3. Remove or archive outdated information
4. Submit a PR with clear explanation of changes

## Getting Help

- GitHub Issues: https://github.com/michaelprowacki/powerrebuilder/issues
- Look for issues labeled `documentation` or `claude-code`
