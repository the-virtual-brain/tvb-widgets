# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

import json
import setuptools
import shutil
from pathlib import Path

REQUIRED_PACKAGES = ["colorcet", "ebrains_drive", "ipywidgets", "mne==0.24.1",
                     "pythreejs", "pyvista>=0.34.0", "tvb-library>=2.5"]

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
