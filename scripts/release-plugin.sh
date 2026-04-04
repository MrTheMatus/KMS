#!/usr/bin/env bash
# Build and package the Obsidian plugin for distribution.
# Output: dist/kms-review-<version>.zip (ready to share or install)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN_DIR="$ROOT/example-vault/.obsidian/plugins/kms-review"

cd "$PLUGIN_DIR"

# Ensure deps & build
if [[ ! -d node_modules ]]; then
  npm install --silent
fi
npm run build

# Read version from manifest
VERSION=$(grep '"version"' manifest.json | head -1 | sed 's/.*: *"\(.*\)".*/\1/')
echo "Building kms-review v${VERSION}"

# Package distributable files
DIST_DIR="$ROOT/dist"
mkdir -p "$DIST_DIR"
ZIPNAME="kms-review-${VERSION}.zip"

cd "$PLUGIN_DIR"
zip -j "$DIST_DIR/$ZIPNAME" main.js manifest.json styles.css

echo ""
echo "Plugin packaged: dist/$ZIPNAME"
echo ""
echo "To install in any Obsidian vault:"
echo "  1. mkdir -p /path/to/vault/.obsidian/plugins/kms-review"
echo "  2. unzip dist/$ZIPNAME -d /path/to/vault/.obsidian/plugins/kms-review/"
echo "  3. Enable 'KMS Review Queue' in Obsidian settings"
