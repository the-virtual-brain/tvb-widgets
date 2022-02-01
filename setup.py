# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

import os
import re
import shutil
import setuptools

TEAM = "Juelich SDL Neuroscience, INS - Marseille, Codemart"

REQUIRED_PACKAGES = ["ebrains_drive", "ipywidgets", "ipygany", "pyvista", "tvb-library"]

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as fd:
    DESCRIPTION = fd.read()


def find_version():
    root_folder = os.path.dirname(os.path.abspath(__file__))
    version = os.path.join(root_folder, "tvbwidgets", "_version.py")

    with open(version, "r", encoding="utf-8") as f:
        file_content = f.read()

        version_pattern = re.search(r"^__version__ *= *['\"](.*?)['\"]$", file_content, re.M)
        if version_pattern:
            return version_pattern.group(1)

        raise RuntimeError("tvbwidgets version number cannot be parsed!")


setuptools.setup(name='tvb-widgets',
                 version=find_version(),
                 packages=setuptools.find_packages(),
                 include_package_data=True,
                 install_requires=REQUIRED_PACKAGES,
                 description='GUI widgets for EBRAINS showcases',
                 long_description=DESCRIPTION,
                 license="GPL-3.0-or-later",
                 author=TEAM,
                 author_email='tvb.admin@thevirtualbrain.org',
                 url='https://github.com/the-virtual-brain/tvb-widgets',
                 keywords='tvb widgets jupyterlab ebrains showcases')

# Cleanup after EGG install. These are created by running setup.py in the source tree
shutil.rmtree('tvb_widgets.egg-info', True)
