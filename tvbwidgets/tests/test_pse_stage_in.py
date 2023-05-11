# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#
import numpy as np
import pytest
import os
from tvb.datatypes import connectivity
from tvb.simulator.coupling import Kuramoto
from tvb.simulator.models.epileptor import Epileptor
from tvb.simulator.simulator import Simulator
from tvbwidgets.core.pse.toml_storage import TOMLStorage, read_from_file


@pytest.fixture
def custom_simulator():
    """ Returns a customized Simulator """
    simulator = Simulator(connectivity=connectivity.Connectivity.from_file())
    simulator.coupling = Kuramoto()
    simulator.conduction_speed = 3.5
    simulator.simulation_length = 1100.0
    simulator.model = Epileptor(a=np.array([2.0]), b=np.array([4.0]))
    simulator.model.variables_of_interest = ['x1', 'x2', 'x2 - x1']
    simulator.model.state_variable_range['x1'] = np.array([-4., 1.])

    return simulator


def test_stage_in_params(custom_simulator):
    toml_storage = TOMLStorage()
    param1 = "conduction_speed"
    param2 = "coupling.a"
    param1_values = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0]
    param2_values = [0.0, 0.3, 0.6, 0.9]
    metrics = ["GlobalVariance", "KuramotoIndex"]
    file_name = "test.h5"
    n_threads = 4
    storage_file_name = toml_storage.write_in_file(custom_simulator, param1, param2, param1_values, param2_values,
                                                   metrics, n_threads, file_name)

    # Check if the file was created
    assert storage_file_name.exists()

    # Check if the data was written correctly in the file
    obj = read_from_file(storage_file_name)
    assert (type(obj), dict)

    param1_from_file = obj["parameters"]["param1"]
    assert param1_from_file == param1
    param2_from_file = obj["parameters"]["param2"]
    assert param2_from_file == param2
    param1_values_from_file = [float(elem) for elem in obj["parameters"]["param1_values"]]
    assert param1_values_from_file == param1_values
    param2_values_from_file = [float(elem) for elem in obj["parameters"]["param2_values"]]
    assert param2_values_from_file == param2_values
    metrics_from_file = obj["parameters"]["metrics"]
    assert metrics_from_file == metrics
    file_name_from_file = obj["parameters"]["file_name"]
    assert file_name_from_file == file_name
    n_threads_from_file = obj["parameters"]["n_threads"]
    assert n_threads_from_file == n_threads

    # Create another Simulator for testing with the default attributes
    default_simulator = Simulator(connectivity=connectivity.Connectivity.from_file())
    sim_from_file = toml_storage.stage_out_simulator(obj["simulator"])
    assert sim_from_file.model.__class__ == Epileptor
    assert sim_from_file.model.__class__ != default_simulator.model.__class__
    assert sim_from_file.model.a != default_simulator.model.a
    assert sim_from_file.model.b != default_simulator.model.b
    assert sim_from_file.model.variables_of_interest != default_simulator.model.variables_of_interest
    assert sim_from_file.coupling.__class__ == Kuramoto
    assert sim_from_file.coupling.__class__ != default_simulator.coupling.__class__
    assert sim_from_file.conduction_speed != default_simulator.conduction_speed
    assert sim_from_file.simulation_length != default_simulator.simulation_length
    assert sim_from_file.model.state_variable_range['x1'].all() == np.array([-4., 1.]).all()

    os.remove(storage_file_name)
