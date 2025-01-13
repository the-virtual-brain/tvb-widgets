# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import os
import pytest
import tvbwidgets.api as api
from tvbwidgets.core.auth import get_current_token, CLB_AUTH
from tvbwidgets.ui.base_widget import TVBWidget
from tvb.simulator.lab import models, integrators


def test_auth():
    token = "Bla-bla-42"
    os.environ[CLB_AUTH] = token
    assert get_current_token() == token


def test_interpret():
    w = api.PhasePlaneWidget(model=models.Generic2dOscillator(),
                             integrator=integrators.HeunDeterministic())
    w.get_widget()
    assert w is not None

    try:
        api.StorageWidget()
        raise RuntimeError("Expected to fail because EBRAINS token does not exist")
    except RuntimeError:
        pass


def test_add_datatype_not_implemented():
    widget = TVBWidget()

    with pytest.raises(NotImplementedError):
        widget.add_datatype(10)
