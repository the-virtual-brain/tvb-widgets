# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

from tvbwidgets.core.simulator.tvb_integrators import IntegratorsEnum


def test_get_integrators_dict():
    integrators = IntegratorsEnum.get_integrators_dict()
    assert len(integrators.keys()) == 15
