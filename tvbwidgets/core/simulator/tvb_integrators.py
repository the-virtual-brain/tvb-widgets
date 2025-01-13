# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import inspect
from enum import Enum
from tvb.simulator import integrators


class IntegratorsEnum(Enum):
    BASE_INTEGRATOR = 'Integrator'

    @staticmethod
    def get_integrators_dict():
        integrators_dict = dict()
        for name, obj in inspect.getmembers(integrators):
            if inspect.isclass(obj) and issubclass(obj, integrators.Integrator):
                integrators_dict[obj.__name__] = obj
        return integrators_dict
