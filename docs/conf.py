"""
Sphinx config file for service-it.

Uses several extensions to get API docs and sourcecode.
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

from pathlib import Path
from typing import Any

import tomlkit

root = Path(__file__).parent.parent.absolute()
toml = tomlkit.loads((root / "pyproject.toml").read_text(encoding="utf8"))


def find(key: str) -> str:
    return toml["tool"]["poetry"][key]


language = None
project = str(find("name"))
version = str(find("version"))
release = version
author = ", ".join(find("authors"))
copyright = f"2020–2021 {author}"


extensions = ["autoapi.extension", "sphinx.ext.napoleon", "sphinx_rtd_theme"]
autoapi_type = "python"
autoapi_dirs = [str(root / project)]
master_doc = "index"


exclude_patterns = ["_build", "Thumbs.db", ".*", "~*", "*~", "*#"]
html_theme = "sphinx_rtd_theme"
