# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

import json
from pathlib import Path

__all__ = ["__version__", "__frontend_module__"]


def _fetch_version():
    here = Path(__file__).parent.resolve()

    for settings in here.rglob("package.json"):
        try:
            with settings.open() as f:
                data = json.load(f)
                version = data["version"]
                version = version.replace("-alpha.", "a").replace("-beta.", "b").replace("-rc.", "rc")
                module = data["name"]
                module = module.replace("-", "")
                return version, module

        except FileNotFoundError:
            pass

    raise FileNotFoundError(f"Could not find package.json under dir {here!s}")


__version__, __frontend_module__ = _fetch_version()
