#!/usr/bin/env bash
set -euo pipefail

# Resolve project root (script assumed to live in tools/)
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

DOXY_DIR="$ROOT_DIR/docs/doxygen"
SPHINX_DIR="$ROOT_DIR/docs/sphinx"

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
echo "==> Documentation generated:"
echo "    - Doxygen XML: $DOXY_DIR/xml"
echo "    - Sphinx HTML: $SPHINX_DIR/_build/html/index.html"
