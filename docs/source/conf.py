# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import inspect
import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

import glide

# From: https://github.com/pandas-dev/pandas/blob/v0.25.1/doc/source/conf.py
def linkcode_resolve(domain, info):
    """
    Determine the URL corresponding to Python object
    """
    if domain != "py":
        return None

    modname = info["module"]
    fullname = info["fullname"]

    submod = sys.modules.get(modname)
    if submod is None:
        return None

    obj = submod
    for part in fullname.split("."):
        try:
            obj = getattr(obj, part)
        except AttributeError:
            return None

    try:
        # inspect.unwrap() was added in Python version 3.4
        if sys.version_info >= (3, 5):
            fn = inspect.getsourcefile(inspect.unwrap(obj))
        else:
            fn = inspect.getsourcefile(obj)
    except TypeError:
        fn = None
    if not fn:
        return None

    try:
        source, lineno = inspect.getsourcelines(obj)
    except OSError:
        lineno = None

    if lineno:
        linespec = "#L{:d}-L{:d}".format(lineno, lineno + len(source) - 1)
    else:
        linespec = ""

    fn = os.path.relpath(fn, start=os.path.dirname(glide.__file__))

    return "https://github.com/kmatarese/glide/blob/master/glide/" "{}{}".format(
        fn, linespec
    )


# -- Project information -----------------------------------------------------

project = "Glide"
copyright = "2019, Kurt Matarese"
author = "Kurt Matarese"

version = glide.__version__
release = glide.__version__

# -- General configuration ---------------------------------------------------

# Necessary for ReadTheDocs
master_doc = "index"

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.linkcode",
    "sphinx.ext.napoleon",
    "m2r",
]

source_suffix = [".rst", ".md"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "alabaster"

html_theme_options = {
    "github_user": "kmatarese",
    "github_repo": "glide",
    "github_banner": True,
    "github_type": "star",
    "show_related": False,
    "show_powered_by": False,
    "show_relbars": True,
    "note_bg": "#FFF59C",
    "logo": "img/glider_image.jpg",
    "logo_name": False,
    "page_width": "980px",
}

html_sidebars = {
    "**": [
        "about.html",
        "navigation.html",
        "relations.html",
        "searchbox.html",
        "donate.html",
    ]
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# If false, no index is generated.
html_use_index = True

# If true, the index is split into individual pages for each letter.
html_split_index = False

# If true, links to the reST sources are added to the pages.
html_show_sourcelink = False
