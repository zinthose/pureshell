# Configuration file for the Sphinx documentation builder.

project = "pureshell"
copyright = "2025, Dane Jones"
author = "Dane Jones"
release = "0.2.1"  # Synced for bump2version

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

autodoc_typehints = "description"

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "alabaster"
