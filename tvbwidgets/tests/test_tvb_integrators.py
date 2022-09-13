import pytest
from tvbwidgets.core.tvb_integrators import IntegratorsEnum


def test_get_integrators_dict():
    integrators = IntegratorsEnum.get_integrators_dict()
    assert len(integrators.keys()) == 15
