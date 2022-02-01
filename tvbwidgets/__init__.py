# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

from ._version import __version__
from .logger.builder import get_logger

LOGGER = get_logger(__name__)
LOGGER.info(f"version: {__version__}")
