# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2024, TVB Widgets Team
#

import json
import setuptools
import shutil
import pkg_resources
from pathlib import Path

with Path('requirements.txt').open() as requirements_txt:
    REQUIRED_PACKAGES = [
        str(requirement)
        for requirement
        in pkg_resources.parse_requirements(requirements_txt)
    ]

REQUIRED_EXTRA_EXAMPLES = ["tvb-data"]
REQUIRED_EXTRA_TESTS = ["pytest", "pytest-mock"]

HERE = Path(__file__).parent.resolve()

DESCRIPTION = (HERE / "README.md").read_text()

# Get the package info from package.json
pkg_json = json.loads((HERE / "package.json").read_bytes())
version = (
    pkg_json["version"]
        .replace("-alpha.", "a")
        .replace("-beta.", "b")
        .replace("-rc.", "rc")
)

setuptools.setup(name='tvb-widgets',
                 version=version,
                 packages=setuptools.find_packages(),
                 include_package_data=True,
                 install_requires=REQUIRED_PACKAGES,
                 extras_require={"tests": REQUIRED_EXTRA_TESTS, "examples": REQUIRED_EXTRA_EXAMPLES},
                 description=pkg_json['description'],
                 long_description=DESCRIPTION,
                 long_description_content_type="text/markdown",
                 license=pkg_json['license'],
                 author=pkg_json["author"]["name"],
                 author_email=pkg_json["author"]["email"],
                 url=pkg_json["homepage"],
                 keywords='tvb widgets jupyterlab ebrains showcases')

# Cleanup after EGG install. These are created by running setup.py in the source tree
shutil.rmtree('tvb_widgets.egg-info', True)
