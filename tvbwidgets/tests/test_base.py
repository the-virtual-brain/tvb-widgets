# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#
import os
import pytest

import tvbwidgets.api as api
from ebrains_drive.exceptions import ClientHttpError
from tvbwidgets.auth import get_current_token
from tvbwidgets.model.model_3d import Model3D
from tvbwidgets.ui.base_widget import TVBWidget
from tvb.simulator.lab import models, integrators


def test_model_3d():
    data_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                               "notebooks", "data", "surface")
    v_path = os.path.join(data_folder, "vertices.txt")
    t_path = os.path.join(data_folder, "triangles.txt")
    with open(v_path) as vertices, open(t_path) as triangles:
        Model3D(vertices, triangles)


def test_auth():
    token = "Bla-bla-42"
    os.environ["CLB_AUTH"] = token
    assert get_current_token() == token


def test_interpret():
    w = api.PhasePlaneWidget(model=models.Generic2dOscillator(),
                             integrator=integrators.HeunDeterministic())
    w.get_widget()
    assert w is not None

    try:
        api.StorageWidget()
        raise RuntimeError("Expected to fail because EBRAINS token does not exist")
    except ClientHttpError:
        pass


def test_add_datatype_not_implemented():
    widget = TVBWidget()

    with pytest.raises(NotImplementedError):
        widget.add_datatype(10)
