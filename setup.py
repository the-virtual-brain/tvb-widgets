# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

import os
import shutil
import setuptools

TEAM = "Juelich SDL Neuroscience, INS - Marseille, Codemart"

REQUIRED_PACKAGES = ["colorcet", "ebrains_drive", "ipywidgets", "pythreejs", "pyvista", "tvb-library"]

REQUIRED_EXTRA_EXAMPLES = ["tvb-data"]
REQUIRED_EXTRA_TESTS = ["pytest", "pytest-mock"]

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as fd:
    DESCRIPTION = fd.read()

setuptools.setup(name='tvb-widgets',
                 packages=setuptools.find_packages(),
                 use_scm_version=True,
                 setup_requires=['setuptools_scm'],
                 include_package_data=True,
                 install_requires=REQUIRED_PACKAGES,
                 extras_require={"tests": REQUIRED_EXTRA_TESTS, "examples": REQUIRED_EXTRA_EXAMPLES},
                 description='GUI widgets for EBRAINS showcases',
                 long_description=DESCRIPTION,
                 license="GPL-3.0-or-later",
                 author=TEAM,
                 author_email='tvb.admin@thevirtualbrain.org',
                 url='https://github.com/the-virtual-brain/tvb-widgets',
                 keywords='tvb widgets jupyterlab ebrains showcases')

# Cleanup after EGG install. These are created by running setup.py in the source tree
shutil.rmtree('tvb_widgets.egg-info', True)
