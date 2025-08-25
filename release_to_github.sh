#!/bin/bash

# GitHub Release Script
# For publishing built Python packages to GitHub Release page

set -e  # Exit immediately on error

# Configuration variables
REPO_OWNER="ShiBody"
REPO_NAME="MacCrashAutoSymbolizer"
GITHUB_HOST="github.cisco.com"
VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
TAG_NAME="v${VERSION}"
RELEASE_NAME="MacCrashAutoSymbolizer v${VERSION}"

# Check required files
echo "🔍 Checking required files..."
WHEEL_FILE="dist/maccrashautosymbolizer-${VERSION}-py3-none-any.whl"
TAR_FILE="dist/maccrashautosymbolizer-${VERSION}.tar.gz"

if [ ! -f "$WHEEL_FILE" ]; then
    echo "❌ Cannot find wheel file: $WHEEL_FILE"
    echo "Please run first: uv build"
    exit 1
fi

if [ ! -f "$TAR_FILE" ]; then
    echo "❌ Cannot find source package file: $TAR_FILE"
    echo "Please run first: uv build"
    exit 1
fi

echo "✅ Found build files:"
echo "   - $WHEEL_FILE"
echo "   - $TAR_FILE"

# Check if tag already exists
echo "🏷️  Checking Git tag..."
if git tag -l | grep -q "^${TAG_NAME}$"; then
    echo "⚠️  Tag $TAG_NAME already exists"
    read -p "Do you want to delete existing tag and recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git tag -d "$TAG_NAME"
        git push origin --delete "$TAG_NAME" 2>/dev/null || echo "Remote tag does not exist or already deleted"
    else
        echo "Cancelling release"
        exit 1
    fi
fi

# Create Git tag
echo "📝 Creating Git tag $TAG_NAME..."
git tag -a "$TAG_NAME" -m "Release $VERSION"
git push origin "$TAG_NAME"

echo "✅ Tag created successfully"

# Generate release notes
echo "📄 Generating release notes..."
RELEASE_NOTES=$(cat << EOF

## 📦 Installation

### Install from GitHub Release
\`\`\`bash
# Download and install wheel file
wget https://${GITHUB_HOST}/${REPO_OWNER}/${REPO_NAME}/releases/download/${TAG_NAME}/maccrashautosymbolizer-${VERSION}-py3-none-any.whl
pip install maccrashautosymbolizer-${VERSION}-py3-none-any.whl
\`\`\`

### Install from Source
\`\`\`bash
# Download and install source package
wget https://${GITHUB_HOST}/${REPO_OWNER}/${REPO_NAME}/releases/download/${TAG_NAME}/maccrashautosymbolizer-${VERSION}.tar.gz
pip install maccrashautosymbolizer-${VERSION}.tar.gz
\`\`\`

## 📋 Included Files

- \`maccrashautosymbolizer-${VERSION}-py3-none-any.whl\` - Python Wheel package
- \`maccrashautosymbolizer-${VERSION}.tar.gz\` - Source archive


## 📚 Documentation

For detailed usage documentation, see: [README.md](https://${GITHUB_HOST}/${REPO_OWNER}/${REPO_NAME}/blob/master/README.md)

## 🐛 Issue Reporting

For issues, please submit to: [Issues](https://${GITHUB_HOST}/${REPO_OWNER}/${REPO_NAME}/issues)
EOF
)

# Use GitHub CLI to create release (if gh is installed)
if command -v gh &> /dev/null; then
    echo "🚀 Using GitHub CLI to create release..."
    echo "$RELEASE_NOTES" | gh release create "$TAG_NAME" \
        --title "$RELEASE_NAME" \
        --notes-file - \
        "$WHEEL_FILE" \
        "$TAR_FILE"
    echo "✅ Release created successfully!"
    echo "📖 Release page: https://${GITHUB_HOST}/${REPO_OWNER}/${REPO_NAME}/releases/tag/${TAG_NAME}"
else
    echo "📋 GitHub CLI not installed, please create Release manually:"
    echo "1. Visit: https://${GITHUB_HOST}/${REPO_OWNER}/${REPO_NAME}/releases/new"
    echo "2. Select tag: $TAG_NAME"
    echo "3. Release title: $RELEASE_NAME"
    echo "4. Upload files:"
    echo "   - $WHEEL_FILE"
    echo "   - $TAR_FILE"
    echo "5. Release notes:"
    echo
    echo "$RELEASE_NOTES"
fi

echo
echo "🎉 Release process completed!"
echo "📦 Version: $VERSION"
echo "🏷️  Tag: $TAG_NAME"
echo "📁 Files: $WHEEL_FILE, $TAR_FILE"
