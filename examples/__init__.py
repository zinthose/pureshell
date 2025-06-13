"""
This file configures the 'examples' directory as a Python package.

It enables running the examples using: `python -m examples.run`.

It also modifies the Python path to include the parent directory,
allowing for imports from the main project directory.
"""

# To run, use: py -m examples.run

import os
import sys

# Add parrent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
