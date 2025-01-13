# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#
import json
import os

import numpy
import pytest
import shutil
import tempfile

from tvbwidgets.core.simulator.model_exporters import JSONModelExporter, PythonCodeExporter
from tvbwidgets.ui.phase_plane_widget import PhasePlaneWidget
from tvb.simulator.models.oscillator import Generic2dOscillator, SupHopf
from tvbwidgets.tests.constants import OSCILLATOR_2d_DEFAULT_CONFIG, SUP_HOPF_DEFAULT_PARAMS


@pytest.fixture
def temp_storage():
    """
    returns a temp dir and path to a json file in the temp dir
    after each test the temp dir is removed
    """
    temp_storage = tempfile.mkdtemp()
    file_path = os.path.join(temp_storage)
    yield temp_storage, file_path
    shutil.rmtree(temp_storage)


@pytest.fixture(autouse=True)
def mock_exporter_filename(temp_storage, monkeypatch):
    _storage, file = temp_storage
    json_file = os.path.join(file, 'test_json_file.json')
    py_file = os.path.join(file, 'test_py_file.py')
    monkeypatch.setattr(JSONModelExporter, 'file_path', json_file)
    monkeypatch.setattr(PythonCodeExporter, 'file_path', py_file)


def test_josn_export_config_simple():
    """
    tests that widget exports default model configuration to a json
    """
    wid = PhasePlaneWidget(model=Generic2dOscillator(
        **{k: numpy.array(v) for k, v in OSCILLATOR_2d_DEFAULT_CONFIG.items() if k != 'model'}))
    wid.get_widget()
    default_config = OSCILLATOR_2d_DEFAULT_CONFIG
    wid.export_model_configuration()

    with open(JSONModelExporter.file_path, 'r') as exported_json:
        exported_config = json.loads(exported_json.read())
        assert default_config == exported_config['default_config_key1']
        assert len(exported_config.keys()) == 1


def test_json_export_with_user_defined_configuration_name():
    """
    test that widget exports configuration with a user defined name
    """
    wid = PhasePlaneWidget(model=Generic2dOscillator(
        **{k: numpy.array(v) for k, v in OSCILLATOR_2d_DEFAULT_CONFIG.items() if k != 'model'}))
    wid.get_widget()
    config_name = 'test_config name'
    default_config = OSCILLATOR_2d_DEFAULT_CONFIG
    wid.config_name.value = config_name
    wid.export_model_configuration()
    with open(JSONModelExporter.file_path, 'r') as exported_json:
        exported_config = json.loads(exported_json.read())
        assert default_config == exported_config[config_name]
        assert len(exported_config.keys()) == 1


def test_python_export_with_user_defined_configuration_name():
    """
    test that widget exports configuration with a user defined name as comment
    """
    wid = PhasePlaneWidget(model=SupHopf(
        **{k: numpy.array(v) for k, v in SUP_HOPF_DEFAULT_PARAMS.items() if k != 'model'}))
    wid.get_widget()
    config_name = 'test_config name2'
    expected_instance_code = f'# {config_name}\nimport numpy\nfrom tvb.simulator import models\n' \
                             f'model_instance = models.SupHopf(a=numpy.array([-0.5]),omega=numpy.array([1.]))\n' \
                             f'model_instance\n\n'
    wid.config_name.value = config_name
    wid.export_type.value = 'Python script'
    wid.export_model_configuration()
    with open(PythonCodeExporter.file_path, 'r') as exported_py:
        exported_config = exported_py.read()
        assert exported_config == expected_instance_code


def test_python_multi_export_with_user_defined_configuration_name():
    """
    test that widget exports configuration with a user defined name as comment
    """
    wid = PhasePlaneWidget(model=SupHopf(
        **{k: numpy.array(v) for k, v in SUP_HOPF_DEFAULT_PARAMS.items() if k != 'model'}))
    wid.get_widget()
    config_name = 'test_config name3'
    expected_instance_code = f'# {config_name}\nimport numpy\nfrom tvb.simulator import models\n' \
                             f'model_instance = models.SupHopf(a=numpy.array([-0.5]),omega=numpy.array([1.]))\n' \
                             f'model_instance\n\n' \
                             f'# {config_name}\n' \
                             'model_instance = models.SupHopf(a=numpy.array([-0.5]),omega=numpy.array([1.]))\n' \
                             'model_instance\n\n'

    wid.config_name.value = config_name
    wid.export_type.value = 'Python script'
    wid.export_model_configuration()
    wid.export_model_configuration()
    with open(PythonCodeExporter.file_path, 'r') as exported_py:
        exported_config = exported_py.read()
        assert exported_config == expected_instance_code
