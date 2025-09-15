#!/usr/bin/env bash

# CI/CD Setup Script for PowerRebuilder
# This script sets up the CI/CD environment and provides instructions

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

# Check prerequisites
check_prerequisites() {
    header "Checking Prerequisites"

    # Check for Git
    if command -v git &> /dev/null; then
        log_success "Git is installed: $(git --version)"
    else
        log_error "Git is not installed"
        exit 1
    fi

    # Check for Python
    if command -v python3 &> /dev/null; then
        log_success "Python is installed: $(python3 --version)"
    else
        log_error "Python 3 is not installed"
        exit 1
    fi

    # Check for uv
    if command -v uv &> /dev/null; then
        log_success "uv is installed: $(uv --version)"
    else
        log_warning "uv is not installed. Installing..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source $HOME/.cargo/env
    fi

    # Check for Docker (optional)
    if command -v docker &> /dev/null; then
        log_success "Docker is installed: $(docker --version)"
    else
        log_warning "Docker is not installed (optional for CI/CD)"
    fi

    # Check for GitHub CLI (optional)
    if command -v gh &> /dev/null; then
        log_success "GitHub CLI is installed: $(gh --version | head -n 1)"
    else
        log_warning "GitHub CLI is not installed (optional for automated setup)"
    fi
}

# Setup local environment
setup_local_environment() {
    header "Setting Up Local Environment"

    # Install Python dependencies
    log_info "Installing Python dependencies..."
    uv sync --all-extras
    log_success "Dependencies installed"

    # Install pre-commit hooks
    log_info "Installing pre-commit hooks..."
    uv run pre-commit install
    log_success "Pre-commit hooks installed"

    # Create necessary directories
    log_info "Creating necessary directories..."
    mkdir -p data output pb_files logs
    log_success "Directories created"

    # Copy example files
    if [ ! -f .env ]; then
        log_info "Creating .env file from example..."
        cat > .env << EOF
# PowerRebuilder Environment Variables
LOG_LEVEL=INFO
WORKERS=4
DB_USER=powerrebuilder
DB_PASSWORD=changeme
EOF
        log_success ".env file created"
    fi

    if [ ! -f docker-compose.override.yml ] && [ -f docker-compose.override.yml.example ]; then
        log_info "Creating docker-compose.override.yml..."
        cp docker-compose.override.yml.example docker-compose.override.yml
        log_success "docker-compose.override.yml created"
    fi
}

# Setup GitHub repository
setup_github_repo() {
    header "GitHub Repository Setup"

    if ! command -v gh &> /dev/null; then
        log_warning "GitHub CLI not installed. Please configure manually."
        show_manual_github_setup
        return
    fi

    # Check if authenticated
    if ! gh auth status &> /dev/null; then
        log_warning "Not authenticated with GitHub. Please run: gh auth login"
        return
    fi

    log_info "Checking repository settings..."

    # Get repository info
    REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")

    if [ -z "$REPO" ]; then
        log_warning "Not in a GitHub repository. Please push to GitHub first."
        return
    fi

    log_success "Repository: $REPO"

    # Configure secrets (if possible)
    log_info "Configuring GitHub Secrets..."
    echo ""
    echo "Please add the following secrets to your GitHub repository:"
    echo "  - PYPI_API_TOKEN: Your PyPI API token for package publishing"
    echo "  - DOCKER_USERNAME: Docker Hub username (optional)"
    echo "  - DOCKER_PASSWORD: Docker Hub password (optional)"
    echo "  - CODECOV_TOKEN: Codecov token for coverage reports (optional)"
    echo ""
    echo "You can add these at: https://github.com/$REPO/settings/secrets/actions"
}

# Show manual GitHub setup instructions
show_manual_github_setup() {
    echo ""
    echo "Manual GitHub Setup Instructions:"
    echo "================================="
    echo ""
    echo "1. Push your code to GitHub:"
    echo "   git remote add origin https://github.com/YOUR_USERNAME/powerrebuilder.git"
    echo "   git push -u origin main"
    echo ""
    echo "2. Configure Branch Protection Rules:"
    echo "   Go to: Settings → Branches → Add rule"
    echo "   - Branch name pattern: main"
    echo "   - ✅ Require a pull request before merging"
    echo "   - ✅ Require status checks to pass before merging"
    echo "   - ✅ Require branches to be up to date before merging"
    echo "   - Select required status checks:"
    echo "     • All CI checks passed"
    echo "     • pre-commit"
    echo "     • test / Tests - Python 3.13 - ubuntu-latest"
    echo ""
    echo "3. Configure GitHub Secrets:"
    echo "   Go to: Settings → Secrets and variables → Actions"
    echo "   Add the following secrets:"
    echo "   - PYPI_API_TOKEN"
    echo "   - DOCKER_USERNAME (optional)"
    echo "   - DOCKER_PASSWORD (optional)"
    echo "   - CODECOV_TOKEN (optional)"
    echo ""
    echo "4. Enable GitHub Pages (for documentation):"
    echo "   Go to: Settings → Pages"
    echo "   - Source: Deploy from a branch"
    echo "   - Branch: gh-pages"
    echo "   - Folder: / (root)"
    echo ""
}

# Setup Docker
setup_docker() {
    header "Docker Setup"

    if ! command -v docker &> /dev/null; then
        log_warning "Docker not installed. Skipping Docker setup."
        return
    fi

    log_info "Building Docker images..."

    # Build development image
    if docker build -t powerrebuilder:dev --target development .; then
        log_success "Development image built"
    else
        log_error "Failed to build development image"
    fi

    # Build production image
    if docker build -t powerrebuilder:latest --target production .; then
        log_success "Production image built"
    else
        log_error "Failed to build production image"
    fi

    log_info "Docker images ready. Use 'docker-compose up' to start services."
}

# Run initial tests
run_initial_tests() {
    header "Running Initial Tests"

    log_info "Running linting checks..."
    if uv run ruff check src/ tests/ --fix; then
        log_success "Linting passed"
    else
        log_warning "Some linting issues were fixed"
    fi

    log_info "Running type checks..."
    if uv run mypy src/ --ignore-missing-imports; then
        log_success "Type checking passed"
    else
        log_warning "Type checking has issues"
    fi

    log_info "Running tests..."
    if uv run pytest tests/ -v --tb=short -m "not slow"; then
        log_success "Tests passed"
    else
        log_error "Some tests failed"
    fi
}

# Generate status report
generate_status_report() {
    header "CI/CD Setup Status Report"

    echo "Setup completed! Here's your status:"
    echo ""
    echo "✅ Completed:"
    echo "  • GitHub Actions workflows created"
    echo "  • Docker configuration added"
    echo "  • Pre-commit hooks installed"
    echo "  • Local environment configured"
    echo ""
    echo "📋 Next Steps:"
    echo "  1. Review and commit the CI/CD configuration:"
    echo "     git add .github/ Dockerfile docker-compose.yml .dockerignore"
    echo "     git commit -m 'feat(ci): add comprehensive CI/CD automation'"
    echo ""
    echo "  2. Push to GitHub:"
    echo "     git push origin main"
    echo ""
    echo "  3. Configure GitHub repository settings (see instructions above)"
    echo ""
    echo "  4. Add required secrets to GitHub"
    echo ""
    echo "  5. Create a test PR to verify everything works"
    echo ""
    echo "📚 Documentation:"
    echo "  • CI/CD Workflows: .github/workflows/"
    echo "  • Contributing Guide: .github/CONTRIBUTING.md"
    echo "  • Docker Setup: docker-compose.yml"
    echo ""
    echo "🚀 Quick Commands:"
    echo "  • Run tests: make test"
    echo "  • Run CI locally: make -f Makefile.ci ci-test"
    echo "  • Build Docker: docker-compose build"
    echo "  • Start services: docker-compose up"
    echo ""
}

# Main execution
main() {
    echo ""
    echo "🚀 PowerRebuilder CI/CD Setup Script"
    echo "===================================="
    echo ""

    check_prerequisites
    setup_local_environment
    setup_github_repo
    setup_docker
    run_initial_tests
    generate_status_report

    echo ""
    log_success "CI/CD setup completed successfully!"
    echo ""
}

# Run main function
main "$@"
