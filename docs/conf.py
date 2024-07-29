# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import sys

# ensure redel is available in path
sys.path.append("..")

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "ReDel"
copyright = "2023-present, Andrew Zhu"
author = "Andrew Zhu"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.githubpages",
    "sphinx.ext.viewcode",
    "sphinx_inline_tabs",  # https://sphinx-inline-tabs.readthedocs.io/en/latest/usage.html
    "sphinx_copybutton",  # https://sphinx-copybutton.readthedocs.io/en/latest/
    "sphinxemoji.sphinxemoji",  # https://sphinxemojicodes.readthedocs.io/en/stable/
    "sphinxcontrib.video",  # https://sphinxcontrib-video.readthedocs.io/en/latest/quickstart.html
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

maximum_signature_line_length = 120

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
# html_extra_path = ["_extra"]
# html_logo = "_static/kani-logo@512.png"
# html_favicon = "_extra/favicon.ico"
html_baseurl = "https://redel.readthedocs.io/en/latest/"

html_css_files = [
    "furo_fixes.css",
]

nitpicky = True
nitpick_ignore_regex = [
    (r"py:class", r"aiohttp\..*"),  # aiohttp intersphinx is borked
    (r"py:class", r"torch\..*"),  # idk if torch has intersphinx
    (r"py:class", r"openai\..*"),  # openai does not use sphinx for docs
    (r"py:class", r"anthropic\..*"),  # anthropic does not use sphinx for docs
    (r"py:class", r"asyncio\.\w+\..*"),  # asyncio submodule intersphinx is borked
    (r"py:class", r"redel\..*\.[\w_0-9]*T"),  # ignore generics and other typevars
]

# sphinx.ext.autodoc
autoclass_content = "both"
autodoc_member_order = "bysource"
autodoc_preserve_defaults = True

# sphinx.ext.intersphinx
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "kani": ("https://kani.readthedocs.io/en/latest", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
}

# sphinx_copybutton
copybutton_exclude = ".linenos, .gp, .go"
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True
copybutton_copy_empty_lines = False

# sphinxemoji.sphinxemoji
sphinxemoji_style = "twemoji"
