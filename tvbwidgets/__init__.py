# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2024, TVB Widgets Team
#

import json
from pathlib import Path
from pkg_resources import get_distribution, DistributionNotFound
from .core.logger.builder import get_logger

LOGGER = get_logger(__name__)


def _fetch_version():
    here = Path(__file__).parent.parent.resolve()

    for settings in here.rglob("package.json"):
        try:
            with settings.open() as f:
                version = json.load(f)["version"]
                return (
                    version.replace("-alpha.", "a")
                        .replace("-beta.", "b")
                        .replace("-rc.", "rc")
                )
        except FileNotFoundError:
            pass

    raise FileNotFoundError(f"Could not find package.json under dir {here!s}")


try:
    __version__ = get_distribution("tvb-widgets").version
except DistributionNotFound:
    LOGGER.debug("Package is not fully installed")
    try:
        __version__ = _fetch_version()

        LOGGER.debug("Version read from the internal package.json file")
    except FileNotFoundError:
        LOGGER.warn("Version not found, we will use fallback")
        __version__ = "1.0"

LOGGER.info(f"Version: {__version__}")
