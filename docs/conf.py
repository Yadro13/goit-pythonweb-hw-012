
import os, sys
sys.path.insert(0, os.path.abspath('..'))
project = 'Contacts API'
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon']
templates_path = ['_templates']
exclude_patterns = []
html_theme = 'alabaster'
