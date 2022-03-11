# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

import json
from pathlib import Path

__all__ = ["__version__"]


def _fetch_version():
    here = Path(__file__).parent.resolve()

    for settings in here.rglob("package.json"):
        try:
            with settings.open() as f:
                version = json.load(f)["version"]
                return version.replace("-alpha.", "a").replace("-beta.", "b").replace("-rc.", "rc")

        except FileNotFoundError:
            pass

    raise FileNotFoundError(f"Could not find package.json under dir {here!s}")


__version__ = _fetch_version()
