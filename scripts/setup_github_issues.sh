#!/bin/bash

# Script to create GitHub issues from local markdown files
# This aligns with the Claude Code workflow and local project management

echo "Setting up GitHub issues for PowerRebuilder..."

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed"
    exit 1
fi

# Check if we're in a git repository with a remote
if ! git remote get-url origin &> /dev/null; then
    echo "Error: No git remote 'origin' found. Please add the GitHub remote first."
    echo "Run: git remote add origin https://github.com/YOUR_USERNAME/powerrebuilder.git"
    exit 1
fi

# Create labels first
echo "Creating labels..."
gh label create "technical-debt" --description "Code that needs refactoring" --color "FFA500" 2>/dev/null || true
gh label create "testing" --description "Testing improvements" --color "0E8A16" 2>/dev/null || true
gh label create "good-first-issue" --description "Good for newcomers" --color "7057FF" 2>/dev/null || true
gh label create "architecture" --description "Architecture improvements" --color "1D76DB" 2>/dev/null || true
gh label create "performance" --description "Performance optimization" --color "F9D900" 2>/dev/null || true
gh label create "cleanup" --description "Code cleanup tasks" --color "D4C5F9" 2>/dev/null || true
gh label create "dependencies" --description "Dependency management" --color "0052CC" 2>/dev/null || true
gh label create "error-handling" --description "Error handling improvements" --color "B60205" 2>/dev/null || true
gh label create "configuration" --description "Configuration management" --color "5319E7" 2>/dev/null || true
gh label create "claude-code" --description "Issues tracked with Claude Code" --color "9333EA" 2>/dev/null || true

echo "Labels created successfully."

# Function to extract title from markdown file
get_title() {
    local file=$1
    # Extract title from filename (e.g., issue_01_test_coverage.md -> Test Coverage)
    basename "$file" .md | sed 's/issue_[0-9]*_//g' | sed 's/_/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2))}1'
}

# Function to extract labels from markdown
get_labels() {
    local file=$1
    grep -m1 "**Labels:**" "$file" | sed 's/.*Labels:** *//' | sed 's/`//g' | sed 's/, /,/g' | sed 's/ $//'
}

# Function to extract body content (everything except the labels line)
get_body() {
    local file=$1
    # Skip the labels line and use the rest as body
    sed '/^\*\*Labels:\*\*/d' "$file"
}

# Process each issue file
for issue_file in github_issues/issue_*.md; do
    if [ -f "$issue_file" ]; then
        echo "Processing $issue_file..."

        # Extract components
        title=$(get_title "$issue_file")
        labels=$(get_labels "$issue_file")
        body=$(get_body "$issue_file")

        # Add claude-code label to all issues
        if [ -n "$labels" ]; then
            labels="${labels},claude-code"
        else
            labels="claude-code"
        fi

        # Create the issue
        echo "Creating issue: $title"
        gh issue create \
            --title "$title" \
            --body "$body" \
            --label "$labels" || echo "Failed to create issue from $issue_file"

        # Small delay to avoid rate limiting
        sleep 1
    fi
done

echo ""
echo "GitHub issues created successfully!"
echo ""
echo "Next steps:"
echo "1. View issues: gh issue list"
echo "2. Create project board: gh project create --title 'PowerRebuilder Development'"
echo "3. Link issues to project: Use GitHub web interface or gh project commands"
echo ""
echo "Useful commands:"
echo "  gh issue list --label 'good-first-issue'"
echo "  gh issue view <number>"
echo "  gh issue edit <number>"
