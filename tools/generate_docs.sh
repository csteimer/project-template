#!/usr/bin/env bash
set -euo pipefail

# Resolve project root (script assumed to live in tools/)
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

DOXY_DIR="$ROOT_DIR/docs/doxygen"
SPHINX_DIR="$ROOT_DIR/docs/sphinx"
SPHINX_BUILD_DIR="$SPHINX_DIR/build/html"

DOXY_HTML_SRC="$DOXY_DIR/build/html"
DOXY_HTML_DST="$SPHINX_BUILD_DIR/doxygen/build/html"

echo "==> Project root: $ROOT_DIR"
echo "==> Doxygen dir: $DOXY_DIR"
echo "==> Sphinx dir:  $SPHINX_DIR"
echo

echo "==> Running Doxygen..."
cd "$DOXY_DIR"
doxygen Doxyfile

echo
echo "==> Building Sphinx HTML..."
cd "$SPHINX_DIR"
make html

echo
echo "==> Integrating Doxygen HTML output into Sphinx build..."
# Clean old copy if present
rm -rf "$SPHINX_BUILD_DIR/doxygen"

# Recreate directory structure
mkdir -p "$DOXY_HTML_DST"

# Copy Doxygen HTML recursively
cp -r "$DOXY_HTML_SRC"/* "$DOXY_HTML_DST"

echo
echo "==> Documentation generated successfully!"
echo "    - Combined Sphinx site: $SPHINX_BUILD_DIR/index.html"
echo "    - Doxygen HTML inside Sphinx: $SPHINX_BUILD_DIR/doxygen/build/html/index.html"
echo "    - Doxygen XML: $DOXY_DIR/build/xml"
