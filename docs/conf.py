"""Configuration file for the Sphinx documentation builder.

This file only contains a selection of the most common options. For a full
list see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html

-- Path setup --------------------------------------------------------------

If extensions (or modules to document with autodoc) are in another directory,
add these directories to sys.path here. If the directory is relative to the
documentation root, use os.path.abspath to make it absolute, like shown here.
"""

# -- Project information -----------------------------------------------------
from pathlib import Path

import tomllib

pyproject = tomllib.loads(
    (Path(__file__).parents[1] / "pyproject.toml").read_text("utf-8")
)
project = "pandas-contract"
copyright = "%Y Micha Scholl"  # noqa: A001
author = "Micha Scholl"
release = version = pyproject["project"]["version"]

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "myst_parser",
    "autodoc2",
]
autodoc2_packages = [
    "../src/pandas_contract",
]
pygments_style = "sphinx"
autodoc2_sort_names = True
autodoc2_replace_bases = [("pandas_contract", "pc")]
autodoc2_class_docstring = "both"
autodoc2_module_all_regexes = [
    "pandas_contract",
    "pandas_contract.checks.*",
]
autodoc2_hidden_objects = ["inherited", "private"]
autodoc2_output_dir = "_out/apidocs"
intersphinx_mapping = {
    "rtd": ("https://docs.readthedocs.io/en/stable/", None),
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
    "pandera": ("https://pandera.readthedocs.io/en/stable/", None),
}
intersphinx_disabled_domains = ["std"]
html_theme_options = {"navigation_depth": 2}
templates_path = ["_out/_templates"]
# -- Options for EPUB output
epub_show_urls = "footnote"
myst_enable_extensions = ["colon_fence"]
# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_out", "Thumbs.db", ".DS_Store"]
html_static_path = ["_static"]
# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"
# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
