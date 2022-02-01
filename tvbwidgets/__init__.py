# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

from setuptools_scm import get_version
from .logger.builder import get_logger

__version__ = get_version()

LOGGER = get_logger(__name__)
LOGGER.info(f"version: {__version__}")
