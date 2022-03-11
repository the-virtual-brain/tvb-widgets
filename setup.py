# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

import os
import json
import shutil
import setuptools
from glob import glob
from pathlib import Path
from os.path import join as pjoin
from jupyter_packaging import create_cmdclass, install_npm, ensure_targets, combine_commands, skip_if_exists

TEAM = "Juelich SDL Neuroscience, INS - Marseille, Codemart"

REQUIRED_PACKAGES = ["ebrains_drive", "ipygany", "ipywidgets", "pyvista", "tvb-library"]

HERE = Path(__file__).parent.resolve()

with open(os.path.join(HERE, 'README.md')) as fd:
    DESCRIPTION = fd.read()

# Representative files that should exist after a successful build
NAME = 'tvbwidgets'
jstargets = [
    pjoin(HERE, NAME, 'nbextension', 'index.js'),
    pjoin(HERE, NAME, 'labextension', 'package.json'),
]
package_data_spec = {
    NAME: ['nbextension/**js*', 'labextension/**']
}
data_files_spec = [
    ('share/jupyter/nbextensions/tvbwidgets', 'tvbwidgets/nbextension', '**'),
    ('share/jupyter/labextensions/tvb-widgets', 'tvbwidgets/labextension', '**'),
    ('share/jupyter/labextensions/tvb-widgets', '.', 'install.json'),
    ('etc/jupyter/nbconfig/notebook.d', '.', 'tvbwidgets.json'),
]
cmdclass = create_cmdclass('jsdeps', package_data_spec=package_data_spec,
                           data_files_spec=data_files_spec)
npm_install = combine_commands(
    install_npm(HERE, build_cmd='build:prod'),
    ensure_targets(jstargets),
)
cmdclass['jsdeps'] = skip_if_exists(jstargets, npm_install)

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
                 scripts=glob(pjoin('scripts', '*')),
                 cmdclass=cmdclass,
                 include_package_data=True,
                 python_requires=">=3.8",
                 install_requires=REQUIRED_PACKAGES,
                 description='GUI widgets for EBRAINS showcases',
                 long_description=DESCRIPTION,
                 license="GPL-3.0-or-later",
                 author=TEAM,
                 author_email='tvb.admin@thevirtualbrain.org',
                 url='https://github.com/the-virtual-brain/tvb-widgets',
                 keywords=['tvb', 'ebrains', 'showcases', 'Jupyter', 'Widgets', 'IPython'])

# Cleanup after EGG install. These are created by running setup.py in the source tree
shutil.rmtree('tvb_widgets.egg-info', True)
