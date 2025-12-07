#!/bin/bash

set -e  # Exit on error

PROJECT_ROOT="$(dirname "$(readlink -f "$0")")"

# Virtual environment path in the project root
PYTHON_VENV="$PROJECT_ROOT/.venv"

if [ -d "$PYTHON_VENV" ]; then
  echo "Removing existing Python virtual environment at $PYTHON_VENV"
  rm -rf "$PYTHON_VENV"
fi

echo "Creating new Python virtual environment at $PYTHON_VENV..."
python3 -m venv "$PYTHON_VENV"

source "$PYTHON_VENV/bin/activate"

echo "Upgrading pip ..."
pip install --upgrade pip

echo "Installing Python-based development tools inside the virtual environment ..."
pip install pre-commit cpplint black clang-format cmakelang gcovr conan

echo "Installing documentation requirements inside the virtual environment ..."
pip install -r docs/sphinx/requirements.txt

echo "Installing native dependencies via apt ..."
sudo apt update
sudo apt install -y ninja-build clang-tidy cppcheck ccache doxygen iwyu

echo "Configuring ccache..."
ccache --set-config=cache_dir=~/.ccache
ccache --set-config=max_size=10G
ccache --show-stats

echo "Installing pre-commit hooks..."
pre-commit install

echo ""
echo "Setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source .venv/bin/activate"
echo ""
