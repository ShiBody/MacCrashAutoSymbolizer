#!/bin/bash

# GitHub Release Upload Script
# Uploads dist/ files to GitHub releases page
# Usage: ./upload_release.sh [--version VERSION] [--help]

set -e  # Exit immediately on error

# Configuration
REPO_OWNER="ShiBody"
REPO_NAME="MacCrashAutoSymbolizer"
DIST_DIR="dist"

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

show_help() {
    cat << EOF
GitHub Release Upload Script

USAGE:
    ./upload_release.sh [OPTIONS]

OPTIONS:
    --version VERSION    Specify version to upload (e.g., 3.0.0)
    --help              Show this help message

DESCRIPTION:
    This script uploads built packages from the dist/ directory to GitHub releases.
    If no version is specified, it will auto-detect from the latest built packages.

PREREQUISITES:
    1. GitHub CLI installed and authenticated:
       brew install gh
       gh auth login

    2. Built packages in dist/ directory:
       python -m build

EXAMPLES:
    ./upload_release.sh                    # Auto-detect version
    ./upload_release.sh --version 3.0.1   # Specify version

The script will:
- Auto-detect or use specified version
- Find wheel and source distribution files
- Create GitHub release if it doesn't exist
- Upload files to the release
- Provide download links

EOF
}

# Parse command line arguments
VERSION=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --version)
            VERSION="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    log_error "GitHub CLI is not installed"
    echo "Please install it with: brew install gh"
    echo "Then authenticate with: gh auth login"
    exit 1
fi

# Check if authenticated with GitHub
if ! gh auth status &> /dev/null; then
    log_error "Not authenticated with GitHub"
    echo "Please run: gh auth login"
    exit 1
fi

# Check if dist directory exists
if [ ! -d "$DIST_DIR" ]; then
    log_error "dist/ directory not found"
    echo "Please run: python -m build"
    exit 1
fi

# Auto-detect version if not specified
if [ -z "$VERSION" ]; then
    log_info "Auto-detecting version from built packages..."

    # Find wheel file and extract version
    WHEEL_FILE=$(ls "$DIST_DIR"/*.whl 2>/dev/null | head -1)
    if [ -n "$WHEEL_FILE" ]; then
        # Extract version from wheel filename: maccrashautosymbolizer-X.Y.Z-py3-none-any.whl
        VERSION=$(basename "$WHEEL_FILE" | sed -E 's/maccrashautosymbolizer-([0-9]+\.[0-9]+\.[0-9]+)-.*/\1/')
        log_success "Detected version: $VERSION"
    else
        log_error "No wheel files found in $DIST_DIR/"
        echo "Please run: python -m build"
        exit 1
    fi
fi

# Define file paths
TAG_NAME="v${VERSION}"
WHEEL_FILE="$DIST_DIR/maccrashautosymbolizer-${VERSION}-py3-none-any.whl"
TAR_FILE="$DIST_DIR/maccrashautosymbolizer-${VERSION}.tar.gz"

# Verify files exist
log_info "Verifying build files..."
missing_files=()

if [ ! -f "$WHEEL_FILE" ]; then
    missing_files+=("$WHEEL_FILE")
fi

if [ ! -f "$TAR_FILE" ]; then
    missing_files+=("$TAR_FILE")
fi

if [ ${#missing_files[@]} -gt 0 ]; then
    log_error "Missing build files:"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    echo ""
    echo "Please run: python -m build"
    exit 1
fi

log_success "Found build files:"
echo "   - $WHEEL_FILE"
echo "   - $TAR_FILE"

# Generate release notes
RELEASE_NOTES=$(cat << EOF
## 🚀 MacCrashAutoSymbolizer v${VERSION}

A powerful tool for automatically symbolizing macOS crash logs and stack traces with support for .ips, .diag, .spin, .crash files and raw text.

### 📦 Installation Options

#### Option 1: Install from PyPI (Recommended)
\`\`\`bash
pip install maccrashautosymbolizer
\`\`\`

#### Option 2: Install from GitHub Release
\`\`\`bash
# Download and install wheel file
pip install https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/download/${TAG_NAME}/maccrashautosymbolizer-${VERSION}-py3-none-any.whl
\`\`\`

#### Option 3: Install from Source
\`\`\`bash
# Download and install source package
pip install https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/download/${TAG_NAME}/maccrashautosymbolizer-${VERSION}.tar.gz
\`\`\`

### 🎯 Quick Start

\`\`\`python
from MacAutoSymbolizer import Symbolizer, Arch

# Create symbolizer instance
symbolizer = Symbolizer()

# Symbolize crash logs
result = symbolizer.symbolize('crash.ips', "45.10.0.32891", Arch.arm)

# Print results
for block in result:
    for line in block:
        print(line)
\`\`\`

### 🌐 Web Interface

\`\`\`bash
cd webPage
pip install fastapi uvicorn jinja2 python-multipart
python -m uvicorn app:app --host 0.0.0.0 --port 8000
\`\`\`

Then open \`http://localhost:8000\` in your browser.

### 📋 What's Included

- \`maccrashautosymbolizer-${VERSION}-py3-none-any.whl\` - Python Wheel package (recommended)
- \`maccrashautosymbolizer-${VERSION}.tar.gz\` - Source distribution

### 📚 Documentation

- [README.md](https://github.com/${REPO_OWNER}/${REPO_NAME}/blob/main/README.md) - Complete documentation
- [Web Interface Features](https://github.com/${REPO_OWNER}/${REPO_NAME}/blob/main/webPage/FEATURES.md) - Web UI documentation
- [Examples](https://github.com/${REPO_OWNER}/${REPO_NAME}/tree/main/examples) - Usage examples

### 🐛 Support

- [Issues](https://github.com/${REPO_OWNER}/${REPO_NAME}/issues) - Bug reports and feature requests
- [Discussions](https://github.com/${REPO_OWNER}/${REPO_NAME}/discussions) - Questions and community

### ✨ Key Features

- 🔍 Auto symbol download from remote repositories
- 📊 Multiple format support (.ips, .diag, .spin, .crash files)
- 🏗️ Multi-architecture support (x86_64, arm64)
- 🌐 Modern web interface with GitHub Primer design
- 🌍 Multi-language support (Chinese/English)
- 📱 Responsive design for all devices
- ⚡ High-performance async processing
EOF
)

# Check if release already exists
log_info "Checking if release $TAG_NAME exists..."
if gh release view "$TAG_NAME" --repo "$REPO_OWNER/$REPO_NAME" &> /dev/null; then
    log_warning "Release $TAG_NAME already exists"
    read -p "Do you want to upload files to existing release? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled"
        exit 0
    fi

    # Upload files to existing release
    log_info "Uploading files to existing release..."
    gh release upload "$TAG_NAME" "$WHEEL_FILE" "$TAR_FILE" --repo "$REPO_OWNER/$REPO_NAME" --clobber
else
    # Create new release with files
    log_info "Creating new release $TAG_NAME..."
    echo "$RELEASE_NOTES" | gh release create "$TAG_NAME" \
        --title "MacCrashAutoSymbolizer v${VERSION}" \
        --notes-file - \
        --repo "$REPO_OWNER/$REPO_NAME" \
        "$WHEEL_FILE" \
        "$TAR_FILE"
fi

# Success message
log_success "Release uploaded successfully!"
echo ""
echo "🔗 Release URL: https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/tag/${TAG_NAME}"
echo ""
echo "📦 Download links:"
echo "   Wheel: https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/download/${TAG_NAME}/maccrashautosymbolizer-${VERSION}-py3-none-any.whl"
echo "   Source: https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/download/${TAG_NAME}/maccrashautosymbolizer-${VERSION}.tar.gz"
echo ""
echo "✨ Users can now install with:"
echo "   pip install maccrashautosymbolizer==${VERSION}"
echo "   # or"
echo "   pip install https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/download/${TAG_NAME}/maccrashautosymbolizer-${VERSION}-py3-none-any.whl"
