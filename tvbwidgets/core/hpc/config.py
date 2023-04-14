# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

from dataclasses import dataclass


@dataclass
class HPCConfig(object):
    site: str
    project: str

    env_dir = 'tvb_widgets_t'
    env_name = 'venv_t'

    STORAGES = {'DAINT-CSCS': 'HOME',
                'JUSUF': 'PROJECT',
                'JUDAC': 'PROJECT'}

    PYTHON_DIRS = {'DAINT-CSCS': 'python3.9',
                   'JUSUF': 'python3.10',
                   'JUDAC': 'python3.10'}
    MODULES = {'DAINT-CSCS': 'cray-python',
               'JUSUF': 'Python',
               'JUDAC': 'Python'}

    @property
    def storage_name(self):
        return self.STORAGES.get(self.site, "PROJECT")

    @property
    def python_dir(self):
        return self.PYTHON_DIRS.get(self.site, 'python3.10')

    @property
    def module_to_load(self):
        return self.MODULES.get(self.site, "")
