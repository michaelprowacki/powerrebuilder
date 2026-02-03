#!/bin/bash
# Auto-commit hook for Claude Code
# This script is called after file writes to ensure changes are committed

# Exit successfully if no git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    exit 0
fi

# Exit if nothing to commit
if git diff --quiet && git diff --cached --quiet; then
    exit 0
fi

# Only auto-commit if explicitly enabled via environment variable
if [ "$CLAUDE_AUTO_COMMIT" != "true" ]; then
    exit 0
fi

# Stage and commit changes
git add -A
git commit -m "Auto-commit: Changes made by Claude Code" --no-verify

exit 0
