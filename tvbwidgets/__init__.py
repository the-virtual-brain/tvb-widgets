# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

from .core.logger.builder import get_logger

LOGGER = get_logger(__name__)
from pathlib import Path
import toml


def get_version():
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    if pyproject_path.exists():
        pyproject = toml.load(pyproject_path)
        return pyproject["project"]["version"]
    return "unknown"

__version__ = get_version()
LOGGER.info(f"Version: {__version__}")
