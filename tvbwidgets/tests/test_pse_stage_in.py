# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import os
import pytest
import numpy as np
from tvb.datatypes import connectivity
from tvb.simulator.coupling import Kuramoto
from tvb.simulator.models.epileptor import Epileptor
from tvb.simulator.simulator import Simulator
from tvbwidgets.core.pse.storage import StoreObj
from tvbwidgets.core.pse.toml_storage import TOMLStorage


@pytest.fixture
def custom_simulator():
    """ Returns a customized Simulator """
    simulator = Simulator(connectivity=connectivity.Connectivity.from_file("connectivity_66.zip"))
    simulator.coupling = Kuramoto()
    simulator.conduction_speed = 3.5
    simulator.simulation_length = 1100.0
    simulator.model = Epileptor(a=np.array([2.0]), b=np.array([4.0]))
    simulator.model.variables_of_interest = ['x1', 'x2', 'x2 - x1']
    simulator.model.state_variable_range['x1'] = np.array([-4., 1.])

    return simulator


def test_stage_in_pse(custom_simulator):
    file_name = "test.h5"
    store_test(StoreObj(custom_simulator, "conduction_speed", "coupling.a",
                        [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0], [0.0, 0.3, 0.6, 0.9],
                        ["GlobalVariance", "KuramotoIndex"], 4, file_name))
    store_test(StoreObj(custom_simulator, "connectivity", "model.Kf",
                        [connectivity.Connectivity.from_file("connectivity_66.zip"),
                         connectivity.Connectivity.from_file("connectivity_68.zip")], [0.0, 1.6, 3.2],
                        ["GlobalVariance", "KuramotoIndex"], 4, file_name))
    store_test(StoreObj(custom_simulator, "model.slope", "connectivity",
                        [-16.0, -6.0, 4.0], [connectivity.Connectivity.from_file("connectivity_68.zip"),
                                             connectivity.Connectivity.from_file()],
                        ["GlobalVariance", "KuramotoIndex"], 4, file_name))


def store_test(custom_obj):
    storage_file_name = TOMLStorage.write_pse_in_file(StoreObj(custom_obj.sim, custom_obj.param1, custom_obj.param2,
                                                               custom_obj.param1_values, custom_obj.param2_values,
                                                               custom_obj.metrics, custom_obj.n_threads,
                                                               custom_obj.file_name))

    # Check if the file was created
    assert storage_file_name.exists()

    # Check if the data was written correctly in the file
    store_obj = TOMLStorage.read_pse_from_file(storage_file_name)
    assert store_obj.param1 == custom_obj.param1
    assert store_obj.param2 == custom_obj.param2
    assert store_obj.metrics == custom_obj.metrics
    assert store_obj.file_name == custom_obj.file_name
    assert store_obj.n_threads == custom_obj.n_threads

    if store_obj.param1 == "connectivity":
        for i in range(len(store_obj.param1_values)):
            assert store_obj.param1_values[i].tract_lengths.shape == custom_obj.param1_values[i].tract_lengths.shape
    else:
        assert store_obj.param1_values == custom_obj.param1_values
    if store_obj.param2 == "connectivity":
        for i in range(len(store_obj.param2_values)):
            assert store_obj.param2_values[i].tract_lengths.shape == custom_obj.param2_values[i].tract_lengths.shape
    else:
        assert store_obj.param2_values == custom_obj.param2_values

    # Create another Simulator for testing with the default attributes
    default_simulator = Simulator(connectivity=connectivity.Connectivity.from_file())

    assert store_obj.sim.model.__class__ == Epileptor
    assert store_obj.sim.model.__class__ != default_simulator.model.__class__
    assert store_obj.sim.model.a == custom_obj.sim.model.a
    assert store_obj.sim.model.b == custom_obj.sim.model.b
    assert store_obj.sim.model.variables_of_interest != default_simulator.model.variables_of_interest
    assert store_obj.sim.coupling.__class__ == Kuramoto
    assert store_obj.sim.coupling.__class__ != default_simulator.coupling.__class__
    assert store_obj.sim.conduction_speed != default_simulator.conduction_speed
    assert store_obj.sim.conduction_speed == custom_obj.sim.conduction_speed
    assert store_obj.sim.simulation_length != default_simulator.simulation_length
    assert store_obj.sim.simulation_length == custom_obj.sim.simulation_length
    assert store_obj.sim.model.state_variable_range['x1'].all() == np.array([-4., 1.]).all()
    assert store_obj.sim.connectivity.tract_lengths.shape != default_simulator.connectivity.tract_lengths.shape
    assert store_obj.sim.connectivity.tract_lengths.shape == custom_obj.sim.connectivity.tract_lengths.shape

    os.remove(storage_file_name)
