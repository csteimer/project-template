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
    "breathe",
    "sphinx.ext.autosectionlabel",
]

templates_path = ["_templates"]
exclude_patterns = ["_build"]

# Make section labels unique across files: :ref:`index:Section Name`
autosectionlabel_prefix_document = True

# -----------------------------------------------------------------------------
# Breathe / Doxygen integration
# -----------------------------------------------------------------------------
# Doxygen XML lives under docs/doxygen/xml/
DOXYGEN_XML_DIR = ROOT_DIR / "docs" / "doxygen" / "build" / "xml"

breathe_default_project = "project_template"
breathe_projects = {
    "project_template": str(DOXYGEN_XML_DIR),
}

# -----------------------------------------------------------------------------
# HTML output
# -----------------------------------------------------------------------------
html_theme = "furo"
html_static_path = ["_static"]
html_title = "project_template documentation"
