# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2024, TVB Widgets Team
#

from dataclasses import dataclass
from pyunicore.helpers.jobs import Resources


@dataclass
class HPCConfig(object):
    site: str
    project: str
    env_dir: str
    env_name: str
    n_threads: int
    resources: Resources
    timeout = -1

    STORAGES = {'DAINT-CSCS': 'HOME',
                'JUSUF': 'PROJECT',
                'JUDAC': 'PROJECT'}

    PYTHON_DIRS = {'DAINT-CSCS': 'python3.9',
                   'JUSUF': 'python3.10',
                   'JUDAC': 'python3.10'}
    MODULES = {'DAINT-CSCS': 'cray-python',
               'JUSUF': 'Python',
               'JUDAC': 'Python'}

    def __post_init__(self):
        if self.env_dir is None:
            self.env_dir = 'tvb_widgets'
        if self.env_name is None:
            self.env_name = 'venv_tvb'
        if self.n_threads is None:
            self.n_threads = 4

    @property
    def storage_name(self):
        return self.STORAGES.get(self.site, "PROJECT")

    @property
    def python_dir(self):
        return self.PYTHON_DIRS.get(self.site, 'python3.10')

    @property
    def module_to_load(self):
        return self.MODULES.get(self.site, "")
