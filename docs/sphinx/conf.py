import sys
from datetime import date
from pathlib import Path

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
SPHINX_DIR = Path(__file__).resolve().parent

# Project root (docs/sphinx -> docs -> project-root)
ROOT_DIR = SPHINX_DIR.parents[1]
sys.path.insert(0, str(ROOT_DIR))

# -----------------------------------------------------------------------------
# Project information
# -----------------------------------------------------------------------------
project = "project_template"
author = "Your Name / Organisation"
current_year = date.today().year
release = "1.0.0"
version = release

# -----------------------------------------------------------------------------
# General configuration
# -----------------------------------------------------------------------------
extensions = [
    "sphinx.ext.autosectionlabel",
]

exclude_patterns = ["build"]

# Make section labels unique across files: :ref:`index:Section Name`
autosectionlabel_prefix_document = True

# -----------------------------------------------------------------------------
# HTML output
# -----------------------------------------------------------------------------
html_theme = "furo"
html_title = "project_template documentation"
